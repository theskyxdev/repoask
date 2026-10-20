from typing import List, Dict, Any
from app.models.schemas import ASTNode

class SmartChunker:
    """
    AST-Aware Smart Chunker.
    Never splits code by character count!
    Instead, produces semantic code units based on AST boundaries:
    - Functions / Methods
    - Classes / Interfaces
    - Module definitions
    Attaches complete contextual metadata.
    """

    @staticmethod
    def chunk_nodes(nodes: List[ASTNode], repo_name: str) -> List[Dict[str, Any]]:
        chunks: List[Dict[str, Any]] = []

        for node in nodes:
            # Build semantic search header containing symbol name, type, file path, parent
            parent_ctx = f" in class {node.parent_name}" if node.parent_name else ""
            params_ctx = f"({', '.join(node.parameters)})" if node.parameters else ""
            header = f"# File: {node.file_path} | {node.type.capitalize()} {node.name}{params_ctx}{parent_ctx} (Lines {node.start_line}-{node.end_line})\n"
            
            if node.docstring:
                header += f"# Description: {node.docstring}\n"
            
            if node.imports:
                header += f"# Dependencies: {', '.join(node.imports[:6])}\n"

            formatted_text = f"{header}\n{node.code}"

            metadata = {
                "repo_name": repo_name,
                "node_id": node.id,
                "file_path": node.file_path,
                "node_type": node.type,
                "symbol_name": node.name,
                "parent_name": node.parent_name or "",
                "start_line": int(node.start_line),
                "end_line": int(node.end_line),
                "tokens": int(node.tokens),
                "imports": ",".join(node.imports[:10]),
                "calls": ",".join(node.calls[:10]),
            }

            chunks.append({
                "id": node.id,
                "text": formatted_text,
                "metadata": metadata
            })

        return chunks
