import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI

from src.api.chat import router, get_rag_service, RAGServiceContainer
from src.models.schemas import ChatResponse, SourceDocument
from src.config.settings import Settings


@pytest.fixture
def app():
    """テスト用のFastAPIアプリケーション"""
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def client(app):
    """テスト用のHTTPクライアント"""
    return TestClient(app)


@pytest.fixture
def mock_settings():
    """テスト用のSettings"""
    return Settings(openai_api_key="test_api_key", version="0.1.0", debug=True)


@pytest.fixture
def mock_rag_service():
    """テスト用のRAGサービス"""
    mock_service = Mock()
    mock_service.is_ready.return_value = True
    return mock_service


class TestChatAPI:
    """チャットAPIのテスト"""

    def test_chat_endpoint_successful(self, client):
        """正常なチャットリクエストをテスト"""
        from src.api.chat import get_rag_service

        # RAGサービスのモック
        mock_rag_service = Mock()

        # チャットレスポンスのモック
        mock_response = ChatResponse(
            answer="テストの回答です。",
            sources=[
                SourceDocument(
                    content="テストソース内容",
                    section="テストセクション",
                    metadata={"score": 0.8},
                )
            ],
            confidence=0.85,
        )
        mock_rag_service.chat.return_value = mock_response

        # 依存性をオーバーライド
        app = client.app
        app.dependency_overrides[get_rag_service] = lambda: mock_rag_service

        try:
            # リクエスト実行
            response = client.post(
                "/api/v1/chat", json={"question": "テストの質問です", "max_results": 3}
            )

            # ステータスコードの確認
            assert response.status_code == 200

            # レスポンス内容の確認
            data = response.json()
            assert data["answer"] == "テストの回答です。"
            assert len(data["sources"]) == 1
            assert data["sources"][0]["content"] == "テストソース内容"
            assert data["sources"][0]["section"] == "テストセクション"
            assert data["confidence"] == 0.85

            # RAGサービスが正しく呼ばれたことを確認
            mock_rag_service.chat.assert_called_once_with(
                question="テストの質問です", max_results=3, session_id=None
            )
        finally:
            # オーバーライドをクリア
            app.dependency_overrides.clear()

    def test_chat_endpoint_default_max_results(self, client):
        """デフォルトのmax_resultsでのチャットリクエストをテスト"""
        from src.api.chat import get_rag_service

        mock_rag_service = Mock()
        mock_response = ChatResponse(answer="回答", sources=[], confidence=0.5)
        mock_rag_service.chat.return_value = mock_response

        # 依存性をオーバーライド
        app = client.app
        app.dependency_overrides[get_rag_service] = lambda: mock_rag_service

        try:
            # max_resultsを指定しないリクエスト
            response = client.post("/api/v1/chat", json={"question": "質問"})

            assert response.status_code == 200

            # デフォルト値（3）で呼ばれることを確認
            mock_rag_service.chat.assert_called_once_with(
                question="質問", max_results=3, session_id=None
            )
        finally:
            app.dependency_overrides.clear()

    def test_chat_endpoint_custom_max_results(self, client):
        """カスタムmax_resultsでのチャットリクエストをテスト"""
        from src.api.chat import get_rag_service

        mock_rag_service = Mock()
        mock_response = ChatResponse(answer="回答", sources=[], confidence=0.5)
        mock_rag_service.chat.return_value = mock_response

        # 依存性をオーバーライド
        app = client.app
        app.dependency_overrides[get_rag_service] = lambda: mock_rag_service

        try:
            # カスタムmax_resultsでのリクエスト
            response = client.post(
                "/api/v1/chat", json={"question": "質問", "max_results": 7}
            )

            assert response.status_code == 200

            # カスタム値で呼ばれることを確認
            mock_rag_service.chat.assert_called_once_with(
                question="質問", max_results=7, session_id=None
            )
        finally:
            app.dependency_overrides.clear()

    def test_chat_endpoint_invalid_max_results(self, client):
        """無効なmax_resultsでのバリデーションエラーをテスト"""
        # max_resultsが範囲外（0以下）
        response = client.post(
            "/api/v1/chat", json={"question": "質問", "max_results": 0}
        )
        assert response.status_code == 422  # Validation Error

        # max_resultsが範囲外（10より大きい）
        response = client.post(
            "/api/v1/chat", json={"question": "質問", "max_results": 11}
        )
        assert response.status_code == 422  # Validation Error

    def test_chat_endpoint_missing_question(self, client):
        """質問が欠如している場合のバリデーションエラーをテスト"""
        response = client.post("/api/v1/chat", json={"max_results": 3})
        assert response.status_code == 422  # Validation Error

    def test_chat_endpoint_empty_question(self, client):
        """空の質問でのバリデーションエラーをテスト"""
        response = client.post("/api/v1/chat", json={"question": "", "max_results": 3})
        assert response.status_code == 422  # Validation Error

    def test_chat_endpoint_internal_error(self, client):
        """内部エラーの処理をテスト"""
        from src.api.chat import get_rag_service

        mock_rag_service = Mock()
        # RAGサービスで例外が発生
        mock_rag_service.chat.side_effect = Exception("テストエラー")

        # 依存性をオーバーライド
        app = client.app
        app.dependency_overrides[get_rag_service] = lambda: mock_rag_service

        try:
            response = client.post("/api/v1/chat", json={"question": "テスト質問"})

            # HTTPException (500) が発生することを確認
            assert response.status_code == 500
            assert "内部サーバーエラーが発生しました" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()

    def test_chat_endpoint_japanese_question(self, client):
        """日本語の質問での処理をテスト"""
        from src.api.chat import get_rag_service

        mock_rag_service = Mock()
        mock_response = ChatResponse(
            answer="日本語での回答です。", sources=[], confidence=0.7
        )
        mock_rag_service.chat.return_value = mock_response

        # 依存性をオーバーライド
        app = client.app
        app.dependency_overrides[get_rag_service] = lambda: mock_rag_service

        try:
            japanese_question = "ゲームの基本システムについて教えてください。"
            response = client.post("/api/v1/chat", json={"question": japanese_question})

            assert response.status_code == 200
            data = response.json()
            assert data["answer"] == "日本語での回答です。"

            # 日本語の質問が正しく渡されることを確認
            mock_rag_service.chat.assert_called_once_with(
                question=japanese_question, max_results=3, session_id=None
            )
        finally:
            app.dependency_overrides.clear()

    def test_chat_endpoint_long_question(self, client):
        """長い質問での処理をテスト"""
        from src.api.chat import get_rag_service

        mock_rag_service = Mock()
        mock_response = ChatResponse(
            answer="長い質問への回答", sources=[], confidence=0.6
        )
        mock_rag_service.chat.return_value = mock_response

        # 依存性をオーバーライド
        app = client.app
        app.dependency_overrides[get_rag_service] = lambda: mock_rag_service

        try:
            # 長い質問（1000文字）
            long_question = "テスト質問です。" * 100
            response = client.post("/api/v1/chat", json={"question": long_question})

            assert response.status_code == 200

            # 長い質問も正しく処理されることを確認
            mock_rag_service.chat.assert_called_once_with(
                question=long_question, max_results=3, session_id=None
            )
        finally:
            app.dependency_overrides.clear()


