import json
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from app.models.schemas import SecurityScanReport
from app.database.session import get_db_connection
from app.services.indexer_service import indexer_service
from app.services.repo_service import repo_service
from app.services.security_scanner import security_scanner

router = APIRouter(prefix="/security", tags=["Security Scanner"])

@router.get("/{repo_id}", response_model=SecurityScanReport)
def get_security_report(repo_id: str):
    repo = indexer_service.get_repo(repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT report_json FROM security_scans WHERE repo_id = ?", (repo_id,))
    row = cursor.fetchone()
    conn.close()

    if row and row["report_json"]:
        return SecurityScanReport(**json.loads(row["report_json"]))

    # On the fly scan
    repo_dir = repo_service.get_repo_dir(repo_id)
    files, _, _ = repo_service.scan_files(repo_dir)
    report = security_scanner.scan_repository(repo_id, repo_dir, files)
    return report
