import re
import uuid
from pathlib import Path
from typing import List, Dict, Any
from app.models.schemas import CodeReviewItem, CodeReviewReport, ASTNode

class CodeReviewer:
    @staticmethod
    def review_repository(repo_id: str, repo_dir: Path, files: List[str], ast_nodes: List[ASTNode]) -> CodeReviewReport:
        items: List[CodeReviewItem] = []

        # 1. Check for Large Files (>400 lines)
        for rel_path in files:
            full_path = repo_dir / rel_path
            try:
                content = full_path.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue

            lines = content.splitlines()
            line_count = len(lines)
            if line_count > 400:
                items.append(
                    CodeReviewItem(
                        id=str(uuid.uuid4())[:8],
                        file_path=rel_path,
                        line_number=1,
                        category="large_file",
                        severity="medium",
                        title=f"File exceeds 400 lines ({line_count} lines)",
                        suggestion=f"Consider refactoring `{rel_path}` into smaller, single-responsibility modules to enhance maintainability and testability.",
                        code_snippet=f"Total lines: {line_count}"
                    )
                )

            # Check for generic exception catching `except:` or `except Exception:` without logging
            for idx, line in enumerate(lines, 1):
                stripped = line.strip()
                if re.match(r"^except\s*:\s*$", stripped) or re.match(r"^except\s+Exception\s*:\s*pass", stripped):
                    items.append(
                        CodeReviewItem(
                            id=str(uuid.uuid4())[:8],
                            file_path=rel_path,
                            line_number=idx,
                            category="best_practice",
                            severity="medium",
                            title="Silent or Bare Exception Suppression",
                            suggestion="Avoid catching bare exceptions or suppressing them with `pass`. Specify explicit exception types and log the traceback.",
                            code_snippet=stripped
                        )
                    )

                # Check for sync I/O in async functions
                if "time.sleep(" in stripped and ("async " in content or "def " in stripped):
                    items.append(
                        CodeReviewItem(
                            id=str(uuid.uuid4())[:8],
                            file_path=rel_path,
                            line_number=idx,
                            category="performance",
                            severity="high",
                            title="Blocking time.sleep() in Event Loop",
                            suggestion="Use non-blocking asynchronous sleep `await asyncio.sleep()` rather than synchronous `time.sleep()` to prevent blocking the worker event loop.",
                            code_snippet=stripped
                        )
                    )

                # Check for console.log left in production frontend files
                if ("console.log(" in stripped or "print(" in stripped) and not rel_path.startswith("test"):
                    if idx < 50 and len(items) < 15: # Sample a few
                        items.append(
                            CodeReviewItem(
                                id=str(uuid.uuid4())[:8],
                                file_path=rel_path,
                                line_number=idx,
                                category="best_practice",
                                severity="low",
                                title="Debug Print/Log Statement Detected",
                                suggestion="Remove ad-hoc `console.log` or raw `print` statements before deploying to production. Use a structured logger instead.",
                                code_snippet=stripped
                            )
                        )

        # 2. Check for unused imports in AST nodes
        for node in ast_nodes:
            if node.type == "module" and node.imports:
                for imp in node.imports:
                    # Check if imp name appears anywhere else in file code
                    clean_name = imp.split(".")[-1].split(" as ")[-1]
                    if clean_name and node.code.count(clean_name) <= 1 and len(items) < 25:
                        items.append(
                            CodeReviewItem(
                                id=str(uuid.uuid4())[:8],
                                file_path=node.file_path,
                                line_number=node.start_line,
                                category="unused_import",
                                severity="low",
                                title=f"Potential Unused Import: '{clean_name}'",
                                suggestion=f"Symbol `{clean_name}` is imported but does not appear to be referenced in `{node.file_path}`.",
                                code_snippet=f"import {imp}"
                            )
                        )

        # 3. Dead Code Detection (functions with 0 callers across the repository)
        all_calls = set()
        for node in ast_nodes:
            for call in node.calls:
                all_calls.add(call)

        for node in ast_nodes:
            if node.type in ("function", "method") and not node.name.startswith(("_", "test", "visit", "get", "post", "main")):
                if node.name not in all_calls and len(items) < 20:
                    items.append(
                        CodeReviewItem(
                            id=str(uuid.uuid4())[:8],
                            file_path=node.file_path,
                            line_number=node.start_line,
                            category="dead_code",
                            severity="info",
                            title=f"Potential Uncalled Function: `{node.name}`",
                            suggestion=f"Function `{node.name}` has no detected call references in the repository AST. Verify if this is an exported public API or dead code.",
                            code_snippet=f"def/function {node.name}"
                        )
                    )

        score = max(40, 100 - (len(items) * 3))
        summary = (
            f"Code review completed with {len(items)} optimization suggestions. "
            f"Repository scored {score}/100 based on structural quality, best practices, and code hygiene."
        )

        return CodeReviewReport(
            repo_id=repo_id,
            review_score=score,
            items=items,
            summary=summary
        )

code_reviewer = CodeReviewer()
