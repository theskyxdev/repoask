import {
  RepoMetadata,
  FileTreeItem,
  ChatResponse,
  ChatMessage,
  ArchitectureSummary,
  DependencyGraphData,
  SecurityScanReport,
  CodeReviewReport,
  GeneratedDoc,
  SearchResultItem,
} from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api/v1";

class ApiClient {
  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const url = `${API_BASE}${endpoint}`;
    const res = await fetch(url, {
      headers: {
        "Content-Type": "application/json",
      },
      ...options,
    });

    if (!res.ok) {
      let errorMsg = `API request failed with status ${res.status}`;
      try {
        const errorData = await res.json();
        if (errorData.detail) errorMsg = errorData.detail;
      } catch {}
      throw new Error(errorMsg);
    }

    return res.json();
  }

  // Repository Endpoints
  async listRepos(): Promise<RepoMetadata[]> {
    return this.request<RepoMetadata[]>("/repo");
  }

  async getRepo(repoId: string): Promise<RepoMetadata> {
    return this.request<RepoMetadata>(`/repo/${repoId}`);
  }

  async cloneRepo(url: string, branch?: string): Promise<{ status: string; repo_id: string; message: string }> {
    return this.request("/repo/clone", {
      method: "POST",
      body: JSON.stringify({ url, branch, depth: 1 }),
    });
  }

  async seedDemoRepo(): Promise<{ status: string; repo_id: string; name: string; message: string }> {
    return this.request("/repo/seed-demo", {
      method: "POST",
      body: JSON.stringify({}),
    });
  }

  async getFileTree(repoId: string): Promise<FileTreeItem[]> {
    return this.request<FileTreeItem[]>(`/repo/${repoId}/tree`);
  }

  async getFileContent(repoId: string, path: string): Promise<{
    path: string;
    filename: string;
    language: string;
    total_lines: number;
    content: string;
    lines: string[];
  }> {
    const encoded = encodeURIComponent(path);
    return this.request(`/repo/${repoId}/file?path=${encoded}`);
  }

  // Chat Endpoints
  async chatQuery(
    repoId: string,
    query: string,
    conversationId?: string,
    geminiApiKey?: string
  ): Promise<ChatResponse> {
    return this.request<ChatResponse>("/chat", {
      method: "POST",
      body: JSON.stringify({
        repo_id: repoId,
        query,
        conversation_id: conversationId,
        gemini_api_key: geminiApiKey,
        top_k: 6,
      }),
    });
  }

  async getChatHistory(conversationId: string): Promise<ChatMessage[]> {
    return this.request<ChatMessage[]>(`/chat/history/${conversationId}`);
  }

  // Architecture & Dependency Endpoints
  async getArchitecture(repoId: string): Promise<ArchitectureSummary> {
    return this.request<ArchitectureSummary>(`/architecture/${repoId}`);
  }

  async getDependencyGraph(repoId: string): Promise<DependencyGraphData> {
    return this.request<DependencyGraphData>(`/dependency/${repoId}`);
  }

  // Security & Review Endpoints
  async getSecurityReport(repoId: string): Promise<SecurityScanReport> {
    return this.request<SecurityScanReport>(`/security/${repoId}`);
  }

  async getCodeReview(repoId: string): Promise<CodeReviewReport> {
    return this.request<CodeReviewReport>(`/review/${repoId}`);
  }

  // Documentation Endpoints
  async generateDoc(repoId: string, docType: string, geminiApiKey?: string): Promise<GeneratedDoc> {
    return this.request<GeneratedDoc>("/docs/generate", {
      method: "POST",
      body: JSON.stringify({
        repo_id: repoId,
        doc_type: docType,
        gemini_api_key: geminiApiKey,
      }),
    });
  }

  async listDocs(repoId: string): Promise<GeneratedDoc[]> {
    return this.request<GeneratedDoc[]>(`/docs/${repoId}`);
  }

  // Search Endpoint
  async searchRepo(repoId: string, query: string, searchType: string = "all"): Promise<SearchResultItem[]> {
    return this.request<SearchResultItem[]>("/search", {
      method: "POST",
      body: JSON.stringify({
        repo_id: repoId,
        query,
        search_type: searchType,
        limit: 30,
      }),
    });
  }
}

export const api = new ApiClient();
