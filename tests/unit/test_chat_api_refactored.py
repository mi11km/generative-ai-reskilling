import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI

from src.api.chat import (
    router,
    get_rag_service,
    get_rag_service_container,
    RAGServiceContainer,
)
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
def reset_container():
    """各テスト前後でRAGServiceContainerをリセット"""
    # テスト前のリセット
    RAGServiceContainer._instance = None
    yield
    # テスト後のリセット
    RAGServiceContainer._instance = None


class TestRAGServiceContainer:
    """RAGServiceContainer クラスのテスト"""

    def test_singleton_behavior(self, reset_container):
        """シングルトンの動作をテスト"""
        container1 = RAGServiceContainer()
        container2 = RAGServiceContainer()

        # 同じインスタンスが返されることを確認
        assert container1 is container2

    @patch("src.api.chat.RAGService")
    def test_get_or_create_rag_service_first_call(
        self, mock_rag_service_class, mock_settings, reset_container
    ):
        """初回呼び出しでRAGServiceが作成されることをテスト"""
        mock_rag_instance = Mock()
        mock_rag_service_class.return_value = mock_rag_instance

        container = RAGServiceContainer()
        result = container.get_or_create_rag_service(mock_settings)

        # RAGServiceが設定で初期化されることを確認
        mock_rag_service_class.assert_called_once_with(mock_settings)
        assert result == mock_rag_instance

    @patch("src.api.chat.RAGService")
    def test_get_or_create_rag_service_caching(
        self, mock_rag_service_class, mock_settings, reset_container
    ):
        """RAGServiceのキャッシュ動作をテスト"""
        mock_rag_instance = Mock()
        mock_rag_service_class.return_value = mock_rag_instance

        container = RAGServiceContainer()

        # 最初の呼び出し
        result1 = container.get_or_create_rag_service(mock_settings)

        # 2回目の呼び出し
        result2 = container.get_or_create_rag_service(mock_settings)

        # RAGServiceは1回だけ作成されることを確認
        mock_rag_service_class.assert_called_once_with(mock_settings)

        # 同じインスタンスが返されることを確認
        assert result1 is result2
        assert result1 == mock_rag_instance

    def test_reset_method(self, mock_settings, reset_container):
        """resetメソッドの動作をテスト"""
        with patch("src.api.chat.RAGService") as mock_rag_service_class:
            mock_rag_instance = Mock()
            mock_rag_service_class.return_value = mock_rag_instance

            container = RAGServiceContainer()

            # RAGServiceを作成
            container.get_or_create_rag_service(mock_settings)
            assert container._rag_service is not None

            # リセット実行
            container.reset()
            assert container._rag_service is None


class TestDependencyInjection:
    """依存性注入のテスト"""

    def test_get_rag_service_container(self, reset_container):
        """get_rag_service_container 関数のテスト"""
        container = get_rag_service_container()
        assert isinstance(container, RAGServiceContainer)

    @patch("src.api.chat.get_settings")
    @patch("src.api.chat.get_rag_service_container")
    def test_get_rag_service_dependency(self, mock_get_container, mock_get_settings):
        """get_rag_service の依存性注入をテスト"""
        mock_settings = Mock()
        mock_get_settings.return_value = mock_settings

        mock_container = Mock()
        mock_rag_service = Mock()
        mock_container.get_or_create_rag_service.return_value = mock_rag_service
        mock_get_container.return_value = mock_container

        result = get_rag_service(mock_settings, mock_container)

        # コンテナのメソッドが正しく呼ばれることを確認
        mock_container.get_or_create_rag_service.assert_called_once_with(mock_settings)
        assert result == mock_rag_service


