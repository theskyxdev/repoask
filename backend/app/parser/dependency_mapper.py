import networkx as nx
from pathlib import Path
from typing import List, Dict, Set, Tuple, Any, Optional
from app.models.schemas import DependencyNode, DependencyEdge, DependencyGraphData, ASTNode

class DependencyMapper:
    """
    Builds and analyzes dependency graphs across repository modules and AST symbols using NetworkX.
    Detects imports, call flows, hub modules, and circular dependencies.
    """

    @staticmethod
    def build_graph(repo_id: str, files: List[str], ast_nodes: List[ASTNode]) -> DependencyGraphData:
        G = nx.DiGraph()

        # Add all file nodes
        normalized_files = set()
        file_to_nodes: Dict[str, List[ASTNode]] = {}
        for f in files:
            norm = f.replace("\\", "/").lstrip("/")
            normalized_files.add(norm)
            G.add_node(norm, label=Path(norm).name, type="file")
            file_to_nodes[norm] = []

        for node in ast_nodes:
            norm_path = node.file_path.replace("\\", "/").lstrip("/")
            if norm_path in file_to_nodes:
                file_to_nodes[norm_path].append(node)

        # Map imports between files
        edges_set: Set[Tuple[str, str, str]] = set()

        for f_path in normalized_files:
            nodes_in_file = file_to_nodes.get(f_path, [])
            all_imports = set()
            for n in nodes_in_file:
                for imp in n.imports:
                    all_imports.add(imp)

            for imp in all_imports:
                target_file = DependencyMapper._resolve_import(f_path, imp, normalized_files)
                if target_file and target_file != f_path:
                    G.add_edge(f_path, target_file, type="import")
                    edges_set.add((f_path, target_file, "import"))

        # Find circular dependencies
        circular_deps: List[List[str]] = []
        try:
            cycles = list(nx.simple_cycles(G))
            for cycle in cycles[:10]: # Limit to top 10 cycles
                if len(cycle) > 1:
                    circular_deps.append(cycle)
        except Exception:
            pass

        # Identify central hub modules using PageRank or in-degree
        hub_modules: List[str] = []
        try:
            in_degrees = dict(G.in_degree())
            sorted_by_indegree = sorted(in_degrees.items(), key=lambda x: x[1], reverse=True)
            hub_modules = [item[0] for item in sorted_by_indegree if item[1] > 0][:8]
        except Exception:
            pass

        # Build response nodes and edges
        dep_nodes: List[DependencyNode] = []
        for node_id in G.nodes():
            in_deg = G.in_degree(node_id)
            out_deg = G.out_degree(node_id)
            cluster = Path(node_id).parts[0] if len(Path(node_id).parts) > 1 else "root"
            dep_nodes.append(
                DependencyNode(
                    id=node_id,
                    name=Path(node_id).name,
                    path=node_id,
                    type="file",
                    imports_count=out_deg,
                    imported_by_count=in_deg,
                    degree=in_deg + out_deg,
                    cluster=cluster
                )
            )

        dep_edges: List[DependencyEdge] = [
            DependencyEdge(source=src, target=tgt, type=etype, weight=1)
            for src, tgt, etype in edges_set
        ]

        return DependencyGraphData(
            nodes=dep_nodes,
            edges=dep_edges,
            circular_dependencies=circular_deps,
            hub_modules=hub_modules
        )

    @staticmethod
    def _resolve_import(current_file: str, import_str: str, all_files: Set[str]) -> Optional[str]:
        current_dir = Path(current_file).parent
        clean_imp = import_str.replace("\\", "/").strip("'\"")

        # Handle JS/TS relative imports like "./utils", "../auth/routes"
        if clean_imp.startswith("./") or clean_imp.startswith("../"):
            candidate = (current_dir / clean_imp).resolve()
            # Try extensions
            for ext in ["", ".ts", ".tsx", ".js", ".jsx", "/index.ts", "/index.js"]:
                c_str = str(candidate) + ext
                c_norm = c_str.replace("\\", "/").lstrip("/")
                if c_norm in all_files:
                    return c_norm
            return None

        # Handle Python dotted imports like "auth.routes", "app.core.config"
        py_path = clean_imp.replace(".", "/")
        for ext in [".py", "/__init__.py"]:
            candidate = py_path + ext
            if candidate in all_files:
                return candidate
            # also check relative to current dir or src
            cand2 = f"src/{candidate}"
            if cand2 in all_files:
                return cand2
            cand3 = f"app/{candidate}"
            if cand3 in all_files:
                return cand3

        # Direct filename check
        for f in all_files:
            if f.endswith(f"/{clean_imp}.py") or f.endswith(f"/{clean_imp}.ts") or f.endswith(f"/{clean_imp}.js"):
                return f

        return None
