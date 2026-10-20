export interface RepoStats {
  total_files: number;
  total_lines: number;
  total_functions: number;
  total_classes: number;
  total_imports: number;
  languages: Record<string, number>;
  primary_language: string;
}

export interface RepoMetadata {
  id: string;
  name: string;
  owner: string;
  url: string;
  default_branch: string;
  description?: string;
  status: "idle" | "cloning" | "parsing" | "indexing" | "ready" | "error";
  progress: number;
  current_step: string;
  stats: RepoStats;
  indexed_at?: string;
  error_message?: string;
}

export interface Citation {
  file_path: string;
  start_line: number;
  end_line: number;
  code_snippet: string;
  symbol_name?: string;
  relevance_reason?: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations: Citation[];
  created_at: string;
}

export interface ChatResponse {
  conversation_id: string;
  message: ChatMessage;
  model_used: string;
}

export interface FileTreeItem {
  name: string;
  path: string;
  type: "file" | "directory";
  size?: number;
  extension?: string;
  children?: FileTreeItem[];
  functions_count?: number;
  classes_count?: number;
}

export interface DependencyNode {
  id: string;
  name: string;
  path: string;
  type: string;
  imports_count: number;
  imported_by_count: number;
  degree: number;
  cluster?: string;
}

export interface DependencyEdge {
  source: string;
  target: string;
  type: string;
  weight: number;
}

export interface DependencyGraphData {
  nodes: DependencyNode[];
  edges: DependencyEdge[];
  circular_dependencies: string[][];
  hub_modules: string[];
}

export interface SecurityVulnerability {
  id: string;
  title: string;
  severity: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";
  category: string;
  file_path: string;
  line_number: number;
  snippet: string;
  description: string;
  remediation: string;
}

export interface SecurityScanReport {
  repo_id: string;
  security_score: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  vulnerabilities: SecurityVulnerability[];
  summary: string;
}

export interface CodeReviewItem {
  id: string;
  file_path: string;
  line_number: number;
  category: "performance" | "security" | "dead_code" | "large_file" | "unused_import" | "best_practice";
  severity: "high" | "medium" | "low" | "info";
  title: string;
  suggestion: string;
  code_snippet?: string;
}

export interface CodeReviewReport {
  repo_id: string;
  review_score: number;
  items: CodeReviewItem[];
  summary: string;
}

export interface ArchitectureFlowStep {
  step: number;
  actor: string;
  action: string;
  target: string;
  file_reference?: string;
}

export interface ArchitectureFlow {
  title: string;
  description: string;
  steps: ArchitectureFlowStep[];
}

export interface ArchitectureSummary {
  repo_id: string;
  overview: string;
  tech_stack: string[];
  design_patterns: string[];
  request_flow?: ArchitectureFlow;
  auth_flow?: ArchitectureFlow;
  database_flow?: ArchitectureFlow;
}

export interface GeneratedDoc {
  doc_type: string;
  title: string;
  markdown_content: string;
  generated_at?: string;
}

export interface SearchResultItem {
  type: "function" | "class" | "file" | "import";
  name: string;
  file_path: string;
  line_number: number;
  code_preview: string;
  score: number;
}
