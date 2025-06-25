import { useState, useRef, useEffect } from "react";
import { MessageBubble } from "./MessageBubble";
import { LoadingSpinner } from "./LoadingSpinner";
import { SessionSidebar } from "./SessionSidebar";
import { apiClient } from "../lib/api";
import { SessionStorage } from "../lib/storage";
import type {
  Message,
  ChatState,
  MessageResponse,
  SourceDocument,
} from "../lib/types";

export function ChatInterface() {
  const [chatState, setChatState] = useState<ChatState>({
    messages: [],
    isLoading: false,
    error: null,
    currentSessionId: null,
  });
  const [inputValue, setInputValue] = useState("");
  const [sidebarVisible, setSidebarVisible] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [chatState.messages]);

  useEffect(() => {
    const initializeSession = async () => {
      if (!SessionStorage.isStorageAvailable()) {
        console.warn("localStorage is not available");
        return;
      }

      const savedSessionId = SessionStorage.getCurrentSessionId();
      if (savedSessionId && savedSessionId !== chatState.currentSessionId) {
        try {
          await loadSessionMessages(savedSessionId);
        } catch (error) {
          console.warn("Failed to load saved session, starting fresh:", error);
          SessionStorage.clearCurrentSessionId();
        }
      }
    };

    initializeSession();
  }, []);

  useEffect(() => {
    if (chatState.currentSessionId && SessionStorage.isStorageAvailable()) {
      SessionStorage.saveCurrentSessionId(chatState.currentSessionId);
    }
  }, [chatState.currentSessionId]);

  const generateMessageId = () => Math.random().toString(36).substr(2, 9);

  const convertMessageResponseToMessage = (
    msgResponse: MessageResponse
  ): Message => ({
    id: msgResponse.id,
    type: msgResponse.role as "user" | "assistant",
    content: msgResponse.content,
    timestamp: new Date(msgResponse.created_at),
    sources: msgResponse.metadata?.sources as SourceDocument[] | undefined,
    confidence: msgResponse.metadata?.confidence as number | undefined,
  });

  const loadSessionMessages = async (sessionId: string) => {
    try {
      const messageResponses = await apiClient.getSessionMessages(sessionId);
      const messages = messageResponses.map(convertMessageResponseToMessage);

      setChatState((prev) => ({
        ...prev,
        messages,
        currentSessionId: sessionId,
        error: null,
      }));
    } catch (error) {
      setChatState((prev) => ({
        ...prev,
        error:
          error instanceof Error
            ? error.message
            : "メッセージの読み込みに失敗しました",
      }));
    }
  };

  const handleSessionSelect = async (sessionId: string) => {
    if (sessionId === chatState.currentSessionId) return;

    await loadSessionMessages(sessionId);
    setSidebarVisible(false);
  };

  const handleNewSession = () => {
    setChatState((prev) => ({
      ...prev,
      messages: [],
      currentSessionId: null,
      error: null,
    }));
    SessionStorage.clearCurrentSessionId();
    setSidebarVisible(false);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!inputValue.trim() || chatState.isLoading) return;

    const userMessage: Message = {
      id: generateMessageId(),
      type: "user",
      content: inputValue.trim(),
      timestamp: new Date(),
    };

    setChatState((prev) => ({
      ...prev,
      messages: [...prev.messages, userMessage],
      isLoading: true,
      error: null,
    }));

    setInputValue("");

    try {
      const response = await apiClient.chat({
        question: userMessage.content,
        max_results: 3,
        session_id: chatState.currentSessionId || undefined,
      });

      const assistantMessage: Message = {
        id: generateMessageId(),
        type: "assistant",
        content: response.answer,
        timestamp: new Date(),
        sources: response.sources,
        confidence: response.confidence,
      };

      setChatState((prev) => ({
        ...prev,
        messages: [...prev.messages, assistantMessage],
        isLoading: false,
        currentSessionId: response.session_id || prev.currentSessionId,
      }));
    } catch (error) {
      setChatState((prev) => ({
        ...prev,
        isLoading: false,
        error: error instanceof Error ? error.message : "エラーが発生しました",
      }));
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e as React.FormEvent);
    }
  };

  const clearError = () => {
    setChatState((prev) => ({ ...prev, error: null }));
  };

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Session Sidebar */}
      <SessionSidebar
        currentSessionId={chatState.currentSessionId}
        onSessionSelect={handleSessionSelect}
        onNewSession={handleNewSession}
        isVisible={sidebarVisible}
        onToggle={() => setSidebarVisible(!sidebarVisible)}
      />

      {/* Main Content */}
      <div className="flex flex-col flex-1 min-w-0">
        {/* Header */}
        <header className="bg-white border-b border-gray-200 px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button
                onClick={() => setSidebarVisible(!sidebarVisible)}
                className="p-2 rounded-lg hover:bg-gray-100 md:hidden"
              >
                ☰
              </button>
              <div>
                <h1 className="text-xl font-semibold text-gray-800">
                  🎮 ゲーム仕様問い合わせBOT
                </h1>
                <p className="text-sm text-gray-600 mt-1">
                  {chatState.currentSessionId
                    ? "継続会話中"
                    : "ゲーム仕様について何でもお聞きください"}
                </p>
              </div>
            </div>

            <button
              onClick={handleNewSession}
              className="hidden md:flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <span>+</span>
              新しい会話
            </button>
          </div>
        </header>

        {/* Messages */}
        <main className="flex-1 overflow-y-auto px-6 py-6">
          <div className="max-w-4xl mx-auto">
            {chatState.messages.length === 0 && (
              <div className="text-center py-12">
                <div className="text-6xl mb-4">🎮</div>
                <h2 className="text-xl font-medium text-gray-700 mb-2">
                  ゲーム仕様について質問してみましょう
                </h2>
                <p className="text-gray-500">
                  ゲームの機能、ルール、仕様について詳しく回答します
                </p>
              </div>
            )}

            {chatState.messages.map((message) => (
              <MessageBubble key={message.id} message={message} />
            ))}

            {chatState.isLoading && (
              <div className="flex justify-start mb-4">
                <div className="bg-white border border-gray-200 rounded-2xl px-4 py-3">
                  <div className="flex items-center gap-2">
                    <LoadingSpinner size="sm" />
                    <span className="text-gray-600">回答を生成中...</span>
                  </div>
                </div>
              </div>
            )}

            {chatState.error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-red-600">⚠️</span>
                    <span className="text-red-700">{chatState.error}</span>
                  </div>
                  <button
                    onClick={clearError}
                    className="text-red-600 hover:text-red-800 text-sm"
                  >
                    ✕
                  </button>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        </main>

        {/* Input */}
        <footer className="bg-white border-t border-gray-200 px-6 py-4">
          <div className="max-w-4xl mx-auto">
            <form onSubmit={handleSubmit} className="flex gap-3">
              <textarea
                ref={inputRef}
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="ゲーム仕様について質問してください..."
                className="flex-1 resize-none border border-gray-300 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                rows={1}
                disabled={chatState.isLoading}
              />
              <button
                type="submit"
                disabled={!inputValue.trim() || chatState.isLoading}
                className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {chatState.isLoading ? (
                  <LoadingSpinner size="sm" className="text-white" />
                ) : (
                  "送信"
                )}
              </button>
            </form>
            <p className="text-xs text-gray-500 mt-2 text-center">
              Enterで送信、Shift+Enterで改行
            </p>
          </div>
        </footer>
      </div>
    </div>
  );
}
