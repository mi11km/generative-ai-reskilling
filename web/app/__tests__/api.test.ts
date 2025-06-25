import { describe, it, expect, beforeEach, vi } from 'vitest';
import { ApiClient } from '../lib/api';
import type { 
  ChatRequest, 
  ChatResponse, 
  HealthResponse, 
  SessionCreate,
  SessionResponse,
  SessionUpdate,
  MessageResponse
} from '../lib/types';

// fetchをモック化
const mockFetch = vi.fn();
global.fetch = mockFetch;

describe('ApiClient', () => {
  let apiClient: ApiClient;

  beforeEach(() => {
    apiClient = new ApiClient();
    mockFetch.mockClear();
  });

  describe('healthCheck', () => {
    it('ヘルスチェックが正常に動作する', async () => {
      const mockResponse: HealthResponse = {
        status: 'healthy',
        version: '1.0.0',
        vector_store_ready: true,
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await apiClient.healthCheck();

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/health',
        {
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );
      expect(result).toEqual(mockResponse);
    });
  });

  describe('chat', () => {
    it('チャットリクエストが正常に動作する', async () => {
      const request: ChatRequest = {
        question: 'テスト質問',
        max_results: 3,
      };

      const mockResponse = {
        answer: 'テスト回答',
        sources: [],
        confidence: 0.95,
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await apiClient.chat(request);

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/chat',
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(request),
        }
      );
      expect(result).toEqual(mockResponse);
    });
  });

  describe('createSession', () => {
    it('セッション作成が正常に動作する', async () => {
      const request: SessionCreate = {
        title: 'テストセッション',
      };

      const mockResponse = {
        id: 'session-123',
        title: 'テストセッション',
        created_at: '2023-01-01T12:00:00Z',
        updated_at: '2023-01-01T12:00:00Z',
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await apiClient.createSession(request);

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/sessions',
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(request),
        }
      );
      expect(result).toEqual(mockResponse);
    });
  });

  describe('getSessions', () => {
    it('セッション一覧取得が正常に動作する', async () => {
      const mockResponse = [
        {
          id: 'session-1',
          title: 'セッション1',
          created_at: '2023-01-01T12:00:00Z',
          updated_at: '2023-01-01T12:00:00Z',
        },
        {
          id: 'session-2',
          title: 'セッション2',
          created_at: '2023-01-01T13:00:00Z',
          updated_at: '2023-01-01T13:00:00Z',
        },
      ];

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await apiClient.getSessions();

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/sessions',
        {
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );
      expect(result).toEqual(mockResponse);
    });
  });

  describe('getSession', () => {
    it('セッション詳細取得が正常に動作する', async () => {
      const sessionId = 'test-session-id';
      const mockResponse: SessionResponse = {
        id: sessionId,
        title: 'テストセッション',
        created_at: '2023-01-01T12:00:00Z',
        updated_at: '2023-01-01T12:00:00Z',
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await apiClient.getSession(sessionId);

      expect(mockFetch).toHaveBeenCalledWith(
        `http://localhost:8000/api/v1/sessions/${sessionId}`,
        {
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );
      expect(result).toEqual(mockResponse);
    });
  });

  describe('updateSession', () => {
    it('セッション更新が正常に動作する', async () => {
      const sessionId = 'test-session-id';
      const request: SessionUpdate = { title: '更新されたタイトル' };
      const mockResponse: SessionResponse = {
        id: sessionId,
        title: '更新されたタイトル',
        created_at: '2023-01-01T12:00:00Z',
        updated_at: '2023-01-01T12:30:00Z',
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await apiClient.updateSession(sessionId, request);

      expect(mockFetch).toHaveBeenCalledWith(
        `http://localhost:8000/api/v1/sessions/${sessionId}`,
        {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(request),
        }
      );
      expect(result).toEqual(mockResponse);
    });
  });

  describe('deleteSession', () => {
    it('セッション削除が正常に動作する', async () => {
      const sessionId = 'test-session-id';
      const mockResponse = { message: 'セッションが削除されました' };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await apiClient.deleteSession(sessionId);

      expect(mockFetch).toHaveBeenCalledWith(
        `http://localhost:8000/api/v1/sessions/${sessionId}`,
        {
          method: 'DELETE',
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );
      expect(result).toEqual(mockResponse);
    });
  });

  describe('getSessionMessages', () => {
    it('セッションメッセージ取得が正常に動作する', async () => {
      const sessionId = 'test-session-id';
      const mockResponse: MessageResponse[] = [
        {
          id: 'message-1',
          session_id: sessionId,
          role: 'user',
          content: 'こんにちは',
          created_at: '2023-01-01T12:00:00Z',
          metadata: {},
        },
        {
          id: 'message-2',
          session_id: sessionId,
          role: 'assistant',
          content: 'こんにちは！何かご質問はありますか？',
          created_at: '2023-01-01T12:01:00Z',
          metadata: { confidence: 0.95 },
        },
      ];

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await apiClient.getSessionMessages(sessionId);

      expect(mockFetch).toHaveBeenCalledWith(
        `http://localhost:8000/api/v1/sessions/${sessionId}/messages`,
        {
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );
      expect(result).toEqual(mockResponse);
    });
  });

  describe('chat with session_id', () => {
    it('session_idを含むチャットリクエストが正常に動作する', async () => {
      const request: ChatRequest = {
        question: 'セッション内での質問',
        max_results: 3,
        session_id: 'test-session-123',
      };

      const mockResponse: ChatResponse = {
        answer: 'セッション内での回答',
        sources: [],
        confidence: 0.8,
        session_id: 'test-session-123',
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await apiClient.chat(request);

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/chat',
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(request),
        }
      );
      expect(result).toEqual(mockResponse);
    });
  });

  describe('エラーハンドリング', () => {
    it('HTTPエラーを適切に処理する', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        json: async () => ({ detail: 'Not Found' }),
      });

      await expect(apiClient.healthCheck()).rejects.toThrow('Not Found');
    });

    it('ネットワークエラーを適切に処理する', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      await expect(apiClient.healthCheck()).rejects.toThrow('Network error');
    });

    it('不明なエラーを適切に処理する', async () => {
      mockFetch.mockRejectedValueOnce('Unknown error');

      await expect(apiClient.healthCheck()).rejects.toThrow('ネットワークエラーが発生しました');
    });
  });
});