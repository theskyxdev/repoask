import ast
import re
import uuid
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from app.models.schemas import ASTNode

class ASTParser:
    """
    Language-aware AST & Structural Code Intelligence Parser.
    Extracts functions, methods, classes, interfaces, imports, and calls
    with exact line numbers and code boundaries.
    """

    @staticmethod
    def parse_file(repo_id: str, relative_path: str, full_path: Path, language: str) -> List[ASTNode]:
        try:
            content = full_path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return []

        lines = content.splitlines()
        total_lines = len(lines)
        if total_lines == 0:
            return []

        if language == "Python":
            return ASTParser._parse_python(repo_id, relative_path, content, lines)
        elif language in ("JavaScript", "TypeScript"):
            return ASTParser._parse_javascript(repo_id, relative_path, content, lines, language)
        elif language in ("Go", "Rust", "Java", "C++", "C", "C#"):
            return ASTParser._parse_c_family(repo_id, relative_path, content, lines, language)
        else:
            return ASTParser._parse_generic_module(repo_id, relative_path, content, lines, language)

    # ----------------------------------------------------
    # PYTHON PARSER (Pure Python AST)
    # ----------------------------------------------------
    @staticmethod
    def _parse_python(repo_id: str, file_path: str, content: str, lines: List[str]) -> List[ASTNode]:
        nodes: List[ASTNode] = []
        try:
            tree = ast.parse(content)
        except SyntaxError:
            # Fallback to regex parser if syntax error exists in file
            return ASTParser._parse_c_family(repo_id, file_path, content, lines, "Python")

        file_imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    file_imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                for alias in node.names:
                    file_imports.append(f"{mod}.{alias.name}" if mod else alias.name)

        class Visitor(ast.NodeVisitor):
            def __init__(self):
                self.current_class: Optional[str] = None

            def visit_ClassDef(self, node: ast.ClassDef):
                start = node.lineno
                end = getattr(node, "end_lineno", start + len(node.body))
                code_snippet = "\n".join(lines[start - 1 : end])
                doc = ast.get_docstring(node)
                bases = [ast.unparse(b) for b in node.bases if hasattr(ast, "unparse")]

                nodes.append(
                    ASTNode(
                        id=f"{repo_id}:{file_path}:{node.name}:{start}",
                        repo_id=repo_id,
                        file_path=file_path,
                        type="class",
                        name=node.name,
                        parent_name=bases[0] if bases else None,
                        start_line=start,
                        end_line=end,
                        code=code_snippet,
                        docstring=doc,
                        parameters=bases,
                        calls=[],
                        imports=file_imports,
                        tokens=len(code_snippet.split()),
                    )
                )

                old_class = self.current_class
                self.current_class = node.name
                self.generic_visit(node)
                self.current_class = old_class

            def visit_FunctionDef(self, node: ast.FunctionDef):
                self._handle_function(node, is_async=False)

            def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
                self._handle_function(node, is_async=True)

            def _handle_function(self, node, is_async: bool):
                start = node.lineno
                end = getattr(node, "end_lineno", start + len(node.body))
                code_snippet = "\n".join(lines[start - 1 : end])
                doc = ast.get_docstring(node)

                params = [arg.arg for arg in node.args.args]
                calls = []
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        if isinstance(child.func, ast.Name):
                            calls.append(child.func.id)
                        elif isinstance(child.func, ast.Attribute):
                            calls.append(child.func.attr)

                node_type = "method" if self.current_class else "function"
                nodes.append(
                    ASTNode(
                        id=f"{repo_id}:{file_path}:{node.name}:{start}",
                        repo_id=repo_id,
                        file_path=file_path,
                        type=node_type,
                        name=node.name,
                        parent_name=self.current_class,
                        start_line=start,
                        end_line=end,
                        code=code_snippet,
                        docstring=doc,
                        parameters=params,
                        calls=list(set(calls)),
                        imports=file_imports,
                        tokens=len(code_snippet.split()),
                    )
                )
                self.generic_visit(node)

        visitor = Visitor()
        visitor.visit(tree)

        # Also add a module-level node for the file if there are global imports / summary
        if not nodes:
            nodes.append(
                ASTNode(
                    id=f"{repo_id}:{file_path}:module:1",
                    repo_id=repo_id,
                    file_path=file_path,
                    type="module",
                    name=Path(file_path).name,
                    parent_name=None,
                    start_line=1,
                    end_line=len(lines),
                    code=content[:3000],
                    docstring="Top-level script or configuration module",
                    parameters=[],
                    calls=[],
                    imports=file_imports,
                    tokens=len(content.split()),
                )
            )

        return nodes

    # ----------------------------------------------------
    # TYPESCRIPT / JAVASCRIPT PARSER
    # ----------------------------------------------------
    @staticmethod
    def _parse_javascript(repo_id: str, file_path: str, content: str, lines: List[str], language: str) -> List[ASTNode]:
        nodes: List[ASTNode] = []
        
        # Extract imports
        imports = []
        import_patterns = [
            r'import\s+.*?from\s+[\'"](.*?)[\'"]',
            r'require\([\'"](.*?)[\'"]\)',
        ]
        for pat in import_patterns:
            imports.extend(re.findall(pat, content))

        # Detect Classes and Interfaces
        class_pattern = re.compile(r'(?:export\s+)?(?:default\s+)?(class|interface)\s+([A-Za-z0-9_$]+)(?:\s+extends\s+([A-Za-z0-9_$.]+))?')
        # Detect Functions
        func_pattern = re.compile(
            r'(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s+([A-Za-z0-9_$]+)\s*\((.*?)\)|'
            r'(?:export\s+)?(?:const|let|var)\s+([A-Za-z0-9_$]+)\s*=\s*(?:async\s*)?\((.*?)\)\s*=>|'
            r'(?:export\s+)?(?:const|let|var)\s+([A-Za-z0-9_$]+)\s*=\s*function'
        )

        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            # Check Class
            m_class = class_pattern.search(line)
            if m_class and "{" in line:
                kind = m_class.group(1) # class or interface
                name = m_class.group(2)
                extends = m_class.group(3)
                end = ASTParser._find_closing_brace(lines, i - 1)
                code_snippet = "\n".join(lines[i - 1 : end])
                nodes.append(
                    ASTNode(
                        id=f"{repo_id}:{file_path}:{name}:{i}",
                        repo_id=repo_id,
                        file_path=file_path,
                        type="class" if kind == "class" else "interface",
                        name=name,
                        parent_name=extends,
                        start_line=i,
                        end_line=end,
                        code=code_snippet,
                        docstring=ASTParser._find_preceding_doc(lines, i - 1),
                        parameters=[extends] if extends else [],
                        calls=[],
                        imports=imports,
                        tokens=len(code_snippet.split()),
                    )
                )
                continue

            # Check Function
            m_func = func_pattern.search(line)
            if m_func:
                name = m_func.group(1) or m_func.group(3) or m_func.group(5)
                raw_params = m_func.group(2) or m_func.group(4) or ""
                params = [p.strip() for p in raw_params.split(",") if p.strip()]
                end = ASTParser._find_closing_brace(lines, i - 1)
                code_snippet = "\n".join(lines[i - 1 : end])
                nodes.append(
                    ASTNode(
                        id=f"{repo_id}:{file_path}:{name}:{i}",
                        repo_id=repo_id,
                        file_path=file_path,
                        type="function",
                        name=name,
                        parent_name=None,
                        start_line=i,
                        end_line=end,
                        code=code_snippet,
                        docstring=ASTParser._find_preceding_doc(lines, i - 1),
                        parameters=params,
                        calls=[],
                        imports=imports,
                        tokens=len(code_snippet.split()),
                    )
                )

        if not nodes:
            return ASTParser._parse_generic_module(repo_id, file_path, content, lines, language, imports)

        return nodes

    # ----------------------------------------------------
    # C-FAMILY (Go, Rust, Java, C++, C, C#)
    # ----------------------------------------------------
    @staticmethod
    def _parse_c_family(repo_id: str, file_path: str, content: str, lines: List[str], language: str) -> List[ASTNode]:
        nodes: List[ASTNode] = []
        imports = []

        # General imports
        if language == "Go":
            imports = re.findall(r'"([a-zA-Z0-9_\-\./]+)"', content)
        elif language in ("Java", "Rust"):
            imports = re.findall(r'(?:import|use)\s+([a-zA-Z0-9_:\.\*]+);', content)

        # Regex for Go / Java / Rust / C++ functions
        func_regex = re.compile(
            r'(?:func\s+(?:\([^\)]+\)\s+)?([A-Za-z0-9_]+)\s*\(|'
            r'(?:public|private|protected|fn)\s+(?:static\s+)?[A-Za-z0-9_<>,\[\]\s]+\s+([A-Za-z0-9_]+)\s*\()'
        )

        for i, line in enumerate(lines, 1):
            m = func_regex.search(line)
            if m:
                name = m.group(1) or m.group(2)
                if not name or name in ("if", "for", "while", "switch"):
                    continue
                end = ASTParser._find_closing_brace(lines, i - 1)
                code_snippet = "\n".join(lines[i - 1 : end])
                nodes.append(
                    ASTNode(
                        id=f"{repo_id}:{file_path}:{name}:{i}",
                        repo_id=repo_id,
                        file_path=file_path,
                        type="function",
                        name=name,
                        parent_name=None,
                        start_line=i,
                        end_line=end,
                        code=code_snippet,
                        docstring=ASTParser._find_preceding_doc(lines, i - 1),
                        parameters=[],
                        calls=[],
                        imports=imports,
                        tokens=len(code_snippet.split()),
                    )
                )

        if not nodes:
            return ASTParser._parse_generic_module(repo_id, file_path, content, lines, language, imports)

        return nodes

    # ----------------------------------------------------
    # FALLBACK / GENERIC MODULE
    # ----------------------------------------------------
    @staticmethod
    def _parse_generic_module(repo_id: str, file_path: str, content: str, lines: List[str], language: str, imports: Optional[List[str]] = None) -> List[ASTNode]:
        snippet = "\n".join(lines[:100])
        return [
            ASTNode(
                id=f"{repo_id}:{file_path}:module:1",
                repo_id=repo_id,
                file_path=file_path,
                type="module",
                name=Path(file_path).name,
                parent_name=None,
                start_line=1,
                end_line=len(lines),
                code=snippet,
                docstring=f"{language} source file",
                parameters=[],
                calls=[],
                imports=imports or [],
                tokens=len(snippet.split()),
            )
        ]

    # Helper: Find matching brace
    @staticmethod
    def _find_closing_brace(lines: List[str], start_idx: int) -> int:
        open_count = 0
        found_first = False
        for idx in range(start_idx, min(len(lines), start_idx + 300)):
            line = lines[idx]
            for char in line:
                if char == "{":
                    open_count += 1
                    found_first = True
                elif char == "}":
                    open_count -= 1
                    if found_first and open_count <= 0:
                        return idx + 1
        return min(len(lines), start_idx + 40)

    # Helper: Preceding Docstring
    @staticmethod
    def _find_preceding_doc(lines: List[str], start_idx: int) -> Optional[str]:
        doc_lines = []
        idx = start_idx - 1
        while idx >= 0:
            l = lines[idx].strip()
            if l.startswith(("//", "#", "/*", "*", '"""', "'''")):
                clean = l.lstrip("/*# '\"").rstrip("*/'\" ")
                if clean:
                    doc_lines.insert(0, clean)
                idx -= 1
            else:
                break
        return " ".join(doc_lines) if doc_lines else None
