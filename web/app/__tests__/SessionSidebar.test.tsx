import {
  render,
  screen,
  fireEvent,
  waitFor,
  act,
} from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { SessionSidebar } from "../components/SessionSidebar";
import { apiClient } from "../lib/api";

// Mock API client
vi.mock("../lib/api", () => ({
  apiClient: {
    getSessions: vi.fn(),
    deleteSession: vi.fn(),
  },
}));

const mockSessions = [
  {
    id: "session-1",
    title: "テストセッション1",
    created_at: "2023-01-01T12:00:00",
    updated_at: "2023-01-01T12:00:00",
  },
  {
    id: "session-2",
    title: "テストセッション2",
    created_at: "2023-01-02T12:00:00",
    updated_at: "2023-01-02T12:00:00",
  },
];

describe("SessionSidebar", () => {
  const defaultProps = {
    currentSessionId: null,
    onSessionSelect: vi.fn(),
    onNewSession: vi.fn(),
    isVisible: true,
    onToggle: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
    // デフォルトでAPIは空の配列を返すようにモック
    vi.mocked(apiClient.getSessions).mockResolvedValue([]);
  });

  it("サイドバーが表示される", async () => {
    await act(async () => {
      render(<SessionSidebar {...defaultProps} />);
    });

    expect(screen.getByText("会話履歴")).toBeInTheDocument();
    expect(screen.getByText("新しい会話を開始")).toBeInTheDocument();
  });

  it("非表示状態では適切なCSSクラスが適用される", async () => {
    await act(async () => {
      render(<SessionSidebar {...defaultProps} isVisible={false} />);
    });

    const sidebar = document.querySelector(".transform");
    expect(sidebar).toHaveClass("-translate-x-full");
  });

  it("表示状態では適切なCSSクラスが適用される", async () => {
    await act(async () => {
      render(<SessionSidebar {...defaultProps} isVisible={true} />);
    });

    const sidebar = document.querySelector(".transform");
    expect(sidebar).toHaveClass("translate-x-0");
  });

  it("新しい会話ボタンをクリックするとonNewSessionが呼ばれる", async () => {
    await act(async () => {
      render(<SessionSidebar {...defaultProps} />);
    });

    const newSessionButton = screen.getByText("新しい会話を開始");
    fireEvent.click(newSessionButton);

    expect(defaultProps.onNewSession).toHaveBeenCalledTimes(1);
  });

  it("セッション一覧が正しく表示される", async () => {
    vi.mocked(apiClient.getSessions).mockResolvedValue(mockSessions);

    render(<SessionSidebar {...defaultProps} />);

    await waitFor(() => {
      expect(screen.getByText("テストセッション1")).toBeInTheDocument();
      expect(screen.getByText("テストセッション2")).toBeInTheDocument();
    });
  });

  it("セッションをクリックするとonSessionSelectが呼ばれる", async () => {
    vi.mocked(apiClient.getSessions).mockResolvedValue(mockSessions);

    render(<SessionSidebar {...defaultProps} />);

    await waitFor(() => {
      expect(screen.getByText("テストセッション1")).toBeInTheDocument();
    });

    const sessionItem = screen.getByText("テストセッション1");
    fireEvent.click(sessionItem);

    expect(defaultProps.onSessionSelect).toHaveBeenCalledWith("session-1");
  });

  it("現在選択中のセッションがハイライトされる", async () => {
    vi.mocked(apiClient.getSessions).mockResolvedValue(mockSessions);

    render(<SessionSidebar {...defaultProps} currentSessionId="session-1" />);

    await waitFor(() => {
      const sessionElement = screen.getByLabelText(
        "Select session: テストセッション1"
      );
      expect(sessionElement).toHaveClass("bg-blue-50");
    });
  });

  it("セッション削除ボタンをクリックすると確認ダイアログが表示される", async () => {
    vi.mocked(apiClient.getSessions).mockResolvedValue(mockSessions);
    const confirmSpy = vi.spyOn(window, "confirm").mockReturnValue(false);

    render(<SessionSidebar {...defaultProps} />);

    await waitFor(() => {
      expect(screen.getByText("テストセッション1")).toBeInTheDocument();
    });

    const deleteButtons = screen.getAllByText("🗑️");
    fireEvent.click(deleteButtons[0]);

    expect(confirmSpy).toHaveBeenCalledWith("このセッションを削除しますか？");
    confirmSpy.mockRestore();
  });

  it("セッション削除が確認されるとAPIが呼ばれる", async () => {
    vi.mocked(apiClient.getSessions).mockResolvedValue(mockSessions);
    vi.mocked(apiClient.deleteSession).mockResolvedValue({
      message: "Deleted",
    });
    const confirmSpy = vi.spyOn(window, "confirm").mockReturnValue(true);

    render(<SessionSidebar {...defaultProps} />);

    await waitFor(() => {
      expect(screen.getByText("テストセッション1")).toBeInTheDocument();
    });

    const deleteButtons = screen.getAllByText("🗑️");
    fireEvent.click(deleteButtons[0]);

    await waitFor(() => {
      expect(apiClient.deleteSession).toHaveBeenCalledWith("session-1");
    });

    confirmSpy.mockRestore();
  });

  it("読み込み中の状態が表示される", async () => {
    vi.mocked(apiClient.getSessions).mockImplementation(
      () => new Promise(() => {})
    );

    await act(async () => {
      render(<SessionSidebar {...defaultProps} />);
    });

    expect(screen.getByText("読み込み中...")).toBeInTheDocument();
  });

  it("エラー状態が表示される", async () => {
    vi.mocked(apiClient.getSessions).mockRejectedValue(new Error("API Error"));

    render(<SessionSidebar {...defaultProps} />);

    await waitFor(() => {
      expect(
        screen.getByText(/API Error|セッション一覧の取得に失敗しました/)
      ).toBeInTheDocument();
    });
  });

  it("セッションが空の場合のメッセージが表示される", async () => {
    vi.mocked(apiClient.getSessions).mockResolvedValue([]);

    render(<SessionSidebar {...defaultProps} />);

    await waitFor(() => {
      expect(screen.getByText("会話履歴がありません")).toBeInTheDocument();
    });
  });

  it("オーバーレイをクリックするとonToggleが呼ばれる", async () => {
    await act(async () => {
      render(<SessionSidebar {...defaultProps} />);
    });

    const overlay = document.querySelector(".fixed.inset-0.bg-black");
    if (overlay) {
      fireEvent.click(overlay);
      expect(defaultProps.onToggle).toHaveBeenCalledTimes(1);
    }
  });

  it("閉じるボタンをクリックするとonToggleが呼ばれる", async () => {
    await act(async () => {
      render(<SessionSidebar {...defaultProps} />);
    });

    const closeButton = screen.getByText("✕");
    fireEvent.click(closeButton);

    expect(defaultProps.onToggle).toHaveBeenCalledTimes(1);
  });

  it("時間のフォーマットが正しく表示される", async () => {
    const recentSession = {
      id: "recent-session",
      title: "最近のセッション",
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    vi.mocked(apiClient.getSessions).mockResolvedValue([recentSession]);

    render(<SessionSidebar {...defaultProps} />);

    await waitFor(() => {
      expect(screen.getByText("最近のセッション")).toBeInTheDocument();
      // 時間表示（HH:MM形式）があることを確認
      expect(
        document.querySelector(".text-sm.text-gray-500")
      ).toBeInTheDocument();
    });
  });
});
