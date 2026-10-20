from pathlib import Path
from typing import Dict, Optional, Tuple, Set

EXTENSION_LANGUAGE_MAP: Dict[str, str] = {
    # Python
    ".py": "Python",
    ".pyw": "Python",
    ".pyx": "Python",
    # TypeScript / JavaScript
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".mjs": "JavaScript",
    ".cjs": "JavaScript",
    # Go
    ".go": "Go",
    # Rust
    ".rs": "Rust",
    # Java & Kotlin
    ".java": "Java",
    ".kt": "Kotlin",
    ".kts": "Kotlin",
    # C / C++ / C#
    ".c": "C",
    ".h": "C",
    ".cpp": "C++",
    ".hpp": "C++",
    ".cc": "C++",
    ".cs": "C#",
    # Web & Style
    ".html": "HTML",
    ".css": "CSS",
    ".scss": "SCSS",
    ".vue": "Vue",
    ".svelte": "Svelte",
    # Scripts & Data
    ".sh": "Shell",
    ".bash": "Shell",
    ".ps1": "PowerShell",
    ".sql": "SQL",
    ".json": "JSON",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".toml": "TOML",
    ".md": "Markdown",
}

IGNORED_DIRECTORIES: Set[str] = {
    ".git",
    ".github",
    ".vscode",
    ".idea",
    "node_modules",
    "vendor",
    "venv",
    ".venv",
    "env",
    "__pycache__",
    "dist",
    "build",
    "out",
    ".next",
    ".turbo",
    "coverage",
    ".pytest_cache",
    ".mypy_cache",
    "target",
    "bin",
    "obj",
}

IGNORED_EXTENSIONS: Set[str] = {
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".webp",
    ".pdf", ".zip", ".tar", ".gz", ".7z", ".rar",
    ".exe", ".dll", ".so", ".dylib", ".bin",
    ".lock", ".lockb", ".wasm", ".pyc", ".map",
}

class LanguageDetector:
    @staticmethod
    def is_ignored_path(path: Path) -> bool:
        for part in path.parts:
            if part in IGNORED_DIRECTORIES or part.startswith("."):
                return True
        if path.suffix.lower() in IGNORED_EXTENSIONS:
            return True
        if ".min." in path.name.lower() or path.name.endswith(".bundle.js"):
            return True
        return False

    @staticmethod
    def detect_language(file_path: Path) -> Optional[str]:
        if LanguageDetector.is_ignored_path(file_path):
            return None
        
        # Check special filenames
        name = file_path.name.lower()
        if name in ("dockerfile", "containerfile"):
            return "Dockerfile"
        if name in ("makefile", "gnumakefile"):
            return "Makefile"
        
        ext = file_path.suffix.lower()
        return EXTENSION_LANGUAGE_MAP.get(ext, None)