class TestHealthAPI:
    """ヘルスチェックAPIのテスト"""

    def test_health_endpoint_healthy(self, client):
        """正常な状態でのヘルスチェックをテスト"""
        from src.api.chat import get_rag_service, get_settings

        # 設定のモック
        mock_settings = Mock()
        mock_settings.version = "0.1.0"

        # RAGサービスのモック
        mock_rag_service = Mock()
        mock_rag_service.is_ready.return_value = True

        # 依存性をオーバーライド
        app = client.app
        app.dependency_overrides[get_settings] = lambda: mock_settings
        app.dependency_overrides[get_rag_service] = lambda: mock_rag_service

        try:
            response = client.get("/api/v1/health")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["version"] == "0.1.0"
            assert data["vector_store_ready"] is True
        finally:
            app.dependency_overrides.clear()

    def test_health_endpoint_vector_store_not_ready(self, client):
        """ベクトルストアが準備できていない状態でのヘルスチェックをテスト"""
        from src.api.chat import get_rag_service, get_settings

        mock_settings = Mock()
        mock_settings.version = "0.1.0"

        mock_rag_service = Mock()
        mock_rag_service.is_ready.return_value = False

        # 依存性をオーバーライド
        app = client.app
        app.dependency_overrides[get_settings] = lambda: mock_settings
        app.dependency_overrides[get_rag_service] = lambda: mock_rag_service

        try:
            response = client.get("/api/v1/health")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"  # ステータス自体は healthy
            assert data["vector_store_ready"] is False
        finally:
            app.dependency_overrides.clear()


class TestRAGServiceContainer:
    """RAGServiceContainer クラスのテスト"""

    def test_singleton_behavior(self):
        """シングルトン動作をテスト"""
        container1 = RAGServiceContainer()
        container2 = RAGServiceContainer()

        # 同じインスタンスが返されることを確認
        assert container1 is container2

    @patch("src.api.chat.RAGService")
    def test_get_or_create_rag_service_first_call(
        self, mock_rag_service_class, mock_settings
    ):
        """初回呼び出しでRAGServiceが作成されることをテスト"""
        # コンテナをリセット
        container = RAGServiceContainer()
        container.reset()

        mock_rag_instance = Mock()
        mock_rag_service_class.return_value = mock_rag_instance

        result = container.get_or_create_rag_service(mock_settings)

        # RAGServiceが設定で初期化されることを確認
        mock_rag_service_class.assert_called_once_with(mock_settings)
        assert result == mock_rag_instance

    @patch("src.api.chat.RAGService")
    def test_get_or_create_rag_service_cached_behavior(
        self, mock_rag_service_class, mock_settings
    ):
        """キャッシュ動作をテスト"""
        # コンテナをリセット
        container = RAGServiceContainer()
        container.reset()

        mock_rag_instance = Mock()
        mock_rag_service_class.return_value = mock_rag_instance

        # 最初の呼び出し
        result1 = container.get_or_create_rag_service(mock_settings)

        # 2回目の呼び出し
        result2 = container.get_or_create_rag_service(mock_settings)

        # RAGServiceは1回だけ作成されることを確認
        mock_rag_service_class.assert_called_once_with(mock_settings)

        # 同じインスタンスが返されることを確認
        assert result1 is result2
        assert result1 == mock_rag_instance

    def test_reset(self, mock_settings):
        """リセット機能をテスト"""
        container = RAGServiceContainer()

        # RAGServiceのモックを設定
        mock_rag_service = Mock()
        container._rag_service = mock_rag_service

        # リセット前は設定されている
        assert container._rag_service == mock_rag_service

        # リセット実行
        container.reset()

        # リセット後はNoneになる
        assert container._rag_service is None