class TestRefactoredChatAPI:
    """リファクタリング後のチャットAPIのテスト"""

    def test_chat_endpoint_with_refactored_dependency(
        self, app, client, reset_container
    ):
        """リファクタリング後の依存性注入でのチャットエンドポイントをテスト"""
        # RAGサービスのモック
        mock_rag_service = Mock()

        # チャットレスポンスのモック
        mock_response = ChatResponse(
            answer="リファクタリング後のテスト回答です。",
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

        # dependency_overridesを使ってRAGサービスをモックに置き換え
        app.dependency_overrides[get_rag_service] = lambda: mock_rag_service

        try:
            # リクエスト実行
            response = client.post(
                "/api/v1/chat",
                json={
                    "question": "リファクタリング後のテスト質問です",
                    "max_results": 3,
                },
            )

            # ステータスコードの確認
            assert response.status_code == 200

            # レスポンス内容の確認
            data = response.json()
            assert data["answer"] == "リファクタリング後のテスト回答です。"
            assert len(data["sources"]) == 1
            assert data["confidence"] == 0.85

            # RAGサービスが正しく呼ばれたことを確認
            mock_rag_service.chat.assert_called_once_with(
                question="リファクタリング後のテスト質問です",
                max_results=3,
                session_id=None,
            )
        finally:
            # テスト後にdependency_overridesをクリア
            app.dependency_overrides.clear()

    def test_health_endpoint_with_refactored_dependency(
        self, app, client, reset_container
    ):
        """リファクタリング後の依存性注入でのヘルスエンドポイントをテスト"""
        # RAGサービスのモック
        mock_rag_service = Mock()
        mock_rag_service.is_ready.return_value = True

        # dependency_overridesを使ってRAGサービスをモックに置き換え
        app.dependency_overrides[get_rag_service] = lambda: mock_rag_service

        try:
            response = client.get("/api/v1/health")

            assert response.status_code == 200
            data = response.json()
            assert data["vector_store_ready"] is True
        finally:
            # テスト後にdependency_overridesをクリア
            app.dependency_overrides.clear()


class TestRAGServiceContainerIntegration:
    """RAGServiceContainer の統合テスト"""

    @patch("src.api.chat.RAGService")
    @patch("src.api.chat.logger")
    def test_container_logging(
        self, mock_logger, mock_rag_service_class, mock_settings, reset_container
    ):
        """RAGService作成時のログ出力をテスト"""
        mock_rag_instance = Mock()
        mock_rag_service_class.return_value = mock_rag_instance

        container = RAGServiceContainer()
        container.get_or_create_rag_service(mock_settings)

        # ログが正しく呼ばれたことを確認
        mock_logger.info.assert_any_call("新しいRAGサービスインスタンスを作成中...")
        mock_logger.info.assert_any_call("RAGサービスインスタンスの作成が完了しました")

    def test_multiple_containers_same_instance(self, reset_container):
        """複数のコンテナインスタンスが同じオブジェクトであることをテスト"""
        containers = [RAGServiceContainer() for _ in range(5)]

        # すべてが同じインスタンスであることを確認
        first_container = containers[0]
        for container in containers[1:]:
            assert container is first_container

    @patch("src.api.chat.RAGService")
    def test_container_thread_safety_simulation(
        self, mock_rag_service_class, mock_settings, reset_container
    ):
        """コンテナのスレッドセーフティ（シミュレーション）をテスト"""
        import threading
        import time

        mock_rag_instance = Mock()
        mock_rag_service_class.return_value = mock_rag_instance

        results = []

        def create_rag_service():
            container = RAGServiceContainer()
            time.sleep(0.01)  # 少し遅延を追加
            rag_service = container.get_or_create_rag_service(mock_settings)
            results.append(rag_service)

        # 複数スレッドで同時実行
        threads = [threading.Thread(target=create_rag_service) for _ in range(5)]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # すべてのスレッドが同じRAGServiceインスタンスを取得したことを確認
        assert len(results) == 5
        assert all(rag_service is results[0] for rag_service in results)

        # RAGServiceは1回だけ作成されたことを確認
        mock_rag_service_class.assert_called_once()


class TestBackwardCompatibility:
    """後方互換性のテスト"""

    @patch("src.api.chat.RAGServiceContainer")
    def test_api_endpoints_still_work(
        self, mock_container_class, client, reset_container
    ):
        """APIエンドポイントが引き続き動作することをテスト"""
        # コンテナのモック
        mock_container = Mock()
        mock_container_class.return_value = mock_container

        mock_rag_service = Mock()
        mock_container.get_or_create_rag_service.return_value = mock_rag_service

        mock_response = ChatResponse(
            answer="後方互換性テストの回答", sources=[], confidence=0.5
        )
        mock_rag_service.chat.return_value = mock_response
        mock_rag_service.is_ready.return_value = True

        # チャットエンドポイントのテスト
        chat_response = client.post(
            "/api/v1/chat", json={"question": "後方互換性のテスト"}
        )
        assert chat_response.status_code == 200

        # ヘルスエンドポイントのテスト
        health_response = client.get("/api/v1/health")
        assert health_response.status_code == 200


@pytest.mark.parametrize(
    "question,expected_calls",
    [
        ("短い質問", 1),
        ("少し長めの質問です", 1),
        ("とても長い質問になります" * 10, 1),
    ],
)
def test_refactored_endpoint_various_inputs(
    question, expected_calls, client, reset_container
):
    """リファクタリング後のエンドポイントで様々な入力をパラメータ化テストで検証"""
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
            "/api/v1/chat", json={"question": question, "max_results": 3}
        )

        assert response.status_code == 200
        assert mock_rag_service.chat.call_count == expected_calls
    finally:
        app.dependency_overrides.clear()
