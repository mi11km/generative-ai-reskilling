import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI

from src.api.chat import router, get_rag_service
from src.models.schemas import ChatRequest, ChatResponse, HealthResponse, SourceDocument
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
    return Settings(
        openai_api_key="test_api_key",
        version="0.1.0",
        debug=True
    )


@pytest.fixture
def mock_rag_service():
    """テスト用のRAGサービス"""
    mock_service = Mock()
    mock_service.is_ready.return_value = True
    return mock_service


class TestChatAPI:
    """チャットAPIのテスト"""
    
    @patch("src.api.chat.get_rag_service")
    def test_chat_endpoint_successful(self, mock_get_rag_service, client):
        """正常なチャットリクエストをテスト"""
        # RAGサービスのモック
        mock_rag_service = Mock()
        mock_get_rag_service.return_value = mock_rag_service
        
        # チャットレスポンスのモック
        mock_response = ChatResponse(
            answer="テストの回答です。",
            sources=[
                SourceDocument(
                    content="テストソース内容",
                    section="テストセクション",
                    metadata={"score": 0.8}
                )
            ],
            confidence=0.85
        )
        mock_rag_service.chat.return_value = mock_response
        
        # リクエスト実行
        response = client.post("/api/v1/chat", json={
            "question": "テストの質問です",
            "max_results": 3
        })
        
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
        mock_rag_service.chat.assert_called_once_with("テストの質問です", 3)
    
    @patch("src.api.chat.get_rag_service")
    def test_chat_endpoint_default_max_results(self, mock_get_rag_service, client):
        """デフォルトのmax_resultsでのチャットリクエストをテスト"""
        mock_rag_service = Mock()
        mock_get_rag_service.return_value = mock_rag_service
        
        mock_response = ChatResponse(
            answer="回答",
            sources=[],
            confidence=0.5
        )
        mock_rag_service.chat.return_value = mock_response
        
        # max_resultsを指定しないリクエスト
        response = client.post("/api/v1/chat", json={
            "question": "質問"
        })
        
        assert response.status_code == 200
        
        # デフォルト値（3）で呼ばれることを確認
        mock_rag_service.chat.assert_called_once_with("質問", 3)
    
    @patch("src.api.chat.get_rag_service")
    def test_chat_endpoint_custom_max_results(self, mock_get_rag_service, client):
        """カスタムmax_resultsでのチャットリクエストをテスト"""
        mock_rag_service = Mock()
        mock_get_rag_service.return_value = mock_rag_service
        
        mock_response = ChatResponse(
            answer="回答",
            sources=[],
            confidence=0.5
        )
        mock_rag_service.chat.return_value = mock_response
        
        # カスタムmax_resultsでのリクエスト
        response = client.post("/api/v1/chat", json={
            "question": "質問",
            "max_results": 7
        })
        
        assert response.status_code == 200
        
        # カスタム値で呼ばれることを確認
        mock_rag_service.chat.assert_called_once_with("質問", 7)
    
    def test_chat_endpoint_invalid_max_results(self, client):
        """無効なmax_resultsでのバリデーションエラーをテスト"""
        # max_resultsが範囲外（0以下）
        response = client.post("/api/v1/chat", json={
            "question": "質問",
            "max_results": 0
        })
        assert response.status_code == 422  # Validation Error
        
        # max_resultsが範囲外（10より大きい）
        response = client.post("/api/v1/chat", json={
            "question": "質問",
            "max_results": 11
        })
        assert response.status_code == 422  # Validation Error
    
    def test_chat_endpoint_missing_question(self, client):
        """質問が欠如している場合のバリデーションエラーをテスト"""
        response = client.post("/api/v1/chat", json={
            "max_results": 3
        })
        assert response.status_code == 422  # Validation Error
    
    def test_chat_endpoint_empty_question(self, client):
        """空の質問でのバリデーションエラーをテスト"""
        response = client.post("/api/v1/chat", json={
            "question": "",
            "max_results": 3
        })
        assert response.status_code == 422  # Validation Error
    
    @patch("src.api.chat.get_rag_service")
    def test_chat_endpoint_internal_error(self, mock_get_rag_service, client):
        """内部エラーの処理をテスト"""
        mock_rag_service = Mock()
        mock_get_rag_service.return_value = mock_rag_service
        
        # RAGサービスで例外が発生
        mock_rag_service.chat.side_effect = Exception("テストエラー")
        
        response = client.post("/api/v1/chat", json={
            "question": "テスト質問"
        })
        
        # HTTPException (500) が発生することを確認
        assert response.status_code == 500
        assert "内部サーバーエラーが発生しました" in response.json()["detail"]
    
    @patch("src.api.chat.get_rag_service")
    def test_chat_endpoint_japanese_question(self, mock_get_rag_service, client):
        """日本語の質問での処理をテスト"""
        mock_rag_service = Mock()
        mock_get_rag_service.return_value = mock_rag_service
        
        mock_response = ChatResponse(
            answer="日本語での回答です。",
            sources=[],
            confidence=0.7
        )
        mock_rag_service.chat.return_value = mock_response
        
        japanese_question = "ゲームの基本システムについて教えてください。"
        response = client.post("/api/v1/chat", json={
            "question": japanese_question
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["answer"] == "日本語での回答です。"
        
        # 日本語の質問が正しく渡されることを確認
        mock_rag_service.chat.assert_called_once_with(japanese_question, 3)
    
    @patch("src.api.chat.get_rag_service")
    def test_chat_endpoint_long_question(self, mock_get_rag_service, client):
        """長い質問での処理をテスト"""
        mock_rag_service = Mock()
        mock_get_rag_service.return_value = mock_rag_service
        
        mock_response = ChatResponse(
            answer="長い質問への回答",
            sources=[],
            confidence=0.6
        )
        mock_rag_service.chat.return_value = mock_response
        
        # 長い質問（1000文字）
        long_question = "テスト質問です。" * 100
        response = client.post("/api/v1/chat", json={
            "question": long_question
        })
        
        assert response.status_code == 200
        
        # 長い質問も正しく処理されることを確認
        mock_rag_service.chat.assert_called_once_with(long_question, 3)


class TestHealthAPI:
    """ヘルスチェックAPIのテスト"""
    
    @patch("src.api.chat.get_rag_service")
    @patch("src.api.chat.get_settings")
    def test_health_endpoint_healthy(self, mock_get_settings, mock_get_rag_service, client):
        """正常な状態でのヘルスチェックをテスト"""
        # 設定のモック
        mock_settings = Mock()
        mock_settings.version = "0.1.0"
        mock_get_settings.return_value = mock_settings
        
        # RAGサービスのモック
        mock_rag_service = Mock()
        mock_rag_service.is_ready.return_value = True
        mock_get_rag_service.return_value = mock_rag_service
        
        response = client.get("/api/v1/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "0.1.0"
        assert data["vector_store_ready"] is True
    
    @patch("src.api.chat.get_rag_service")
    @patch("src.api.chat.get_settings")
    def test_health_endpoint_vector_store_not_ready(self, mock_get_settings, mock_get_rag_service, client):
        """ベクトルストアが準備できていない状態でのヘルスチェックをテスト"""
        mock_settings = Mock()
        mock_settings.version = "0.1.0"
        mock_get_settings.return_value = mock_settings
        
        mock_rag_service = Mock()
        mock_rag_service.is_ready.return_value = False
        mock_get_rag_service.return_value = mock_rag_service
        
        response = client.get("/api/v1/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"  # ステータス自体は healthy
        assert data["vector_store_ready"] is False


class TestGetRAGService:
    """get_rag_service 依存性注入のテスト"""
    
    @patch("src.api.chat._rag_service", None)
    @patch("src.api.chat.RAGService")
    def test_get_rag_service_first_call(self, mock_rag_service_class, mock_settings):
        """初回呼び出しでRAGServiceが作成されることをテスト"""
        mock_rag_instance = Mock()
        mock_rag_service_class.return_value = mock_rag_instance
        
        result = get_rag_service(mock_settings)
        
        # RAGServiceが設定で初期化されることを確認
        mock_rag_service_class.assert_called_once_with(mock_settings)
        assert result == mock_rag_instance
    
    @patch("src.api.chat.RAGService")
    def test_get_rag_service_singleton_behavior(self, mock_rag_service_class, mock_settings):
        """シングルトン動作をテスト"""
        # グローバル変数をクリア
        import src.api.chat
        src.api.chat._rag_service = None
        
        mock_rag_instance = Mock()
        mock_rag_service_class.return_value = mock_rag_instance
        
        # 最初の呼び出し
        result1 = get_rag_service(mock_settings)
        
        # 2回目の呼び出し
        result2 = get_rag_service(mock_settings)
        
        # RAGServiceは1回だけ作成されることを確認
        mock_rag_service_class.assert_called_once_with(mock_settings)
        
        # 同じインスタンスが返されることを確認
        assert result1 is result2
        assert result1 == mock_rag_instance


@pytest.mark.parametrize("question,max_results", [
    ("短い質問", 1),
    ("中くらいの長さの質問です。", 3),
    ("とても長い質問になります。" * 10, 5),
    ("日本語での質問：ゲームシステムについて", 7),
    ("English question about game mechanics", 10),
])
@patch("src.api.chat.get_rag_service")
def test_chat_endpoint_various_inputs(mock_get_rag_service, question, max_results, client):
    """様々な入力でのチャットエンドポイントをパラメータ化テストで検証"""
    mock_rag_service = Mock()
    mock_get_rag_service.return_value = mock_rag_service
    
    mock_response = ChatResponse(
        answer=f"回答: {question[:20]}...",
        sources=[],
        confidence=0.5
    )
    mock_rag_service.chat.return_value = mock_response
    
    response = client.post("/api/v1/chat", json={
        "question": question,
        "max_results": max_results
    })
    
    assert response.status_code == 200
    mock_rag_service.chat.assert_called_once_with(question, max_results)


@pytest.mark.parametrize("invalid_max_results", [-1, 0, 11, 100, -5])
def test_chat_endpoint_invalid_max_results_parametrized(invalid_max_results, client):
    """無効なmax_results値をパラメータ化テストで検証"""
    response = client.post("/api/v1/chat", json={
        "question": "テスト質問",
        "max_results": invalid_max_results
    })
    
    assert response.status_code == 422  # Validation Error