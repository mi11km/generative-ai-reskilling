import { render, screen } from "@testing-library/react";
import { MessageBubble } from "../components/MessageBubble";
import type { Message } from "../lib/types";

// SourceInfoコンポーネントをモック化
vi.mock("../components/SourceInfo", () => ({
  SourceInfo: ({
    sources,
    confidence,
  }: {
    sources: { length: number };
    confidence: number;
  }) => (
    <div data-testid="source-info">
      Sources: {sources.length}, Confidence: {confidence}
    </div>
  ),
}));

describe("MessageBubble", () => {
  const mockUserMessage: Message = {
    id: "1",
    type: "user",
    content: "こんにちは、テストメッセージです",
    timestamp: new Date("2023-01-01T12:00:00"),
  };

  const mockAssistantMessage: Message = {
    id: "2",
    type: "assistant",
    content: "こんにちは！お手伝いできることがありますか？",
    timestamp: new Date("2023-01-01T12:01:00"),
    sources: [
      {
        content: "テスト用のソース情報",
        section: "テストセクション",
      },
    ],
    confidence: 0.95,
  };

  it("ユーザーメッセージを正しく表示する", () => {
    render(<MessageBubble message={mockUserMessage} />);

    expect(
      screen.getByText("こんにちは、テストメッセージです")
    ).toBeInTheDocument();
    expect(screen.getByText("12:00")).toBeInTheDocument();
  });

  it("アシスタントメッセージを正しく表示する", () => {
    render(<MessageBubble message={mockAssistantMessage} />);

    expect(
      screen.getByText("こんにちは！お手伝いできることがありますか？")
    ).toBeInTheDocument();
    expect(screen.getByText("12:01")).toBeInTheDocument();
  });

  it("ユーザーメッセージには青い背景が適用される", () => {
    render(<MessageBubble message={mockUserMessage} />);

    const messageElement = screen.getByText(
      "こんにちは、テストメッセージです"
    ).parentElement;
    expect(messageElement).toHaveClass("bg-blue-600");
  });

  it("アシスタントメッセージには白い背景が適用される", () => {
    render(<MessageBubble message={mockAssistantMessage} />);

    const messageElement = screen.getByText(
      "こんにちは！お手伝いできることがありますか？"
    ).parentElement;
    expect(messageElement).toHaveClass("bg-white");
  });

  it("アシスタントメッセージのソース情報が含まれることを確認", () => {
    render(<MessageBubble message={mockAssistantMessage} />);

    expect(
      screen.getByText("こんにちは！お手伝いできることがありますか？")
    ).toBeInTheDocument();
    expect(screen.getByTestId("source-info")).toBeInTheDocument();
    expect(
      screen.getByText("Sources: 1, Confidence: 0.95")
    ).toBeInTheDocument();
  });

  it("ユーザーメッセージにはソース情報が表示されない", () => {
    render(<MessageBubble message={mockUserMessage} />);

    expect(screen.queryByTestId("source-info")).not.toBeInTheDocument();
  });
});
