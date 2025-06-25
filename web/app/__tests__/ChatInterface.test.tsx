import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ChatInterface } from "../components/ChatInterface";
import { apiClient } from "../lib/api";

// APIクライアントをモック化
vi.mock("../lib/api", () => ({
  apiClient: {
    chat: vi.fn(),
    getSessionMessages: vi.fn(),
  },
}));

// SessionSidebarコンポーネントをモック化
vi.mock("../components/SessionSidebar", () => ({
  SessionSidebar: ({ onToggle }: { onToggle: () => void }) => (
    <div data-testid="session-sidebar">
      <button type="button" onClick={onToggle}>
        Toggle Sidebar
      </button>
    </div>
  ),
}));

describe("ChatInterface", () => {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const mockApiClient = apiClient as any;

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("初期状態で正しく表示される", () => {
    render(<ChatInterface />);

    expect(screen.getByText("🎮 ゲーム仕様問い合わせBOT")).toBeInTheDocument();
    expect(
      screen.getByText("ゲーム仕様について何でもお聞きください")
    ).toBeInTheDocument();
    expect(
      screen.getByText("ゲーム仕様について質問してみましょう")
    ).toBeInTheDocument();
    expect(
      screen.getByPlaceholderText("ゲーム仕様について質問してください...")
    ).toBeInTheDocument();
  });

  it("メッセージを送信できる", async () => {
    const user = userEvent.setup();
    const mockResponse = {
      answer: "テスト回答",
      sources: [],
      confidence: 0.95,
      session_id: "session-123",
    };

    mockApiClient.chat.mockResolvedValueOnce(mockResponse);

    render(<ChatInterface />);

    const input = screen.getByPlaceholderText(
      "ゲーム仕様について質問してください..."
    );
    const submitButton = screen.getByText("送信");

    await user.type(input, "テスト質問");
    await user.click(submitButton);

    expect(mockApiClient.chat).toHaveBeenCalledWith({
      question: "テスト質問",
      max_results: 3,
      session_id: undefined,
    });

    await waitFor(() => {
      expect(screen.getByText("テスト質問")).toBeInTheDocument();
      expect(screen.getByText("テスト回答")).toBeInTheDocument();
    });
  });

  it("Enterキーでメッセージを送信できる", async () => {
    const user = userEvent.setup();
    const mockResponse = {
      answer: "テスト回答",
      sources: [],
      confidence: 0.95,
      session_id: "session-123",
    };

    mockApiClient.chat.mockResolvedValueOnce(mockResponse);

    render(<ChatInterface />);

    const input = screen.getByPlaceholderText(
      "ゲーム仕様について質問してください..."
    );

    await user.type(input, "テスト質問{Enter}");

    expect(mockApiClient.chat).toHaveBeenCalledWith({
      question: "テスト質問",
      max_results: 3,
      session_id: undefined,
    });
  });

  it("Shift+Enterで改行できる", async () => {
    const user = userEvent.setup();

    render(<ChatInterface />);

    const input = screen.getByPlaceholderText(
      "ゲーム仕様について質問してください..."
    );

    await user.type(input, "テスト{Shift>}{Enter}{/Shift}質問");

    expect(input).toHaveValue("テスト\n質問");
    expect(mockApiClient.chat).not.toHaveBeenCalled();
  });

  it("空のメッセージは送信できない", async () => {
    const user = userEvent.setup();

    render(<ChatInterface />);

    const submitButton = screen.getByText("送信");

    expect(submitButton).toBeDisabled();

    const input = screen.getByPlaceholderText(
      "ゲーム仕様について質問してください..."
    );
    await user.type(input, "   "); // スペースのみ

    expect(submitButton).toBeDisabled();
  });

  it("ローディング中は送信ボタンが無効になる", async () => {
    const user = userEvent.setup();

    // 長時間かかるPromiseを作成
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    let resolvePromise: (value: any) => void;
    const longRunningPromise = new Promise((resolve) => {
      resolvePromise = resolve;
    });

    mockApiClient.chat.mockReturnValueOnce(longRunningPromise);

    render(<ChatInterface />);

    const input = screen.getByPlaceholderText(
      "ゲーム仕様について質問してください..."
    );
    const submitButton = screen.getByText("送信");

    await user.type(input, "テスト質問");
    await user.click(submitButton);

    // ローディング中の状態を確認
    expect(screen.getByText("回答を生成中...")).toBeInTheDocument();

    // 入力フィールドとボタンが無効になっていることを確認
    expect(input).toBeDisabled();

    // ローディング中は送信ボタンがLoadingSpinnerになる
    const buttons = screen.getAllByRole("button");
    const submitBtn = buttons.find(
      (button) => button.getAttribute("type") === "submit"
    );
    expect(submitBtn).toBeDisabled();

    // Promiseを解決
    resolvePromise?.({
      answer: "テスト回答",
      sources: [],
      confidence: 0.95,
      session_id: "session-123",
    });

    await waitFor(() => {
      expect(screen.queryByText("回答を生成中...")).not.toBeInTheDocument();
      expect(input).not.toBeDisabled();
    });
  });

  it("APIエラーを適切に表示する", async () => {
    const user = userEvent.setup();

    mockApiClient.chat.mockRejectedValueOnce(
      new Error("APIエラーが発生しました")
    );

    render(<ChatInterface />);

    const input = screen.getByPlaceholderText(
      "ゲーム仕様について質問してください..."
    );
    const submitButton = screen.getByText("送信");

    await user.type(input, "テスト質問");
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText("APIエラーが発生しました")).toBeInTheDocument();
    });

    // エラーを消去できることを確認
    const closeButton = screen.getByText("✕");
    await user.click(closeButton);

    await waitFor(() => {
      expect(
        screen.queryByText("APIエラーが発生しました")
      ).not.toBeInTheDocument();
    });
  });

  it("新しい会話ボタンが動作する", async () => {
    const user = userEvent.setup();

    render(<ChatInterface />);

    // 最初にメッセージを送信してセッションを作成
    const mockResponse = {
      answer: "テスト回答",
      sources: [],
      confidence: 0.95,
      session_id: "session-123",
    };

    mockApiClient.chat.mockResolvedValueOnce(mockResponse);

    const input = screen.getByPlaceholderText(
      "ゲーム仕様について質問してください..."
    );
    await user.type(input, "テスト質問");
    await user.click(screen.getByText("送信"));

    await waitFor(() => {
      expect(screen.getByText("継続会話中")).toBeInTheDocument();
    });

    // 新しい会話ボタンをクリック
    const newSessionButton = screen.getByText("新しい会話");
    await user.click(newSessionButton);

    // 状態がリセットされることを確認
    expect(
      screen.getByText("ゲーム仕様について何でもお聞きください")
    ).toBeInTheDocument();
    expect(screen.queryByText("テスト質問")).not.toBeInTheDocument();
    expect(screen.queryByText("テスト回答")).not.toBeInTheDocument();
  });
});
