import type {
  ChatRequest,
  ChatResponse,
  HealthResponse,
  ApiError,
  SessionCreate,
  SessionResponse,
  SessionUpdate,
  MessageResponse,
} from "./types";

const API_BASE_URL = "http://localhost:8000";

class ApiClient {
  private async request<T>(
    endpoint: string,
    options?: RequestInit
  ): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;

    try {
      const response = await fetch(url, {
        headers: {
          "Content-Type": "application/json",
          ...options?.headers,
        },
        ...options,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
          errorData.detail || `HTTP error! status: ${response.status}`
        );
      }

      return await response.json();
    } catch (error) {
      if (error instanceof Error) {
        throw error;
      }
      throw new Error("ネットワークエラーが発生しました");
    }
  }

  async chat(request: ChatRequest): Promise<ChatResponse> {
    return this.request<ChatResponse>("/api/v1/chat", {
      method: "POST",
      body: JSON.stringify(request),
    });
  }

  async healthCheck(): Promise<HealthResponse> {
    return this.request<HealthResponse>("/api/v1/health");
  }

  // Session management methods
  async createSession(request: SessionCreate): Promise<SessionResponse> {
    return this.request<SessionResponse>("/api/v1/sessions", {
      method: "POST",
      body: JSON.stringify(request),
    });
  }

  async getSessions(): Promise<SessionResponse[]> {
    return this.request<SessionResponse[]>("/api/v1/sessions");
  }

  async getSession(sessionId: string): Promise<SessionResponse> {
    return this.request<SessionResponse>(`/api/v1/sessions/${sessionId}`);
  }

  async updateSession(
    sessionId: string,
    request: SessionUpdate
  ): Promise<SessionResponse> {
    return this.request<SessionResponse>(`/api/v1/sessions/${sessionId}`, {
      method: "PUT",
      body: JSON.stringify(request),
    });
  }

  async deleteSession(sessionId: string): Promise<{ message: string }> {
    return this.request<{ message: string }>(`/api/v1/sessions/${sessionId}`, {
      method: "DELETE",
    });
  }

  async getSessionMessages(sessionId: string): Promise<MessageResponse[]> {
    return this.request<MessageResponse[]>(
      `/api/v1/sessions/${sessionId}/messages`
    );
  }
}

export const apiClient = new ApiClient();

export { ApiClient };
export type { ApiError };
