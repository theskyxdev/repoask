import os
import re
import json
import shutil
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime
import git

from app.core.config import settings
from app.models.schemas import RepoMetadata, RepoStats, FileTreeItem
from app.database.session import get_db_connection
from app.parser.language_detector import LanguageDetector

class RepoService:
    @staticmethod
    def extract_repo_info(url: str) -> Tuple[str, str, str]:
        """Extracts owner, name, and clean repo_id from a GitHub URL."""
        clean_url = url.strip().rstrip("/")
        if clean_url.endswith(".git"):
            clean_url = clean_url[:-4]
        
        parts = clean_url.split("/")
        if len(parts) >= 2:
            owner = parts[-2]
            name = parts[-1]
        else:
            owner = "user"
            name = clean_url.replace(":", "_").replace("/", "_")
            
        repo_id = re.sub(r"[^a-zA-Z0-9_\-]", "_", f"{owner}_{name}".lower())
        return owner, name, repo_id

    @staticmethod
    def get_repo_dir(repo_id: str) -> Path:
        clean_id = re.sub(r"[^a-zA-Z0-9_\-]", "_", repo_id)
        return settings.REPOS_DIR / clean_id

    @staticmethod
    def clone_repository(url: str, branch: Optional[str] = None, depth: int = 1) -> Tuple[str, Path]:
        owner, name, repo_id = RepoService.extract_repo_info(url)
        repo_dir = RepoService.get_repo_dir(repo_id)

        if repo_dir.exists() and any(repo_dir.iterdir()):
            return repo_id, repo_dir

        repo_dir.mkdir(parents=True, exist_ok=True)

        try:
            clone_kwargs = {"depth": depth}
            if branch:
                clone_kwargs["branch"] = branch
            git.Repo.clone_from(url, str(repo_dir), **clone_kwargs)
        except Exception as e:
            # If Git clone fails (e.g. rate limit, private repo, or no internet), raise informative error
            raise RuntimeError(f"Git clone failed for {url}: {str(e)}")

        return repo_id, repo_dir

    @staticmethod
    def scan_files(repo_dir: Path) -> Tuple[List[str], Dict[str, str], RepoStats]:
        files: List[str] = []
        file_languages: Dict[str, str] = {}
        language_bytes: Dict[str, int] = {}
        total_lines = 0

        for path in repo_dir.rglob("*"):
            if not path.is_file():
                continue
            if LanguageDetector.is_ignored_path(path):
                continue

            rel = str(path.relative_to(repo_dir)).replace("\\", "/")
            files.append(rel)

            lang = LanguageDetector.detect_language(path) or "Other"
            file_languages[rel] = lang
            
            try:
                size = path.stat().st_size
                language_bytes[lang] = language_bytes.get(lang, 0) + size
                if size < 500_000: # read lines for reasonable files
                    total_lines += sum(1 for _ in open(path, "rb"))
            except Exception:
                pass

        primary_lang = max(language_bytes.items(), key=lambda x: x[1])[0] if language_bytes else "Unknown"
        stats = RepoStats(
            total_files=len(files),
            total_lines=total_lines,
            languages=language_bytes,
            primary_language=primary_lang
        )

        return files, file_languages, stats

    @staticmethod
    def build_file_tree(repo_dir: Path, current_path: Path = None) -> List[FileTreeItem]:
        if current_path is None:
            current_path = repo_dir

        items: List[FileTreeItem] = []
        try:
            entries = sorted(list(current_path.iterdir()), key=lambda e: (not e.is_dir(), e.name.lower()))
        except Exception:
            return []

        for entry in entries:
            if LanguageDetector.is_ignored_path(entry):
                continue

            rel_path = str(entry.relative_to(repo_dir)).replace("\\", "/")
            if entry.is_dir():
                children = RepoService.build_file_tree(repo_dir, entry)
                if children: # Only include directories with visible contents
                    items.append(
                        FileTreeItem(
                            name=entry.name,
                            path=rel_path,
                            type="directory",
                            children=children
                        )
                    )
            else:
                items.append(
                    FileTreeItem(
                        name=entry.name,
                        path=rel_path,
                        type="file",
                        size=entry.stat().st_size,
                        extension=entry.suffix.lower()
                    )
                )

        return items

    @staticmethod
    def get_file_content(repo_id: str, relative_path: str) -> Dict[str, Any]:
        repo_dir = RepoService.get_repo_dir(repo_id)
        file_path = (repo_dir / relative_path).resolve()

        # Security check: prevent directory traversal
        if not str(file_path).startswith(str(repo_dir.resolve())):
            raise ValueError("Unauthorized path traversal attempt.")

        if not file_path.exists() or not file_path.is_file():
            raise FileNotFoundError(f"File '{relative_path}' not found in repository.")

        content = file_path.read_text(encoding="utf-8", errors="replace")
        lines = content.splitlines()
        lang = LanguageDetector.detect_language(file_path) or "text"

        return {
            "path": relative_path,
            "filename": file_path.name,
            "language": lang,
            "total_lines": len(lines),
            "content": content,
            "lines": lines
        }

repo_service = RepoService()
