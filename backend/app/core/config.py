import os
from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "RepoAsk"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Base Directories
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    REPOS_DIR: Path = DATA_DIR / "repos"
    CHROMA_DIR: Path = DATA_DIR / "chromadb"
    SQLITE_PATH: Path = DATA_DIR / "repoask.db"
    
    # LLM Settings
    GEMINI_API_KEY: Optional[str] = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    DEFAULT_MODEL: str = "gemini-2.0-flash"
    EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"
    
    # Cloner & Parser Limits
    MAX_REPO_SIZE_MB: int = 150
    MAX_FILE_SIZE_KB: int = 400
    MAX_CHUNKS_PER_QUERY: int = 6
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ]

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()

# Ensure directories exist
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
settings.REPOS_DIR.mkdir(parents=True, exist_ok=True)
settings.CHROMA_DIR.mkdir(parents=True, exist_ok=True)
