import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime
from app.core.config import settings

def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(settings.SQLITE_PATH), timeout=30.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Repositories table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS repos (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        owner TEXT NOT NULL,
        url TEXT NOT NULL UNIQUE,
        default_branch TEXT DEFAULT 'main',
        description TEXT,
        status TEXT DEFAULT 'idle',
        progress INTEGER DEFAULT 0,
        current_step TEXT DEFAULT '',
        stats_json TEXT,
        indexed_at TIMESTAMP,
        error_message TEXT
    );
    """)

    # AST Symbols table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ast_symbols (
        id TEXT PRIMARY KEY,
        repo_id TEXT NOT NULL,
        file_path TEXT NOT NULL,
        type TEXT NOT NULL,
        name TEXT NOT NULL,
        parent_name TEXT,
        start_line INTEGER NOT NULL,
        end_line INTEGER NOT NULL,
        code TEXT NOT NULL,
        docstring TEXT,
        parameters_json TEXT,
        calls_json TEXT,
        imports_json TEXT,
        tokens INTEGER DEFAULT 0,
        FOREIGN KEY (repo_id) REFERENCES repos (id) ON DELETE CASCADE
    );
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ast_repo ON ast_symbols(repo_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ast_name ON ast_symbols(name);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ast_path ON ast_symbols(file_path);")

    # Dependency Graph Cache
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS dependency_cache (
        repo_id TEXT PRIMARY KEY,
        graph_json TEXT NOT NULL,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Chat Conversations & Messages
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS conversations (
        id TEXT PRIMARY KEY,
        repo_id TEXT NOT NULL,
        title TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id TEXT PRIMARY KEY,
        conversation_id TEXT NOT NULL,
        repo_id TEXT NOT NULL,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        citations_json TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Security Scans Cache
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS security_scans (
        repo_id TEXT PRIMARY KEY,
        score INTEGER NOT NULL,
        report_json TEXT NOT NULL,
        scanned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Code Reviews Cache
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS code_reviews (
        repo_id TEXT PRIMARY KEY,
        score INTEGER NOT NULL,
        report_json TEXT NOT NULL,
        reviewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Generated Docs Cache
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS generated_docs (
        id TEXT PRIMARY KEY,
        repo_id TEXT NOT NULL,
        doc_type TEXT NOT NULL,
        title TEXT NOT NULL,
        markdown_content TEXT NOT NULL,
        generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(repo_id, doc_type)
    );
    """)

    conn.commit()
    conn.close()

# Initialize on import
init_db()
