from typing import List, Dict, Optional, Any
from pathlib import Path
from app.models.schemas import GeneratedDoc, RepoMetadata, ASTNode
from app.core.config import settings

class DocGenerator:
    @staticmethod
    def generate_doc(
        repo_meta: RepoMetadata,
        doc_type: str,
        files: List[str],
        ast_nodes: List[ASTNode],
        api_key: Optional[str] = None
    ) -> GeneratedDoc:
        
        effective_key = api_key or settings.GEMINI_API_KEY
        title_map = {
            "readme": "Production README.md",
            "architecture": "Architecture & System Design Guide",
            "folder_structure": "Repository Folder Tree & Component Guide",
            "api": "API & Interface Specification",
            "developer_guide": "Developer Onboarding & Setup Guide",
        }
        title = title_map.get(doc_type, "Repository Documentation")

        # Top functions and classes
        classes = [n for n in ast_nodes if n.type == "class"]
        functions = [n for n in ast_nodes if n.type in ("function", "method")]

        if doc_type == "readme":
            content = DocGenerator._generate_readme(repo_meta, files, classes, functions)
        elif doc_type == "architecture":
            content = DocGenerator._generate_architecture(repo_meta, files, classes, functions)
        elif doc_type == "folder_structure":
            content = DocGenerator._generate_folder_structure(repo_meta, files)
        elif doc_type == "api":
            content = DocGenerator._generate_api_doc(repo_meta, functions, classes)
        elif doc_type == "developer_guide":
            content = DocGenerator._generate_developer_guide(repo_meta)
        else:
            content = DocGenerator._generate_readme(repo_meta, files, classes, functions)

        return GeneratedDoc(
            doc_type=doc_type,
            title=title,
            markdown_content=content
        )

    @staticmethod
    def _generate_readme(meta: RepoMetadata, files: List[str], classes: List[ASTNode], functions: List[ASTNode]) -> str:
        lang_badges = " ".join([f"`{lang}`" for lang in meta.stats.languages.keys()])
        return f"""# {meta.name}

> {meta.description or f'High-performance repository powered by {meta.stats.primary_language}.'}

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-success)](#)
[![Languages](https://img.shields.io/badge/Stack-{meta.stats.primary_language}-black)](#)

---

## ⚡ Overview

**{meta.name}** is structured across **{meta.stats.total_files} files** and **{meta.stats.total_lines:,} lines of code**.
Language breakdown: {lang_badges}.

### Key Metrics
- **Classes / Modules**: {meta.stats.total_classes}
- **Functions / Methods**: {meta.stats.total_functions}
- **Primary Language**: {meta.stats.primary_language}

---

## 🏗 Architecture & Core Components

| Component | File Path | Description |
|-----------|-----------|-------------|
{DocGenerator._format_components_table(classes, functions)}

---

## 🚀 Quickstart & Installation

### 1. Clone the repository
```bash
git clone {meta.url}
cd {meta.name}
```

### 2. Install dependencies
```bash
# If Python:
pip install -r requirements.txt

# If Node.js / TypeScript:
npm install
```

### 3. Run the development server
```bash
# Start application
npm run dev # or uvicorn app.main:app --reload
```

---

## 📂 Project Organization
See [`ARCHITECTURE.md`](#) and [`FOLDER_STRUCTURE.md`](#) for module-by-module navigation.
"""

    @staticmethod
    def _generate_architecture(meta: RepoMetadata, files: List[str], classes: List[ASTNode], functions: List[ASTNode]) -> str:
        return f"""# System Architecture: {meta.name}

## 1. High-Level Design
`{meta.name}` adheres to modular software engineering patterns. The codebase partitions responsibilities across routing, service business logic, and persistence.

```mermaid
graph TD
    Client[Client / Consumer] --> Router[API / Entry Router]
    Router --> ServiceLayer[Service & Processing Layer]
    ServiceLayer --> DataStore[(Persistence & Models)]
    ServiceLayer --> CoreUtils[Core Utilities & Config]
```

## 2. Core Modules & Entities

### Primary Domain Classes
{chr(10).join([f'- **`{c.name}`** (`{c.file_path}`): {c.docstring or "Domain entity / controller"}' for c in classes[:10]]) or "Modular functional architecture without heavy class hierarchies."}

### Key Public Functions & Handlers
{chr(10).join([f'- **`{f.name}`** (`{f.file_path}:{f.start_line}`): `{f.parameters}`' for f in functions[:12]])}

## 3. Data & Request Flow
1. **Entry**: Incoming requests or CLI entry points validate input parameters.
2. **Execution**: Core processing logic is delegated to single-responsibility functions.
3. **Output**: Structured responses or mutated states are committed and returned.
"""

    @staticmethod
    def _generate_folder_structure(meta: RepoMetadata, files: List[str]) -> str:
        # Group files by top-level folder
        tree_map: Dict[str, List[str]] = {}
        for f in sorted(files):
            parts = f.split("/")
            top = parts[0] if len(parts) > 1 else "(root)"
            tree_map.setdefault(top, []).append(f)

        sections = []
        for top, file_list in tree_map.items():
            file_sample = "\n".join([f"  ├── {Path(f).name}" for f in file_list[:8]])
            if len(file_list) > 8:
                file_sample += f"\n  └── ... ({len(file_list) - 8} more files)"
            sections.append(f"### `/{top}` ({len(file_list)} files)\n```text\n{top}/\n{file_sample}\n```")

        return f"""# Repository Folder Structure: {meta.name}

Total Indexed Files: **{len(files)}**

{chr(10).join(sections)}
"""

    @staticmethod
    def _generate_api_doc(meta: RepoMetadata, functions: List[ASTNode], classes: List[ASTNode]) -> str:
        routes = [f for f in functions if any(k in f.name.lower() for k in ("get", "post", "put", "delete", "handle", "route", "api", "query"))]
        target_funcs = routes if routes else functions[:15]

        items = []
        for fn in target_funcs:
            params_str = ", ".join(fn.parameters) if fn.parameters else "None"
            items.append(f"""### `{fn.name}({params_str})`
- **Location**: `{fn.file_path}` (Lines {fn.start_line}–{fn.end_line})
- **Docstring**: {fn.docstring or "No docstring provided."}
- **Parameters**: `{params_str}`
```python
# Function Signature
{fn.code.splitlines()[0] if fn.code else f'def {fn.name}()'}
```
""")

        return f"""# API & Interface Specification: {meta.name}

This document details primary callable interfaces, API routers, and export functions discovered by RepoAsk AST parser.

{chr(10).join(items)}
"""

    @staticmethod
    def _generate_developer_guide(meta: RepoMetadata) -> str:
        return f"""# Developer Onboarding Guide: {meta.name}

Welcome to `{meta.name}`. This guide covers local environment setup, code formatting conventions, and testing workflows.

## Prerequisites
- **Git** >= 2.30
- **{meta.stats.primary_language}** Runtime Environment

## Environment Setup
1. Clone the repository and configure local environment:
```bash
git clone {meta.url}
cd {meta.name}
cp .env.example .env
```
2. Configure required keys in `.env`.

## Coding Standards & Conventions
- Maintain single-responsibility modules.
- Ensure all public functions have type annotations and descriptive docstrings.
- Adhere to the established repository AST architecture.

## Running Tests & Linting
```bash
# Run test suite
pytest -v  # or npm test
```
"""

    @staticmethod
    def _format_components_table(classes: List[ASTNode], functions: List[ASTNode]) -> str:
        rows = []
        sample = (classes + functions)[:10]
        for item in sample:
            desc = item.docstring.splitlines()[0] if item.docstring else f"{item.type.capitalize()} implementation"
            rows.append(f"| `{item.name}` | `{item.file_path}:{item.start_line}` | {desc[:60]} |")
        return "\n".join(rows) if rows else "| Main | `(root)` | Application core |"

doc_generator = DocGenerator()
