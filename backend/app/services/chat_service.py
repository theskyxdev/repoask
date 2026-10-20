import uuid
import json
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Any, Set, Tuple

from app.core.config import settings
from app.models.schemas import ChatQueryRequest, ChatResponse, ChatMessage, Citation
from app.database.session import get_db_connection
from app.vectorstore.store import vector_store
from app.llm.gemini_client import gemini_client

STOP_WORDS = {
    "a", "an", "the", "in", "on", "of", "for", "to", "at", "by", "from", "with",
    "is", "are", "was", "were", "be", "been", "being", "have", "has", "had",
    "do", "does", "did", "and", "or", "but", "if", "then", "else", "when",
    "what", "where", "how", "who", "which", "why", "can", "could", "will",
    "would", "should", "tell", "me", "only", "just", "show", "give", "explain",
    "please", "find", "about", "used", "using", "work", "works"
}

class ChatService:
    @staticmethod
    def _extract_query_features(query: str) -> Dict[str, Any]:
        raw_words = re.findall(r"[a-zA-Z0-9_\-\.]+", query.lower())
        tokens = [w for w in raw_words if len(w) > 1 and w not in STOP_WORDS]
        q_lower = query.lower()

        is_database = any(
            k in q_lower for k in [
                "database", "db", "mongo", "mongodb", "postgres", "postgresql",
                "sql", "sqlite", "mysql", "redis", "supabase", "prisma",
                "mongoose", "sqlalchemy", "orm", "session", "table", "schema",
                "model", "models", "migration", "migrations", "store", "storage"
            ]
        )

        is_auth = any(
            k in q_lower for k in [
                "auth", "authentication", "login", "signin", "sign-in", "register",
                "signup", "sign-up", "jwt", "token", "tokens", "password", "hash",
                "bcrypt", "middleware", "protect", "protected", "permission",
                "role", "roles", "bearer", "oauth"
            ]
        )

        is_architecture = any(
            k in q_lower for k in [
                "architecture", "structure", "folder", "directory", "entry",
                "entrypoint", "flow", "lifecycle", "design", "pattern", "system"
            ]
        )

        is_stack = any(
            k in q_lower for k in [
                "tech stack", "stack", "technology", "technologies", "framework",
                "dependencies", "dependency", "package", "packages", "library",
                "libraries", "built with", "version"
            ]
        )

        return {
            "tokens": tokens,
            "is_database": is_database,
            "is_auth": is_auth,
            "is_architecture": is_architecture,
            "is_stack": is_stack,
        }

    @staticmethod
    def _inspect_manifests(repo_id: str) -> List[Dict[str, Any]]:
        contexts = []
        repo_dir = settings.REPOS_DIR / repo_id
        if not repo_dir.exists():
            return contexts

        # Scan for package.json or requirements.txt
        for p in repo_dir.rglob("package.json"):
            if "node_modules" in p.parts:
                continue
            try:
                rel = str(p.relative_to(repo_dir)).replace("\\", "/")
                data = json.loads(p.read_text(encoding="utf-8", errors="replace"))
                deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
                
                # Check for database/auth/framework indicators
                db_indicators = [k for k in deps if any(d in k for d in ["mongo", "mongoose", "supabase", "postgres", "pg", "mysql", "sqlite", "prisma", "sequelize", "typeorm", "redis"])]
                auth_indicators = [k for k in deps if any(a in k for a in ["jwt", "token", "auth", "passport", "bcrypt"])]
                fw_indicators = [k for k in deps if any(f in k for f in ["express", "fastapi", "react", "next", "vite", "vue", "nest"])]

                summary = f"# Manifest: {rel}\n"
                if db_indicators:
                    summary += f"- Database / ORM packages: {', '.join(db_indicators)}\n"
                if auth_indicators:
                    summary += f"- Auth / Crypto packages: {', '.join(auth_indicators)}\n"
                if fw_indicators:
                    summary += f"- Core Framework packages: {', '.join(fw_indicators)}\n"

                contexts.append({
                    "text": summary + f"\n```json\n{json.dumps(deps, indent=2)[:800]}\n```",
                    "metadata": {
                        "file_path": rel,
                        "symbol_name": "package.json",
                        "node_type": "manifest",
                        "start_line": 1,
                        "end_line": len(p.read_text(encoding="utf-8", errors="replace").splitlines()),
                        "score": 14.0
                    },
                    "distance": 0.05
                })
            except Exception:
                pass

        for req in repo_dir.rglob("requirements.txt"):
            try:
                rel = str(req.relative_to(repo_dir)).replace("\\", "/")
                content = req.read_text(encoding="utf-8", errors="replace")
                contexts.append({
                    "text": f"# Manifest: {rel}\n```text\n{content[:800]}\n```",
                    "metadata": {
                        "file_path": rel,
                        "symbol_name": "requirements.txt",
                        "node_type": "manifest",
                        "start_line": 1,
                        "end_line": len(content.splitlines()),
                        "score": 14.0
                    },
                    "distance": 0.05
                })
            except Exception:
                pass

        return contexts

    @staticmethod
    def _hybrid_retrieve(repo_id: str, query: str, top_k: int = 6) -> List[Dict[str, Any]]:
        features = ChatService._extract_query_features(query)
        candidates: Dict[str, Dict[str, Any]] = {}

        conn = get_db_connection()
        cursor = conn.cursor()

        # 1. Targeted Database Queries
        if features["is_database"]:
            cursor.execute(
                """
                SELECT file_path, name, type, start_line, end_line, code, imports_json, docstring
                FROM ast_symbols 
                WHERE repo_id = ? AND (
                    LOWER(file_path) LIKE '%database%' OR LOWER(file_path) LIKE '%db%' 
                    OR LOWER(file_path) LIKE '%supabase%' OR LOWER(file_path) LIKE '%prisma%'
                    OR LOWER(file_path) LIKE '%model%' OR LOWER(file_path) LIKE '%schema%'
                    OR LOWER(file_path) LIKE '%migration%' OR LOWER(file_path) LIKE '%session%'
                    OR LOWER(name) LIKE '%db%' OR LOWER(name) LIKE '%connect%'
                    OR LOWER(name) LIKE '%session%' OR LOWER(name) LIKE '%model%'
                    OR LOWER(code) LIKE '%mongoose.connect%' OR LOWER(code) LIKE '%createclient%'
                    OR LOWER(code) LIKE '%sessionmaker%' OR LOWER(code) LIKE '%mongoclient%'
                )
                ORDER BY 
                    CASE 
                        WHEN LOWER(file_path) LIKE '%config/database%' THEN 1
                        WHEN LOWER(file_path) LIKE '%database/session%' THEN 2
                        WHEN LOWER(file_path) LIKE '%supabase/client%' THEN 3
                        WHEN LOWER(name) LIKE 'connectdb' THEN 4
                        WHEN LOWER(name) LIKE 'get_db' THEN 5
                        WHEN LOWER(file_path) LIKE '%models/%' THEN 6
                        ELSE 10 
                    END
                LIMIT 8
                """,
                (repo_id,)
            )
            for row in cursor.fetchall():
                key = f"{row['file_path']}:{row['start_line']}"
                score = 25.0
                if "database" in row['file_path'].lower() or "session" in row['file_path'].lower():
                    score += 10.0
                candidates[key] = {
                    "text": f"# File: {row['file_path']} | {row['type']} {row['name']} (Lines {row['start_line']}-{row['end_line']})\n{row['code']}",
                    "metadata": {
                        "file_path": row["file_path"],
                        "symbol_name": row["name"],
                        "node_type": row["type"],
                        "start_line": row["start_line"],
                        "end_line": row["end_line"],
                        "imports": row["imports_json"] or "",
                        "score": score
                    },
                    "distance": 0.05
                }

        # 2. Targeted Auth Queries
        if features["is_auth"]:
            cursor.execute(
                """
                SELECT file_path, name, type, start_line, end_line, code, imports_json, docstring
                FROM ast_symbols 
                WHERE repo_id = ? AND (
                    LOWER(file_path) LIKE '%auth%' OR LOWER(file_path) LIKE '%login%' 
                    OR LOWER(file_path) LIKE '%jwt%' OR LOWER(file_path) LIKE '%token%'
                    OR LOWER(file_path) LIKE '%middleware%' OR LOWER(name) LIKE '%auth%'
                    OR LOWER(name) LIKE '%login%' OR LOWER(name) LIKE '%token%'
                    OR LOWER(name) LIKE '%verify%' OR LOWER(name) LIKE '%dispatch%'
                    OR LOWER(code) LIKE '%jwt%' OR LOWER(code) LIKE '%bcrypt%'
                )
                ORDER BY 
                    CASE 
                        WHEN LOWER(name) LIKE 'jwtauthmiddleware' THEN 1
                        WHEN LOWER(name) LIKE 'login' THEN 2
                        WHEN LOWER(file_path) LIKE '%middleware/auth%' THEN 3
                        WHEN LOWER(file_path) LIKE '%controllers/auth%' THEN 4
                        WHEN LOWER(file_path) LIKE '%routers/auth%' THEN 5
                        ELSE 10 
                    END
                LIMIT 8
                """,
                (repo_id,)
            )
            for row in cursor.fetchall():
                key = f"{row['file_path']}:{row['start_line']}"
                score = 22.0
                if "auth" in row['name'].lower() or "login" in row['name'].lower():
                    score += 8.0
                candidates[key] = {
                    "text": f"# File: {row['file_path']} | {row['type']} {row['name']} (Lines {row['start_line']}-{row['end_line']})\n{row['code']}",
                    "metadata": {
                        "file_path": row["file_path"],
                        "symbol_name": row["name"],
                        "node_type": row["type"],
                        "start_line": row["start_line"],
                        "end_line": row["end_line"],
                        "imports": row["imports_json"] or "",
                        "score": score
                    },
                    "distance": 0.05
                }

        # 3. Keyword / Token Exact and Substring Search in AST Symbols
        for token in features["tokens"][:5]:
            cursor.execute(
                """
                SELECT file_path, name, type, start_line, end_line, code, imports_json
                FROM ast_symbols 
                WHERE repo_id = ? AND (
                    LOWER(name) = ? OR LOWER(name) LIKE ? OR LOWER(file_path) LIKE ? OR LOWER(code) LIKE ?
                )
                LIMIT 5
                """,
                (repo_id, token, f"%{token}%", f"%{token}%", f"%{token}%")
            )
            for row in cursor.fetchall():
                key = f"{row['file_path']}:{row['start_line']}"
                score = 12.0
                if row["name"].lower() == token:
                    score += 15.0
                elif token in row["name"].lower():
                    score += 8.0
                if row["type"] in ("function", "method", "class"):
                    score += 3.0

                if key in candidates:
                    candidates[key]["metadata"]["score"] += score
                else:
                    candidates[key] = {
                        "text": f"# File: {row['file_path']} | {row['type']} {row['name']} (Lines {row['start_line']}-{row['end_line']})\n{row['code']}",
                        "metadata": {
                            "file_path": row["file_path"],
                            "symbol_name": row["name"],
                            "node_type": row["type"],
                            "start_line": row["start_line"],
                            "end_line": row["end_line"],
                            "imports": row["imports_json"] or "",
                            "score": score
                        },
                        "distance": 0.2
                    }

        conn.close()

        # 4. Manifest / Package Check (if DB or stack query)
        if features["is_database"] or features["is_stack"]:
            manifest_contexts = ChatService._inspect_manifests(repo_id)
            for mc in manifest_contexts:
                key = f"{mc['metadata']['file_path']}:{mc['metadata']['start_line']}"
                candidates[key] = mc

        # 5. Vector Store Chunks (Semantic Vector Signal)
        try:
            vec_results = vector_store.query(repo_id=repo_id, query_text=query, top_k=top_k)
            for vr in vec_results:
                dist = vr.get("distance", 1.0)
                # Filter out pure noise (distance > 0.82)
                if dist < 0.82:
                    meta = vr.get("metadata", {})
                    key = f"{meta.get('file_path')}:{meta.get('start_line')}"
                    sim_score = max(0.0, (1.0 - dist) * 10.0)
                    if key in candidates:
                        candidates[key]["metadata"]["score"] += sim_score
                    else:
                        vr["metadata"]["score"] = sim_score
                        candidates[key] = vr
        except Exception as e:
            print(f"[ChatService] Vector query error: {e}")

        # 6. Sort Candidates by Total Score
        sorted_contexts = sorted(
            candidates.values(),
            key=lambda x: x["metadata"].get("score", 0.0),
            reverse=True
        )

        return sorted_contexts[: max(top_k, 5)]

    @staticmethod
    def query_repo(request: ChatQueryRequest) -> ChatResponse:
        repo_id = request.repo_id
        conversation_id = request.conversation_id or str(uuid.uuid4())

        # 1. Ensure conversation exists in DB
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM conversations WHERE id = ?", (conversation_id,))
        if not cursor.fetchone():
            title = request.query[:40] + ("..." if len(request.query) > 40 else "")
            cursor.execute(
                "INSERT INTO conversations (id, repo_id, title) VALUES (?, ?, ?)",
                (conversation_id, repo_id, title)
            )
            conn.commit()

        # 2. Save user message
        user_msg_id = str(uuid.uuid4())
        cursor.execute(
            """
            INSERT INTO messages (id, conversation_id, repo_id, role, content)
            VALUES (?, ?, ?, 'user', ?)
            """,
            (user_msg_id, conversation_id, repo_id, request.query)
        )
        conn.commit()

        # 3. Retrieve conversation history
        cursor.execute(
            """
            SELECT role, content FROM messages 
            WHERE conversation_id = ? 
            ORDER BY created_at ASC LIMIT 10
            """,
            (conversation_id,)
        )
        history = [{"role": row["role"], "content": row["content"]} for row in cursor.fetchall()]
        conn.close()

        # 4. Multi-Signal Hybrid Retrieval
        retrieved_contexts = ChatService._hybrid_retrieve(
            repo_id=repo_id,
            query=request.query,
            top_k=request.top_k
        )

        # 5. Generate Evidence-Backed LLM / Code Intelligence response
        answer, citations, model_used = gemini_client.generate_chat_response(
            query=request.query,
            retrieved_contexts=retrieved_contexts,
            conversation_history=history,
            api_key=request.gemini_api_key
        )

        # 6. Save assistant message
        conn = get_db_connection()
        cursor = conn.cursor()
        asst_msg_id = str(uuid.uuid4())
        citations_json = json.dumps([c.model_dump() for c in citations])
        cursor.execute(
            """
            INSERT INTO messages (id, conversation_id, repo_id, role, content, citations_json)
            VALUES (?, ?, ?, 'assistant', ?, ?)
            """,
            (asst_msg_id, conversation_id, repo_id, answer, citations_json)
        )
        conn.commit()
        conn.close()

        chat_message = ChatMessage(
            id=asst_msg_id,
            role="assistant",
            content=answer,
            citations=citations,
            created_at=datetime.utcnow()
        )

        return ChatResponse(
            conversation_id=conversation_id,
            message=chat_message,
            model_used=model_used
        )

    @staticmethod
    def get_conversation_history(conversation_id: str) -> List[ChatMessage]:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, role, content, citations_json, created_at 
            FROM messages 
            WHERE conversation_id = ? 
            ORDER BY created_at ASC
            """,
            (conversation_id,)
        )
        rows = cursor.fetchall()
        conn.close()

        messages = []
        for r in rows:
            cits = [Citation(**c) for c in json.loads(r["citations_json"])] if r["citations_json"] else []
            messages.append(
                ChatMessage(
                    id=r["id"],
                    role=r["role"],
                    content=r["content"],
                    citations=cits,
                    created_at=datetime.fromisoformat(r["created_at"]) if r["created_at"] else datetime.utcnow()
                )
            )
        return messages

chat_service = ChatService()
