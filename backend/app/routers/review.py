import json
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from app.models.schemas import CodeReviewReport, ASTNode
from app.database.session import get_db_connection
from app.services.indexer_service import indexer_service
from app.services.repo_service import repo_service
from app.services.code_reviewer import code_reviewer

router = APIRouter(prefix="/review", tags=["Code Review"])

@router.get("/{repo_id}", response_model=CodeReviewReport)
def get_code_review(repo_id: str):
    repo = indexer_service.get_repo(repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT report_json FROM code_reviews WHERE repo_id = ?", (repo_id,))
    row = cursor.fetchone()

    if row and row["report_json"]:
        conn.close()
        return CodeReviewReport(**json.loads(row["report_json"]))

    # Query AST nodes to run review
    cursor.execute("SELECT * FROM ast_symbols WHERE repo_id = ?", (repo_id,))
    raw_nodes = cursor.fetchall()
    conn.close()

    ast_nodes = [
        ASTNode(
            id=n["id"],
            repo_id=n["repo_id"],
            file_path=n["file_path"],
            type=n["type"],
            name=n["name"],
            parent_name=n["parent_name"],
            start_line=n["start_line"],
            end_line=n["end_line"],
            code=n["code"],
            docstring=n["docstring"],
            parameters=json.loads(n["parameters_json"]) if n["parameters_json"] else [],
            calls=json.loads(n["calls_json"]) if n["calls_json"] else [],
            imports=json.loads(n["imports_json"]) if n["imports_json"] else [],
            tokens=n["tokens"]
        )
        for n in raw_nodes
    ]

    repo_dir = repo_service.get_repo_dir(repo_id)
    files, _, _ = repo_service.scan_files(repo_dir)
    return code_reviewer.review_repository(repo_id, repo_dir, files, ast_nodes)