class TestGetRAGService:
    """get_rag_service 依存性注入のテスト"""

    @patch("src.api.chat.RAGServiceContainer")
    def test_get_rag_service_calls_container(self, mock_container_class, mock_settings):
        """get_rag_serviceがコンテナを使用することをテスト"""
        mock_container_instance = Mock()
        mock_container_class.return_value = mock_container_instance

        mock_rag_service = Mock()
        mock_container_instance.get_or_create_rag_service.return_value = (
            mock_rag_service
        )

        result = get_rag_service(mock_settings, mock_container_instance)

        # コンテナのメソッドが正しい引数で呼ばれることを確認
        mock_container_instance.get_or_create_rag_service.assert_called_once_with(
            mock_settings
        )
        assert result == mock_rag_service


@pytest.mark.parametrize(
    "question,max_results",
    [
        ("短い質問", 1),
        ("中くらいの長さの質問です。", 3),
        ("とても長い質問になります。" * 10, 5),
        ("日本語での質問：ゲームシステムについて", 7),
        ("English question about game mechanics", 10),
    ],
)
def test_chat_endpoint_various_inputs(question, max_results, client):
    """様々な入力でのチャットエンドポイントをパラメータ化テストで検証"""
    from src.api.chat import get_rag_service

    mock_rag_service = Mock()
    mock_response = ChatResponse(
        answer=f"回答: {question[:20]}...", sources=[], confidence=0.5
    )
    mock_rag_service.chat.return_value = mock_response

    # 依存性をオーバーライド
    app = client.app
    app.dependency_overrides[get_rag_service] = lambda: mock_rag_service

    try:
        response = client.post(
            "/api/v1/chat", json={"question": question, "max_results": max_results}
        )

        assert response.status_code == 200
        mock_rag_service.chat.assert_called_once_with(
            question=question, max_results=max_results, session_id=None
        )
    finally:
        app.dependency_overrides.clear()


@pytest.mark.parametrize("invalid_max_results", [-1, 0, 11, 100, -5])
def test_chat_endpoint_invalid_max_results_parametrized(invalid_max_results, client):
    """無効なmax_results値をパラメータ化テストで検証"""
    response = client.post(
        "/api/v1/chat",
        json={"question": "テスト質問", "max_results": invalid_max_results},
    )

    assert response.status_code == 422  # Validation Error


class TestChatWithSession:
    """セッション機能を含むチャットAPIのテスト"""

    def test_chat_endpoint_with_session_id(self, client):
        """session_idを含むチャットリクエストをテスト"""
        from src.api.chat import get_rag_service

        mock_rag_service = Mock()
        mock_response = ChatResponse(
            answer="セッション内での回答",
            sources=[],
            confidence=0.8,
            session_id="test-session-123",
        )
        mock_rag_service.chat.return_value = mock_response

        # 依存性をオーバーライド
        app = client.app
        app.dependency_overrides[get_rag_service] = lambda: mock_rag_service

        try:
            response = client.post(
                "/api/v1/chat",
                json={
                    "question": "前回の質問に続いて...",
                    "max_results": 3,
                    "session_id": "test-session-123",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["answer"] == "セッション内での回答"
            assert data["session_id"] == "test-session-123"

            # session_idが正しく渡されることを確認
            mock_rag_service.chat.assert_called_once_with(
                question="前回の質問に続いて...",
                max_results=3,
                session_id="test-session-123",
            )
        finally:
            app.dependency_overrides.clear()

    def test_chat_endpoint_session_id_none(self, client):
        """session_idがNoneの場合のテスト"""
        from src.api.chat import get_rag_service

        mock_rag_service = Mock()
        mock_response = ChatResponse(
            answer="新規セッションでの回答",
            sources=[],
            confidence=0.7,
            session_id="auto-generated-session-456",
        )
        mock_rag_service.chat.return_value = mock_response

        # 依存性をオーバーライド
        app = client.app
        app.dependency_overrides[get_rag_service] = lambda: mock_rag_service

        try:
            response = client.post(
                "/api/v1/chat", json={"question": "新しい質問です", "session_id": None}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["session_id"] == "auto-generated-session-456"

            # session_idがNoneで渡されることを確認
            mock_rag_service.chat.assert_called_once_with(
                question="新しい質問です", max_results=3, session_id=None
            )
        finally:
            app.dependency_overrides.clear()
