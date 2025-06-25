import { useState, useEffect, useCallback } from "react";
import { apiClient } from "../lib/api";
import type { SessionState } from "../lib/types";

interface SessionSidebarProps {
  currentSessionId: string | null;
  onSessionSelect: (sessionId: string) => void;
  onNewSession: () => void;
  isVisible: boolean;
  onToggle: () => void;
}

export function SessionSidebar({
  currentSessionId,
  onSessionSelect,
  onNewSession,
  isVisible,
  onToggle,
}: SessionSidebarProps) {
  const [sessionState, setSessionState] = useState<SessionState>({
    sessions: [],
    currentSessionId: null,
    isLoading: false,
    error: null,
  });

  const loadSessions = useCallback(async () => {
    setSessionState((prev) => ({ ...prev, isLoading: true, error: null }));
    try {
      const sessions = await apiClient.getSessions();
      setSessionState((prev) => ({
        ...prev,
        sessions,
        isLoading: false,
      }));
    } catch (error) {
      setSessionState((prev) => ({
        ...prev,
        isLoading: false,
        error:
          error instanceof Error
            ? error.message
            : "セッション一覧の取得に失敗しました",
      }));
    }
  }, []);

  const handleDeleteSession = async (
    sessionId: string,
    e: React.MouseEvent
  ) => {
    e.stopPropagation();
    if (!confirm("このセッションを削除しますか？")) return;

    try {
      await apiClient.deleteSession(sessionId);
      await loadSessions();

      // 削除されたセッションが現在選択中の場合は、新しいセッションを開始
      if (currentSessionId === sessionId) {
        onNewSession();
      }
    } catch (error) {
      console.error("セッション削除エラー:", error);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60);

    if (diffInHours < 24) {
      return date.toLocaleTimeString("ja-JP", {
        hour: "2-digit",
        minute: "2-digit",
      });
    }
    return date.toLocaleDateString("ja-JP", {
      month: "short",
      day: "numeric",
    });
  };

  useEffect(() => {
    if (isVisible) {
      loadSessions();
    }
  }, [isVisible, loadSessions]);

  return (
    <>
      {/* オーバーレイ */}
      {isVisible && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-40 md:hidden"
          onClick={onToggle}
          onKeyDown={(e) => e.key === "Escape" && onToggle()}
          role="button"
          tabIndex={0}
          aria-label="Close sidebar"
        />
      )}

      {/* サイドバー */}
      <div
        className={`
        fixed top-0 left-0 h-full w-80 bg-white border-r border-gray-200 z-50
        transform transition-transform duration-300 ease-in-out
        ${isVisible ? "translate-x-0" : "-translate-x-full"}
        md:relative md:translate-x-0 md:z-auto
      `}
      >
        {/* ヘッダー */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-800">会話履歴</h2>
          <button
            type="button"
            onClick={onToggle}
            className="p-2 rounded-lg hover:bg-gray-100 md:hidden"
          >
            ✕
          </button>
        </div>

        {/* 新規セッションボタン */}
        <div className="p-4 border-b border-gray-200">
          <button
            type="button"
            onClick={onNewSession}
            className="w-full flex items-center gap-2 px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <span className="text-lg">+</span>
            新しい会話を開始
          </button>
        </div>

        {/* セッション一覧 */}
        <div className="flex-1 overflow-y-auto">
          {sessionState.isLoading && (
            <div className="p-4 text-center text-gray-500">読み込み中...</div>
          )}

          {sessionState.error && (
            <div className="p-4 text-center text-red-600">
              {sessionState.error}
            </div>
          )}

          {!sessionState.isLoading &&
            !sessionState.error &&
            sessionState.sessions &&
            sessionState.sessions.length === 0 && (
              <output className="p-4 text-center text-gray-500">
                会話履歴がありません
              </output>
            )}

          {sessionState.sessions?.map((session) => (
            <div
              key={session.id}
              className={`
                flex items-center justify-between p-4 border-b border-gray-100 hover:bg-gray-50
                ${currentSessionId === session.id ? "bg-blue-50 border-blue-200" : ""}
              `}
            >
              <button
                type="button"
                onClick={() => onSessionSelect(session.id)}
                aria-label={`Select session: ${session.title}`}
                className="flex-1 min-w-0 text-left"
              >
                <h3
                  className={`
                  font-medium truncate
                  ${currentSessionId === session.id ? "text-blue-700" : "text-gray-800"}
                `}
                >
                  {session.title}
                </h3>
                <p className="text-sm text-gray-500 mt-1">
                  {formatDate(session.updated_at)}
                </p>
              </button>

              <button
                type="button"
                onClick={(e) => handleDeleteSession(session.id, e)}
                className="p-1 text-gray-400 hover:text-red-600 rounded"
                title="削除"
              >
                🗑️
              </button>
            </div>
          )) || null}
        </div>
      </div>
    </>
  );
}
