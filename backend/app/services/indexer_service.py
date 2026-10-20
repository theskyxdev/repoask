import json
import sqlite3
import threading
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime

from app.core.config import settings
from app.models.schemas import RepoMetadata, RepoStats, ASTNode
from app.database.session import get_db_connection
from app.services.repo_service import repo_service
from app.parser.ast_parser import ASTParser
from app.parser.chunker import SmartChunker
from app.parser.dependency_mapper import DependencyMapper
from app.vectorstore.store import vector_store
from app.services.security_scanner import security_scanner
from app.services.code_reviewer import code_reviewer

class IndexerService:
    @staticmethod
    def update_repo_status(repo_id: str, status: str, progress: int, step: str, error: Optional[str] = None):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE repos 
            SET status = ?, progress = ?, current_step = ?, error_message = ?
            WHERE id = ?
            """,
            (status, progress, step, error, repo_id)
        )
        conn.commit()
        conn.close()

    @staticmethod
    def get_repo(repo_id: str) -> Optional[RepoMetadata]:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM repos WHERE id = ?", (repo_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        stats_data = json.loads(row["stats_json"]) if row["stats_json"] else {}
        stats = RepoStats(**stats_data)

        return RepoMetadata(
            id=row["id"],
            name=row["name"],
            owner=row["owner"],
            url=row["url"],
            default_branch=row["default_branch"],
            description=row["description"],
            status=row["status"],
            progress=row["progress"],
            current_step=row["current_step"],
            stats=stats,
            indexed_at=datetime.fromisoformat(row["indexed_at"]) if row["indexed_at"] else None,
            error_message=row["error_message"]
        )

    @staticmethod
    def list_repos() -> List[RepoMetadata]:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM repos ORDER BY indexed_at DESC, id ASC")
        rows = cursor.fetchall()
        conn.close()

        repos = []
        for row in rows:
            stats_data = json.loads(row["stats_json"]) if row["stats_json"] else {}
            repos.append(
                RepoMetadata(
                    id=row["id"],
                    name=row["name"],
                    owner=row["owner"],
                    url=row["url"],
                    default_branch=row["default_branch"],
                    description=row["description"],
                    status=row["status"],
                    progress=row["progress"],
                    current_step=row["current_step"],
                    stats=RepoStats(**stats_data),
                    indexed_at=datetime.fromisoformat(row["indexed_at"]) if row["indexed_at"] else None,
                    error_message=row["error_message"]
                )
            )
        return repos

    @staticmethod
    def start_indexing_async(url: str, branch: Optional[str] = None):
        owner, name, repo_id = repo_service.extract_repo_info(url)
        
        # Save initial repo row in DB
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO repos (id, name, owner, url, default_branch, status, progress, current_step)
            VALUES (?, ?, ?, ?, ?, 'cloning', 10, 'Initializing repository clone...')
            ON CONFLICT(id) DO UPDATE SET
                status = 'cloning',
                progress = 10,
                current_step = 'Initializing repository clone...',
                error_message = NULL
            """,
            (repo_id, name, owner, url, branch or "main")
        )
        conn.commit()
        conn.close()

        # Run indexing in background thread
        thread = threading.Thread(
            target=IndexerService._index_pipeline,
            args=(repo_id, url, branch),
            daemon=True
        )
        thread.start()
        return repo_id

    @staticmethod
    def _index_pipeline(repo_id: str, url: str, branch: Optional[str]):
        try:
            # 1. Clone
            IndexerService.update_repo_status(repo_id, "cloning", 20, "Cloning repository...")
            repo_id, repo_dir = repo_service.clone_repository(url, branch)

            # 2. File Scan & Language Detection
            IndexerService.update_repo_status(repo_id, "parsing", 35, "Scanning files & detecting languages...")
            files, file_languages, stats = repo_service.scan_files(repo_dir)

            # 3. AST Parsing
            IndexerService.update_repo_status(repo_id, "parsing", 50, f"Running AST parser on {len(files)} files...")
            all_ast_nodes: List[ASTNode] = []
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM ast_symbols WHERE repo_id = ?", (repo_id,))

            for rel_path in files:
                full_path = repo_dir / rel_path
                lang = file_languages.get(rel_path, "Other")
                file_nodes = ASTParser.parse_file(repo_id, rel_path, full_path, lang)
                all_ast_nodes.extend(file_nodes)

                # Insert into DB
                for node in file_nodes:
                    cursor.execute(
                        """
                        INSERT OR REPLACE INTO ast_symbols 
                        (id, repo_id, file_path, type, name, parent_name, start_line, end_line, code, docstring, parameters_json, calls_json, imports_json, tokens)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            node.id, repo_id, node.file_path, node.type, node.name,
                            node.parent_name, node.start_line, node.end_line, node.code,
                            node.docstring, json.dumps(node.parameters), json.dumps(node.calls),
                            json.dumps(node.imports), node.tokens
                        )
                    )

            stats.total_functions = sum(1 for n in all_ast_nodes if n.type in ("function", "method"))
            stats.total_classes = sum(1 for n in all_ast_nodes if n.type in ("class", "interface"))
            stats.total_imports = sum(len(n.imports) for n in all_ast_nodes)
            conn.commit()

            # 4. Dependency Graph
            IndexerService.update_repo_status(repo_id, "indexing", 70, "Building NetworkX dependency graph...")
            dep_graph = DependencyMapper.build_graph(repo_id, files, all_ast_nodes)
            cursor.execute(
                """
                INSERT OR REPLACE INTO dependency_cache (repo_id, graph_json)
                VALUES (?, ?)
                """,
                (repo_id, dep_graph.model_dump_json())
            )
            conn.commit()

            # 5. Smart Chunking & ChromaDB Vector Indexing
            IndexerService.update_repo_status(repo_id, "indexing", 85, "Generating embeddings & indexing vector store...")
            chunks = SmartChunker.chunk_nodes(all_ast_nodes, repo_id)
            vector_store.index_chunks(repo_id, chunks)

            # 6. Security Scan & Code Review Pre-computation
            IndexerService.update_repo_status(repo_id, "indexing", 95, "Running security scan and code review...")
            sec_report = security_scanner.scan_repository(repo_id, repo_dir, files)
            cursor.execute(
                "INSERT OR REPLACE INTO security_scans (repo_id, score, report_json) VALUES (?, ?, ?)",
                (repo_id, sec_report.security_score, sec_report.model_dump_json())
            )

            rev_report = code_reviewer.review_repository(repo_id, repo_dir, files, all_ast_nodes)
            cursor.execute(
                "INSERT OR REPLACE INTO code_reviews (repo_id, score, report_json) VALUES (?, ?, ?)",
                (repo_id, rev_report.review_score, rev_report.model_dump_json())
            )

            # Finalize
            now = datetime.utcnow().isoformat()
            cursor.execute(
                """
                UPDATE repos 
                SET status = 'ready', progress = 100, current_step = 'Indexing complete!',
                    stats_json = ?, indexed_at = ?
                WHERE id = ?
                """,
                (stats.model_dump_json(), now, repo_id)
            )
            conn.commit()
            conn.close()

        except Exception as e:
            print(f"[IndexerService] Indexing error: {e}")
            IndexerService.update_repo_status(repo_id, "error", 0, "Indexing failed", str(e))

indexer_service = IndexerService()
