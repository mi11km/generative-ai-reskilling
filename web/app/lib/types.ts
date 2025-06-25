// API request/response types based on FastAPI backend schemas
export interface ChatRequest {
  question: string;
  max_results?: number;
}

export interface SourceDocument {
  content: string;
  section: string;
  metadata?: Record<string, unknown>;
}

export interface ChatResponse {
  answer: string;
  sources: SourceDocument[];
  confidence: number;
}

export interface HealthResponse {
  status: string;
  version: string;
  vector_store_ready: boolean;
}

// Frontend-specific types
export interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  sources?: SourceDocument[];
  confidence?: number;
}

export interface ChatState {
  messages: Message[];
  isLoading: boolean;
  error: string | null;
}

export interface ApiError {
  message: string;
  status?: number;
}