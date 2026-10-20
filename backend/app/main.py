from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.database.session import init_db
from app.routers import repo, chat, architecture, dependency, security, review, docs, search

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite database schema
    init_db()
    # Check if we should auto-seed demo repository for instant out-of-the-box exploration
    from app.services.indexer_service import indexer_service
    existing = indexer_service.list_repos()
    if not existing:
        print("[RepoAsk] Initializing default enterprise demo repository...")
        try:
            repo.seed_demo_repo()
            print("[RepoAsk] Demo repository initialized successfully!")
        except Exception as e:
            print(f"[RepoAsk] Demo initialization error: {e}")
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Intelligent GitHub Repository Understanding with AST Parsing, NetworkX Dependency Mapping, and Evidence-backed Citations.",
    lifespan=lifespan
)

import time
from collections import defaultdict
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response, JSONResponse
from fastapi import Request

# In-memory sliding window rate limiter
class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_requests: int = 180, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        # Exempt health check and preflight OPTIONS from rate limiting
        if request.method == "OPTIONS" or request.url.path.endswith("/health"):
            return await call_next(request)

        client_ip = request.client.host if request.client else "127.0.0.1"
        now = time.time()
        
        # Clean timestamps older than window
        self.requests[client_ip] = [t for t in self.requests[client_ip] if now - t < self.window_seconds]
        
        if len(self.requests[client_ip]) >= self.max_requests:
            return JSONResponse(
                {"error": "Too Many Requests", "detail": "Rate limit exceeded. Please wait a moment."},
                status_code=429,
                headers={"Retry-After": "30"}
            )
            
        self.requests[client_ip].append(now)
        return await call_next(request)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        return response

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:[0-9]+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers under API_V1_STR
api_prefix = settings.API_V1_STR
app.include_router(repo.router, prefix=api_prefix)
app.include_router(chat.router, prefix=api_prefix)
app.include_router(architecture.router, prefix=api_prefix)
app.include_router(dependency.router, prefix=api_prefix)
app.include_router(security.router, prefix=api_prefix)
app.include_router(review.router, prefix=api_prefix)
app.include_router(docs.router, prefix=api_prefix)
app.include_router(search.router, prefix=api_prefix)

@app.get("/health")
@app.get(f"{api_prefix}/health")
def health():
    return {
        "status": "online",
        "service": "RepoAsk Engine",
        "version": settings.VERSION,
        "features": [
            "AST Chunking",
            "NetworkX Dependency Graph",
            "ChromaDB Vector Store",
            "Evidence-backed Citations",
            "Static Security Scanner",
            "Automated Code Review",
            "Auto Documentation Generator"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
