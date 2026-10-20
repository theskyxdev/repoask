import json
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
from app.models.schemas import DocGenerationRequest, GeneratedDoc, ASTNode
from app.database.session import get_db_connection
from app.services.indexer_service import indexer_service
from app.services.repo_service import repo_service
from app.services.doc_generator import doc_generator

router = APIRouter(prefix="/docs", tags=["Documentation"])

@router.post("/generate", response_model=GeneratedDoc)
def generate_documentation(request: DocGenerationRequest):
    repo = indexer_service.get_repo(request.repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ast_symbols WHERE repo_id = ?", (request.repo_id,))
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

    repo_dir = repo_service.get_repo_dir(request.repo_id)
    files, _, _ = repo_service.scan_files(repo_dir)

    doc = doc_generator.generate_doc(
        repo_meta=repo,
        doc_type=request.doc_type,
        files=files,
        ast_nodes=ast_nodes,
        api_key=request.gemini_api_key
    )

    # Cache doc in database
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT OR REPLACE INTO generated_docs (id, repo_id, doc_type, title, markdown_content)
        VALUES (?, ?, ?, ?, ?)
        """,
        (f"{request.repo_id}:{request.doc_type}", request.repo_id, doc.doc_type, doc.title, doc.markdown_content)
    )
    conn.commit()
    conn.close()

    return doc

@router.get("/{repo_id}", response_model=List[GeneratedDoc])
def list_generated_docs(repo_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT doc_type, title, markdown_content, generated_at FROM generated_docs WHERE repo_id = ?", (repo_id,))
    rows = cursor.fetchall()
    conn.close()

    return [
        GeneratedDoc(
            doc_type=r["doc_type"],
            title=r["title"],
            markdown_content=r["markdown_content"]
        )
        for r in rows
    ]
