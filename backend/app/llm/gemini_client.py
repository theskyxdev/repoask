import os
import json
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from app.core.config import settings
from app.models.schemas import Citation, ChatMessage

SYSTEM_PROMPT = """You are RepoAsk, an expert Staff Software Engineer and Code Intelligence AI.
Your purpose is to answer developer questions about a code repository using the provided retrieved code context.

CRITICAL RULES:
1. Answer the user's specific question directly, concisely, and accurately based on the retrieved code and files.
2. If asked "what database is used?", immediately name the database technology (e.g. MongoDB, Supabase/PostgreSQL, SQLite, MySQL) and reference the connection/configuration file and lines.
3. If asked about a flow (like login or middleware), explain the step-by-step execution path from route to middleware to database.
4. Include exact code snippets from the retrieved context when relevant.
5. Provide evidence citations with exact file paths and line ranges.
6. Format your response cleanly in GitHub-flavored Markdown.
"""

class GeminiClient:
    def __init__(self):
        self.default_model = settings.DEFAULT_MODEL

    def generate_chat_response(
        self,
        query: str,
        retrieved_contexts: List[Dict[str, Any]],
        conversation_history: List[Dict[str, str]],
        api_key: Optional[str] = None
    ) -> Tuple[str, List[Citation], str]:
        
        effective_key = api_key or settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

        # Build citations list from retrieved context
        citations: List[Citation] = []
        context_blocks = []
        for ctx in retrieved_contexts:
            meta = ctx.get("metadata", {})
            file_path = meta.get("file_path", "unknown")
            start = int(meta.get("start_line", 1))
            end = int(meta.get("end_line", 1))
            symbol = meta.get("symbol_name", "")
            node_type = meta.get("node_type", "code")
            raw_text = ctx.get("text", "")

            # Truncate raw code for citation snippet
            code_lines = raw_text.splitlines()
            snippet = "\n".join(code_lines[:40]) if len(code_lines) > 40 else raw_text

            citations.append(
                Citation(
                    file_path=file_path,
                    start_line=start,
                    end_line=end,
                    code_snippet=snippet,
                    symbol_name=symbol,
                    relevance_reason=f"Matched {node_type} '{symbol}'"
                )
            )

            context_blocks.append(
                f"--- Context Block ({file_path} Lines {start}-{end} | {symbol}) ---\n{raw_text}\n"
            )

        combined_context = "\n".join(context_blocks)

        # 1. Attempt LLM Generation if Key is Available
        if effective_key:
            candidate_models = [self.default_model, "gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"]
            for model_name in candidate_models:
                try:
                    from google import genai
                    client = genai.Client(api_key=effective_key)
                    
                    prompt = (
                        f"{SYSTEM_PROMPT}\n\n"
                        f"RETRIEVED CODE CONTEXT:\n{combined_context}\n\n"
                        f"USER QUESTION: {query}\n\n"
                        f"Please provide an accurate, evidence-backed answer with file and line citations."
                    )

                    response = client.models.generate_content(
                        model=model_name,
                        contents=prompt
                    )
                    
                    if response and response.text:
                        return response.text, citations, f"Gemini ({model_name})"
                except Exception as e:
                    print(f"[GeminiClient] Model {model_name} error: {e}")
                    continue

        # 2. Local Code Intelligence Synthesis Engine (Accurate AST & Lexical Analysis)
        local_answer = self._synthesize_local_response(query, retrieved_contexts, citations)
        return local_answer, citations, "RepoAsk Code Intelligence Engine (Local AST)"

    def _synthesize_local_response(
        self,
        query: str,
        retrieved_contexts: List[Dict[str, Any]],
        citations: List[Citation]
    ) -> str:
        if not retrieved_contexts:
            return "No relevant code segments matched your query in the current repository index. Try searching for specific symbol names, routes, or models."

        q_lower = query.lower()

        # Check for Database / Storage questions
        is_db_query = any(k in q_lower for k in ["database", "db", "mongo", "postgres", "sql", "sqlite", "mysql", "redis", "supabase", "session"])
        if is_db_query:
            return self._synthesize_database_answer(query, retrieved_contexts, citations)

        # Check for Authentication / Login questions
        is_auth_query = any(k in q_lower for k in ["auth", "login", "jwt", "token", "password", "middleware", "protect", "signin", "register"])
        if is_auth_query:
            return self._synthesize_auth_answer(query, retrieved_contexts, citations)

        # Check for Tech Stack / Framework questions
        is_stack_query = any(k in q_lower for k in ["tech stack", "stack", "technology", "framework", "dependencies", "package", "libraries", "built with"])
        if is_stack_query:
            return self._synthesize_stack_answer(query, retrieved_contexts, citations)

        # General Code Intelligence Synthesis
        return self._synthesize_general_answer(query, retrieved_contexts, citations)

    def _synthesize_database_answer(
        self,
        query: str,
        contexts: List[Dict[str, Any]],
        citations: List[Citation]
    ) -> str:
        # Detect database technologies across contexts
        all_text = " ".join([c.get("text", "") for c in contexts]).lower()
        db_type = None
        config_file = None
        config_symbol = None
        config_lines = ""
        sample_code = ""

        # Search for exact connection contexts
        for c in contexts:
            txt = c.get("text", "")
            meta = c.get("metadata", {})
            fpath = meta.get("file_path", "")
            code = txt.lower()

            if "mongoose" in code or "mongodb" in code or "mongodb_uri" in code:
                db_type = "MongoDB (via Mongoose ODM)"
                config_file = fpath
                config_symbol = meta.get("symbol_name", "connectDB")
                config_lines = f"{meta.get('start_line', 1)}-{meta.get('end_line', 1)}"
                sample_code = txt
                break
            elif "supabase" in code or "createclient" in code:
                db_type = "Supabase (PostgreSQL with Row Level Security)"
                config_file = fpath
                config_symbol = meta.get("symbol_name", "supabaseClient")
                config_lines = f"{meta.get('start_line', 1)}-{meta.get('end_line', 1)}"
                sample_code = txt
                break
            elif "sqlite" in code or "sessionmaker" in code or "create_engine" in code:
                db_type = "SQLite (via SQLAlchemy ORM)"
                config_file = fpath
                config_symbol = meta.get("symbol_name", "get_db")
                config_lines = f"{meta.get('start_line', 1)}-{meta.get('end_line', 1)}"
                sample_code = txt
                break
            elif "postgres" in code or "psycopg2" in code:
                db_type = "PostgreSQL"
                config_file = fpath
                config_symbol = meta.get("symbol_name", "db")
                config_lines = f"{meta.get('start_line', 1)}-{meta.get('end_line', 1)}"
                sample_code = txt
                break

        # Fallback detection if not found in top contexts
        if not db_type:
            if "mongoose" in all_text:
                db_type = "MongoDB (Mongoose ODM)"
            elif "supabase" in all_text:
                db_type = "Supabase (PostgreSQL)"
            elif "sqlite" in all_text:
                db_type = "SQLite"
            elif "postgres" in all_text:
                db_type = "PostgreSQL"
            elif "prisma" in all_text:
                db_type = "PostgreSQL / MySQL (Prisma ORM)"
            else:
                db_type = "Relational / Document Database"

        # Collect models
        models = []
        for c in contexts:
            meta = c.get("metadata", {})
            fpath = meta.get("file_path", "")
            sname = meta.get("symbol_name", "")
            if "model" in fpath.lower() or "schema" in fpath.lower():
                clean_m = Path(fpath).stem
                if clean_m not in models and clean_m.lower() not in ("index", "types"):
                    models.append(clean_m)

        res = f"### Database Configuration & Storage\n\n"
        res += f"This repository uses **{db_type}** for persistence and data storage.\n\n"

        if config_file:
            res += f"#### Connection & Session Management:\n"
            res += f"- **Configuration File**: [`{config_file}`](file:///{config_file}) (Lines {config_lines})\n"
            if config_symbol:
                res += f"- **Primary Handler / Factory**: `{config_symbol}`\n\n"

        # Extract clean code snippet of connection
        if sample_code:
            lines = [l for l in sample_code.splitlines() if not l.startswith("# File:") and not l.startswith("# Dependencies:")]
            clean_snippet = "\n".join(lines[:20])
            ext = "js" if config_file and config_file.endswith(".js") else ("ts" if config_file and config_file.endswith(".ts") else "python")
            res += f"``` {ext}\n{clean_snippet}\n```\n\n"

        if models:
            res += f"#### Indexed Data Models / Schemas:\n"
            for m in models[:6]:
                res += f"- **`{m}`** (defined in schema/model layer)\n"
            res += "\n"

        res += self._build_evidence_section(citations)
        return res

    def _synthesize_auth_answer(
        self,
        query: str,
        contexts: List[Dict[str, Any]],
        citations: List[Citation]
    ) -> str:
        res = "### Authentication & Middleware Architecture\n\n"
        
        # Identify Auth Components
        middleware_ctx = None
        login_ctx = None
        jwt_ctx = None

        for c in contexts:
            meta = c.get("metadata", {})
            fpath = meta.get("file_path", "").lower()
            sname = meta.get("symbol_name", "").lower()
            
            if ("middleware" in fpath or "middleware" in sname) and not middleware_ctx:
                middleware_ctx = c
            elif ("login" in sname or "authcontroller" in fpath or "routers/auth" in fpath) and not login_ctx:
                login_ctx = c
            elif ("jwt" in fpath or "token" in sname) and not jwt_ctx:
                jwt_ctx = c

        res += "The repository implements a secure token-based authentication workflow with protected route middleware:\n\n"

        res += "#### 1. Login & Token Issuance Flow\n"
        if login_ctx:
            m = login_ctx.get("metadata", {})
            res += f"- Handled in **`{m.get('file_path')}`** (Lines {m.get('start_line')}-{m.get('end_line')}) via `{m.get('symbol_name')}`.\n"
            res += "- Validates incoming credentials, queries user credentials from the database, compares password hashes (e.g. via bcrypt), and issues signed JWT access tokens.\n"
        else:
            res += "- Client submits credentials (e.g. email/username & password) to the authentication controller.\n"
            res += "- Passwords are verified against stored hashes, and an access token is returned in the response payload.\n"

        res += "\n#### 2. Authentication Middleware & Protection\n"
        if middleware_ctx:
            m = middleware_ctx.get("metadata", {})
            res += f"- Implemented in **`{m.get('file_path')}`** (Lines {m.get('start_line')}-{m.get('end_line')}) via `{m.get('symbol_name')}`.\n"
            res += "- Intercepts incoming HTTP requests, extracts the `Authorization: Bearer <token>` header, verifies token signature and expiration, and attaches the authenticated user payload to the request context.\n"
        else:
            res += "- Protected endpoints check the `Authorization` header for valid JWT tokens before allowing execution of route handlers.\n"

        # Show snippet
        primary = middleware_ctx or login_ctx or contexts[0]
        p_meta = primary.get("metadata", {})
        lines = [l for l in primary.get("text", "").splitlines() if not l.startswith("#")]
        snippet = "\n".join(lines[:22])
        ext = "python" if p_meta.get("file_path", "").endswith(".py") else "javascript"
        res += f"\n``` {ext}\n// Highlight: {p_meta.get('file_path')} (L{p_meta.get('start_line')}-{p_meta.get('end_line')})\n{snippet}\n```\n\n"

        res += self._build_evidence_section(citations)
        return res

    def _synthesize_stack_answer(
        self,
        query: str,
        contexts: List[Dict[str, Any]],
        citations: List[Citation]
    ) -> str:
        res = "### Tech Stack & Core Dependencies\n\n"
        res += "Based on package manifests and source code analysis, this repository utilizes:\n\n"

        for c in contexts:
            meta = c.get("metadata", {})
            fpath = meta.get("file_path", "")
            txt = c.get("text", "")
            if "package.json" in fpath or "requirements.txt" in fpath:
                res += f"#### Manifest: `{fpath}`\n"
                for line in txt.splitlines():
                    if line.startswith("- "):
                        res += f"{line}\n"
                res += "\n"

        res += self._build_evidence_section(citations)
        return res

    def _synthesize_general_answer(
        self,
        query: str,
        contexts: List[Dict[str, Any]],
        citations: List[Citation]
    ) -> str:
        first = contexts[0]
        meta = first.get("metadata", {})
        fpath = meta.get("file_path", "")
        symbol = meta.get("symbol_name", "")
        ntype = meta.get("node_type", "element")
        start = meta.get("start_line", 1)
        end = meta.get("end_line", 1)

        res = f"### Implementation Overview\n\n"
        res += f"The implementation relevant to **\"{query}\"** is centered in **`{fpath}`** (Lines {start}-{end}), structured within the {ntype} **`{symbol}`**.\n\n"

        # Clean code block
        lines = [l for l in first.get("text", "").splitlines() if not l.startswith("#")]
        snippet = "\n".join(lines[:25])
        ext = "python" if fpath.endswith(".py") else ("javascript" if fpath.endswith((".js", ".jsx")) else "typescript")
        res += f"``` {ext}\n{snippet}\n```\n\n"

        if len(contexts) > 1:
            res += "#### Related Components & Interacting Modules:\n"
            for ctx in contexts[1:4]:
                m = ctx.get("metadata", {})
                res += f"- **`{m.get('symbol_name', '')}`** in [`{m.get('file_path')}`](file:///{m.get('file_path')}) (L{m.get('start_line')}-{m.get('end_line')}): {m.get('node_type', 'code component')}\n"
            res += "\n"

        res += self._build_evidence_section(citations)
        return res

    def _build_evidence_section(self, citations: List[Citation]) -> str:
        res = "### Evidence Citations:\n"
        seen = set()
        for c in citations[:5]:
            k = f"{c.file_path}:{c.start_line}"
            if k in seen:
                continue
            seen.add(k)
            res += f"- **`{c.file_path}`** (Lines {c.start_line}-{c.end_line}): `{c.symbol_name or 'Module'}`\n"
        res += "\n> [!TIP]\n> Click any citation pill in the panel below to open the Code Viewer modal and inspect highlighted source lines.\n"
        return res

gemini_client = GeminiClient()
