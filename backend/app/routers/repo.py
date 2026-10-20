import json
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from typing import List, Optional, Dict, Any
from app.models.schemas import RepoCloneRequest, RepoMetadata, FileTreeItem
from app.services.repo_service import repo_service
from app.services.indexer_service import indexer_service
from app.database.session import get_db_connection

router = APIRouter(prefix="/repo", tags=["Repository"])

@router.post("/clone", response_model=Dict[str, Any])
def clone_repo(request: RepoCloneRequest):
    try:
        repo_id = indexer_service.start_indexing_async(request.url, request.branch)
        return {
            "status": "started",
            "repo_id": repo_id,
            "message": "Repository cloning and AST parsing pipeline started."
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("", response_model=List[RepoMetadata])
def list_repositories():
    return indexer_service.list_repos()

@router.get("/{repo_id}", response_model=RepoMetadata)
def get_repository(repo_id: str):
    repo = indexer_service.get_repo(repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    return repo

@router.get("/{repo_id}/tree", response_model=List[FileTreeItem])
def get_file_tree(repo_id: str):
    repo = indexer_service.get_repo(repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    repo_dir = repo_service.get_repo_dir(repo_id)
    return repo_service.build_file_tree(repo_dir)

@router.get("/{repo_id}/file")
def get_file_content(repo_id: str, path: str = Query(..., description="Relative file path")):
    try:
        return repo_service.get_file_content(repo_id, path)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/seed-demo", response_model=Dict[str, Any])
def seed_demo_repo():
    """Seeds a ready-to-use production sample repository for instant demonstration."""
    demo_url = "https://github.com/repoask/enterprise_auth"
    demo_id = "repoask_enterprise_auth"
    demo_dir = repo_service.get_repo_dir(demo_id)
    demo_dir.mkdir(parents=True, exist_ok=True)

    # Write realistic production files to demo directory
    files_to_create = {
        "app/main.py": '''"""Main FastAPI Application Entrypoint."""
from fastapi import FastAPI, Depends
from app.routers import auth, users, analytics
from app.core.config import settings
from app.middleware.auth import JWTAuthMiddleware

app = FastAPI(
    title="Enterprise AuthService",
    version="2.4.0",
    description="Scalable authentication and identity platform"
)

app.add_middleware(JWTAuthMiddleware)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["analytics"])

@app.get("/health")
async def health_check():
    """Returns system health and database connectivity."""
    return {"status": "healthy", "service": "auth-service", "version": "2.4.0"}
''',
        "app/core/config.py": '''"""Configuration and Settings Module."""
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Enterprise AuthService"
    JWT_SECRET_KEY: str = "production-256-bit-secure-token-change-in-prod"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    DATABASE_URL: str = "postgresql+asyncpg://admin:pass@postgres.cluster:5432/auth_db"

settings = Settings()
''',
        "app/middleware/auth.py": '''"""Authentication Middleware."""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
import jwt
from app.core.config import settings

class JWTAuthMiddleware(BaseHTTPMiddleware):
    """Intercepts requests to validate Bearer tokens on protected routes."""
    
    async def dispatch(self, request: Request, call_next):
        if request.url.path in ("/health", "/api/v1/auth/login", "/docs", "/openapi.json"):
            return await call_next(request)
            
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse({"error": "Missing or malformed Authorization header"}, status_code=401)
            
        token = auth_header.split(" ")[1]
        try:
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            request.state.user = payload
        except jwt.ExpiredSignatureError:
            return JSONResponse({"error": "Token has expired"}, status_code=401)
        except jwt.PyJWTError:
            return JSONResponse({"error": "Invalid token signature"}, status_code=401)
            
        return await call_next(request)
''',
        "app/routers/auth.py": '''"""Authentication Endpoints and JWT Lifecycle."""
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
import jwt
from app.core.config import settings
from app.models.user import User
from app.database.session import get_db

router = APIRouter()

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

@router.post("/login", response_model=TokenResponse)
async def login(credentials: LoginRequest, db = Depends(get_db)):
    """Authenticates user credentials and issues a signed JWT access token."""
    user = await User.find_by_email(db, credentials.email)
    if not user or not user.verify_password(credentials.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
        
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "roles": user.roles,
        "exp": expire
    }
    encoded_jwt = jwt.encode(token_data, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    
    return TokenResponse(
        access_token=encoded_jwt,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
''',
        "app/models/user.py": '''"""User Database Models and Schema."""
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from app.database.session import Base
import bcrypt

class User(Base):
    """User entity storing credentials and role permissions."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    
    def verify_password(self, plain_password: str) -> bool:
        return bcrypt.checkpw(plain_password.encode('utf-8'), self.hashed_password.encode('utf-8'))
        
    @classmethod
    async def find_by_email(cls, db, email: str):
        """Query user by email address."""
        return await db.execute_query(cls.email == email)
''',
        "app/database/session.py": '''"""Database Session Manager."""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

Base = declarative_base()
engine = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
''',
        "app/routers/users.py": '''"""User Management Endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from app.models.user import User

router = APIRouter()

@router.get("/me")
async def get_current_user(user: dict = Depends(lambda: {"id": 1, "email": "dev@repomind.io"})):
    """Fetches profile for authenticated session user."""
    return user

@router.get("/")
async def list_users():
    """List system users with pagination."""
    return [{"id": 1, "email": "staff@repomind.io", "role": "admin"}]
''',
        "app/routers/analytics.py": '''"""Audit Logging and Metrics."""
from fastapi import APIRouter

router = APIRouter()

@router.get("/traffic")
async def get_traffic_metrics():
    """Returns authentication telemetry and request rates."""
    return {"requests_per_minute": 4200, "auth_success_rate": 0.994}
'''
    }

    for path_str, code in files_to_create.items():
        file_path = demo_dir / path_str
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(code, encoding="utf-8")

    # Insert repo row in database
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO repos (id, name, owner, url, default_branch, description, status, progress, current_step)
        VALUES (?, ?, ?, ?, 'main', 'Scalable authentication and identity platform with JWT verification and RBAC.', 'cloning', 10, 'Initializing seed...')
        ON CONFLICT(id) DO UPDATE SET status = 'cloning'
        """,
        (demo_id, "enterprise-auth-service", "repoask", demo_url)
    )
    conn.commit()
    conn.close()

    # Run the indexer directly on this demo repo!
    indexer_service._index_pipeline(
        demo_id,
        demo_url,
        "main"
    )

    return {
        "status": "success",
        "repo_id": demo_id,
        "name": "enterprise-auth-service",
        "message": "Demo repository seeded and indexed with full AST and dependency graph!"
    }
