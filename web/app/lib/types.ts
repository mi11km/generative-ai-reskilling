// API request/response types based on FastAPI backend schemas
export interface ChatRequest {
  question: string;
  max_results?: number;
  session_id?: string;
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
  session_id?: string;
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
  currentSessionId: string | null;
}

export interface ApiError {
  message: string;
  status?: number;
}

// Session management types
export interface SessionCreate {
  title?: string;
}

export interface SessionResponse {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface SessionUpdate {
  title: string;
}

export interface MessageResponse {
  id: string;
  session_id: string;
  role: string;
  content: string;
  created_at: string;
  metadata?: Record<string, unknown>;
}

export interface SessionState {
  sessions: SessionResponse[];
  currentSessionId: string | null;
  isLoading: boolean;
  error: string | null;
}