import json
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from app.models.schemas import DependencyGraphData
from app.database.session import get_db_connection
from app.services.indexer_service import indexer_service

router = APIRouter(prefix="/dependency", tags=["Dependency Graph"])

@router.get("/{repo_id}", response_model=DependencyGraphData)
def get_dependency_graph(repo_id: str):
    repo = indexer_service.get_repo(repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT graph_json FROM dependency_cache WHERE repo_id = ?", (repo_id,))
    row = cursor.fetchone()
    conn.close()

    if not row or not row["graph_json"]:
        return DependencyGraphData(nodes=[], edges=[])

    data = json.loads(row["graph_json"])
    return DependencyGraphData(**data)
