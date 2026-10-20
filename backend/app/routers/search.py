import json
from pathlib import Path
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from app.models.schemas import SearchRequest, SearchResultItem
from app.database.session import get_db_connection
from app.services.indexer_service import indexer_service

router = APIRouter(prefix="/search", tags=["Search"])

@router.post("", response_model=List[SearchResultItem])
def search_repository(request: SearchRequest):
    repo = indexer_service.get_repo(request.repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    q = f"%{request.query.lower()}%"
    conn = get_db_connection()
    cursor = conn.cursor()

    type_filter = ""
    params = [request.repo_id, q, q]

    if request.search_type == "functions":
        type_filter = "AND type IN ('function', 'method')"
    elif request.search_type == "classes":
        type_filter = "AND type IN ('class', 'interface')"
    elif request.search_type == "imports":
        # Search specifically in imports JSON
        cursor.execute(
            f"""
            SELECT id, name, type, file_path, start_line, code, imports_json 
            FROM ast_symbols 
            WHERE repo_id = ? AND LOWER(imports_json) LIKE ?
            LIMIT ?
            """,
            (request.repo_id, q, request.limit)
        )
        rows = cursor.fetchall()
        conn.close()
        return [
            SearchResultItem(
                type="import",
                name=f"Import in {Path(r['file_path']).name}",
                file_path=r["file_path"],
                line_number=r["start_line"],
                code_preview=f"Imports: {r['imports_json'][:120]}",
                score=0.9
            )
            for r in rows
        ]

    # General search across symbol name, file_path, and docstring
    cursor.execute(
        f"""
        SELECT id, name, type, file_path, start_line, code, docstring 
        FROM ast_symbols 
        WHERE repo_id = ? AND (LOWER(name) LIKE ? OR LOWER(file_path) LIKE ?) {type_filter}
        ORDER BY 
            CASE WHEN LOWER(name) = LOWER(?) THEN 1
                 WHEN LOWER(name) LIKE ? THEN 2
                 ELSE 3 END
        LIMIT ?
        """,
        (request.repo_id, q, q, request.query.lower(), f"{request.query.lower()}%", request.limit)
    )
    rows = cursor.fetchall()
    conn.close()

    results = []
    for r in rows:
        preview = r["code"].splitlines()[0] if r["code"] else r["name"]
        results.append(
            SearchResultItem(
                type=r["type"],
                name=r["name"],
                file_path=r["file_path"],
                line_number=r["start_line"],
                code_preview=preview[:140],
                score=1.0 if request.query.lower() in r["name"].lower() else 0.8
            )
        )

    return results
