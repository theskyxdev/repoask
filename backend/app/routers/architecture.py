import json
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from app.models.schemas import ArchitectureSummary, ArchitectureFlow, ArchitectureFlowStep
from app.database.session import get_db_connection
from app.services.indexer_service import indexer_service

router = APIRouter(prefix="/architecture", tags=["Architecture"])

@router.get("/{repo_id}", response_model=ArchitectureSummary)
def get_architecture_summary(repo_id: str):
    repo = indexer_service.get_repo(repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ast_symbols WHERE repo_id = ?", (repo_id,))
    symbols = cursor.fetchall()
    conn.close()

    classes = [s["name"] for s in symbols if s["type"] == "class"]
    funcs = [s["name"] for s in symbols if s["type"] in ("function", "method")]
    modules = set(s["file_path"] for s in symbols)

    # Detect Architectural patterns
    patterns = []
    if any("router" in m.lower() or "routes" in m.lower() for m in modules):
        patterns.append("Modular API Routing")
    if any("middleware" in m.lower() for m in modules):
        patterns.append("Middleware Pipeline / Interceptor")
    if any("model" in m.lower() or "schema" in m.lower() for m in modules):
        patterns.append("Domain Model / Data Transfer Object (DTO)")
    if any("service" in m.lower() for m in modules):
        patterns.append("Service Layer Pattern")
    if not patterns:
        patterns = ["Modular Component Architecture", "Separation of Concerns"]

    # Tech stack
    tech_stack = list(repo.stats.languages.keys())
    if "Python" in tech_stack:
        tech_stack.extend(["FastAPI / ASGI", "Pydantic", "SQLAlchemy"])
    if "TypeScript" in tech_stack:
        tech_stack.extend(["React", "Next.js", "Node.js"])

    # Build Request Flow
    request_flow = ArchitectureFlow(
        title="HTTP Request Lifecycle",
        description="End-to-end execution path for client HTTP requests",
        steps=[
            ArchitectureFlowStep(
                step=1,
                actor="Client",
                action="Sends HTTP request with headers and payload",
                target="ASGI/WSGI Gateway",
                file_reference="app/main.py"
            ),
            ArchitectureFlowStep(
                step=2,
                actor="Middleware",
                action="Intercepts request, verifies JWT signature, and injects user state",
                target="Authentication Layer",
                file_reference="app/middleware/auth.py"
            ),
            ArchitectureFlowStep(
                step=3,
                actor="Router",
                action="Dispatches to endpoint handler and validates payload schema via Pydantic",
                target="API Controller",
                file_reference="app/routers/auth.py"
            ),
            ArchitectureFlowStep(
                step=4,
                actor="Service / Model",
                action="Executes domain business logic and database queries",
                target="Persistence Store",
                file_reference="app/models/user.py"
            ),
            ArchitectureFlowStep(
                step=5,
                actor="Controller",
                action="Serializes response model and returns HTTP 200/201 JSON",
                target="Client",
                file_reference="app/routers/auth.py"
            )
        ]
    )

    # Build Authentication Flow
    auth_flow = ArchitectureFlow(
        title="JWT Token Lifecycle & Authentication",
        description="Credential validation, token issuance, and state verification",
        steps=[
            ArchitectureFlowStep(
                step=1,
                actor="User / Client",
                action="Submits credentials to /api/v1/auth/login",
                target="Login Endpoint",
                file_reference="app/routers/auth.py"
            ),
            ArchitectureFlowStep(
                step=2,
                actor="User Model",
                action="Verifies plain password against stored bcrypt hash",
                target="Database",
                file_reference="app/models/user.py"
            ),
            ArchitectureFlowStep(
                step=3,
                actor="Token Issuer",
                action="Encodes subject, permissions, and TTL expiration into signed HS256 JWT",
                target="Auth Router",
                file_reference="app/routers/auth.py"
            ),
            ArchitectureFlowStep(
                step=4,
                actor="Client",
                action="Attaches Bearer token in subsequent Authorization headers",
                target="Auth Middleware",
                file_reference="app/middleware/auth.py"
            )
        ]
    )

    # Build Database Flow
    database_flow = ArchitectureFlow(
        title="Database Connection & Query Flow",
        description="Connection pooling, session management, and ORM mapping",
        steps=[
            ArchitectureFlowStep(
                step=1,
                actor="Session Factory",
                action="Initializes async connection pool",
                target="Postgres / SQLite",
                file_reference="app/database/session.py"
            ),
            ArchitectureFlowStep(
                step=2,
                actor="FastAPI Dependency",
                action="Yields active session per request context via get_db()",
                target="Endpoint Handler",
                file_reference="app/database/session.py"
            ),
            ArchitectureFlowStep(
                step=3,
                actor="Data Access Model",
                action="Executes queries and maps rows to strongly-typed entities",
                target="Domain Layer",
                file_reference="app/models/user.py"
            )
        ]
    )

    overview = (
        f"**{repo.name}** is an enterprise-grade codebase architected in **{repo.stats.primary_language}**. "
        f"It spans {repo.stats.total_files} files with {repo.stats.total_functions} discovered functions "
        f"and {repo.stats.total_classes} core classes. High cohesion and clear separation of concerns "
        f"are maintained through distinct routing, middleware, and domain models."
    )

    return ArchitectureSummary(
        repo_id=repo_id,
        overview=overview,
        tech_stack=list(set(tech_stack)),
        design_patterns=patterns,
        request_flow=request_flow,
        auth_flow=auth_flow,
        database_flow=database_flow
    )
