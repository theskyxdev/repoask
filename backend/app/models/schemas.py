import re
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, field_validator
from datetime import datetime

# --- Repository Schemas ---
class RepoCloneRequest(BaseModel):
    url: str = Field(..., description="Public GitHub repository URL")
    branch: Optional[str] = Field(None, description="Branch to checkout (defaults to default branch)")
    depth: int = Field(1, description="Git clone depth")

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        clean = v.strip()
        if not re.match(r"^https?://[a-zA-Z0-9_\-\.]+(?:/[a-zA-Z0-9_\-\.\~%]+)+/?(?:\.git)?$", clean):
            raise ValueError("Invalid repository URL. Must be an HTTP/HTTPS repository URL.")
        if any(bad in clean.lower() for bad in ["file://", "ssh://", "--", ";", "|", "&", "$", "`"]):
            raise ValueError("URL contains prohibited characters or insecure protocols.")
        return clean

    @field_validator("branch")
    @classmethod
    def validate_branch(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            clean = v.strip()
            if not clean:
                return None
            if not re.match(r"^[a-zA-Z0-9_\-\./]+$", clean) or ".." in clean or clean.startswith("-"):
                raise ValueError("Invalid branch name.")
            return clean
        return v

class RepoStats(BaseModel):
    total_files: int = 0
    total_lines: int = 0
    total_functions: int = 0
    total_classes: int = 0
    total_imports: int = 0
    languages: Dict[str, int] = Field(default_factory=dict)
    primary_language: str = "Unknown"

class RepoMetadata(BaseModel):
    id: str
    name: str
    owner: str
    url: str
    default_branch: str = "main"
    description: Optional[str] = None
    status: str = "idle" # idle, cloning, parsing, indexing, ready, error
    progress: int = 0 # 0-100
    current_step: str = ""
    stats: RepoStats = Field(default_factory=RepoStats)
    indexed_at: Optional[datetime] = None
    error_message: Optional[str] = None

# --- AST & Parsing Schemas ---
class ASTNode(BaseModel):
    id: str
    repo_id: str
    file_path: str
    type: str  # function, class, method, interface, enum, module
    name: str
    parent_name: Optional[str] = None
    start_line: int
    end_line: int
    code: str
    docstring: Optional[str] = None
    parameters: List[str] = Field(default_factory=list)
    return_type: Optional[str] = None
    calls: List[str] = Field(default_factory=list)
    imports: List[str] = Field(default_factory=list)
    tokens: int = 0

class FileTreeItem(BaseModel):
    name: str
    path: str
    type: str # "file" | "directory"
    size: int = 0
    extension: Optional[str] = None
    children: Optional[List["FileTreeItem"]] = None
    functions_count: int = 0
    classes_count: int = 0

# --- Dependency Graph Schemas ---
class DependencyNode(BaseModel):
    id: str
    name: str
    path: str
    type: str # "module", "file", "package"
    imports_count: int = 0
    imported_by_count: int = 0
    degree: int = 0
    cluster: Optional[str] = None

class DependencyEdge(BaseModel):
    source: str
    target: str
    type: str = "import" # "import", "call", "inheritance"
    weight: int = 1

class DependencyGraphData(BaseModel):
    nodes: List[DependencyNode] = Field(default_factory=list)
    edges: List[DependencyEdge] = Field(default_factory=list)
    circular_dependencies: List[List[str]] = Field(default_factory=list)
    hub_modules: List[str] = Field(default_factory=list)

# --- Chat & Evidence Schemas ---
class Citation(BaseModel):
    file_path: str
    start_line: int
    end_line: int
    code_snippet: str
    symbol_name: Optional[str] = None
    relevance_reason: Optional[str] = None

class ChatQueryRequest(BaseModel):
    repo_id: str
    query: str
    conversation_id: Optional[str] = None
    gemini_api_key: Optional[str] = None
    top_k: int = 6

class ChatMessage(BaseModel):
    id: str
    role: str # "user" | "assistant"
    content: str
    citations: List[Citation] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ChatResponse(BaseModel):
    conversation_id: str
    message: ChatMessage
    model_used: str

# --- Security Scanner Schemas ---
class SecurityVulnerability(BaseModel):
    id: str
    title: str
    severity: str # "CRITICAL" | "HIGH" | "MEDIUM" | "LOW"
    category: str # "Hardcoded Secret", "Unsafe Eval", "SQL Injection", "XSS", "Weak JWT", "Insecure Deserialization"
    file_path: str
    line_number: int
    snippet: str
    description: str
    remediation: str

class SecurityScanReport(BaseModel):
    repo_id: str
    security_score: int # 0-100 (100 being most secure)
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    vulnerabilities: List[SecurityVulnerability] = Field(default_factory=list)
    summary: str

# --- Code Review Schemas ---
class CodeReviewItem(BaseModel):
    id: str
    file_path: str
    line_number: int
    category: str # "performance", "security", "dead_code", "large_file", "unused_import", "best_practice"
    severity: str # "high", "medium", "low", "info"
    title: str
    suggestion: str
    code_snippet: Optional[str] = None

class CodeReviewReport(BaseModel):
    repo_id: str
    review_score: int # 0-100
    items: List[CodeReviewItem] = Field(default_factory=list)
    summary: str

# --- Architecture Schemas ---
class ArchitectureFlowStep(BaseModel):
    step: int
    actor: str
    action: str
    target: str
    file_reference: Optional[str] = None

class ArchitectureFlow(BaseModel):
    title: str
    description: str
    steps: List[ArchitectureFlowStep] = Field(default_factory=list)

class ArchitectureSummary(BaseModel):
    repo_id: str
    overview: str
    tech_stack: List[str] = Field(default_factory=list)
    design_patterns: List[str] = Field(default_factory=list)
    request_flow: Optional[ArchitectureFlow] = None
    auth_flow: Optional[ArchitectureFlow] = None
    database_flow: Optional[ArchitectureFlow] = None

# --- Documentation Schemas ---
class DocGenerationRequest(BaseModel):
    repo_id: str
    doc_type: str # "readme" | "architecture" | "folder_structure" | "api" | "developer_guide"
    gemini_api_key: Optional[str] = None

class GeneratedDoc(BaseModel):
    doc_type: str
    title: str
    markdown_content: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)

# --- Search Schemas ---
class SearchRequest(BaseModel):
    repo_id: str
    query: str
    search_type: str = "all" # "all" | "functions" | "classes" | "files" | "imports"
    limit: int = 20

class SearchResultItem(BaseModel):
    type: str # "function" | "class" | "file" | "import"
    name: str
    file_path: str
    line_number: int
    code_preview: str
    score: float = 1.0
