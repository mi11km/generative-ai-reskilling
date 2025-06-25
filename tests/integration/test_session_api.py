import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from src.main import create_app
from src.api.sessions import SessionServiceContainer


@pytest.fixture
def client():
    """テスト用クライアント"""
    app = create_app()
    return TestClient(app)


@pytest.fixture
def mock_session_service():
    """モックセッションサービス"""
    return Mock()


@pytest.fixture(autouse=True)
def setup_mock_session_service(mock_session_service):
    """各テストでモックセッションサービスを使用"""
    with patch.object(
        SessionServiceContainer,
        "get_or_create_session_service",
        return_value=mock_session_service,
    ):
        yield mock_session_service


class TestSessionAPI:
    """セッション管理APIの統合テスト"""

    def test_create_session_with_title(self, client, mock_session_service):
        """タイトル指定でセッション作成のテスト"""
        # Arrange
        mock_session_service.create_session.return_value = {
            "id": "test-session-id",
            "title": "テストセッション",
            "created_at": "2023-01-01T12:00:00",
            "updated_at": "2023-01-01T12:00:00",
        }

        # Act
        response = client.post("/api/v1/sessions", json={"title": "テストセッション"})

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "test-session-id"
        assert data["title"] == "テストセッション"
        mock_session_service.create_session.assert_called_once_with("テストセッション")

    def test_create_session_without_title(self, client, mock_session_service):
        """タイトル未指定でセッション作成のテスト"""
        # Arrange
        mock_session_service.create_session.return_value = {
            "id": "test-session-id",
            "title": "新しい会話 - 2023/01/01 12:00",
            "created_at": "2023-01-01T12:00:00",
            "updated_at": "2023-01-01T12:00:00",
        }

        # Act
        response = client.post("/api/v1/sessions", json={})

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "test-session-id"
        assert "新しい会話" in data["title"]
        mock_session_service.create_session.assert_called_once_with(None)

    def test_get_sessions(self, client, mock_session_service):
        """セッション一覧取得のテスト"""
        # Arrange
        mock_session_service.get_sessions.return_value = [
            {
                "id": "session-1",
                "title": "セッション1",
                "created_at": "2023-01-01T12:00:00",
                "updated_at": "2023-01-01T12:00:00",
            },
            {
                "id": "session-2",
                "title": "セッション2",
                "created_at": "2023-01-02T12:00:00",
                "updated_at": "2023-01-02T12:00:00",
            },
        ]

        # Act
        response = client.get("/api/v1/sessions")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["id"] == "session-1"
        assert data[1]["id"] == "session-2"
        mock_session_service.get_sessions.assert_called_once()

    def test_get_session_exists(self, client, mock_session_service):
        """存在するセッション取得のテスト"""
        # Arrange
        session_id = "test-session-id"
        mock_session_service.get_session.return_value = {
            "id": session_id,
            "title": "テストセッション",
            "created_at": "2023-01-01T12:00:00",
            "updated_at": "2023-01-01T12:00:00",
        }

        # Act
        response = client.get(f"/api/v1/sessions/{session_id}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == session_id
        assert data["title"] == "テストセッション"
        mock_session_service.get_session.assert_called_once_with(session_id)

    def test_get_session_not_found(self, client, mock_session_service):
        """存在しないセッション取得のテスト"""
        # Arrange
        session_id = "non-existent-id"
        mock_session_service.get_session.return_value = None

        # Act
        response = client.get(f"/api/v1/sessions/{session_id}")

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "セッションが見つかりません"

    def test_update_session_success(self, client, mock_session_service):
        """セッション更新成功のテスト"""
        # Arrange
        session_id = "test-session-id"
        mock_session_service.update_session_title.return_value = True
        mock_session_service.get_session.return_value = {
            "id": session_id,
            "title": "更新されたタイトル",
            "created_at": "2023-01-01T12:00:00",
            "updated_at": "2023-01-01T12:30:00",
        }

        # Act
        response = client.put(
            f"/api/v1/sessions/{session_id}", json={"title": "更新されたタイトル"}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "更新されたタイトル"
        mock_session_service.update_session_title.assert_called_once_with(
            session_id, "更新されたタイトル"
        )

    def test_update_session_not_found(self, client, mock_session_service):
        """存在しないセッション更新のテスト"""
        # Arrange
        session_id = "non-existent-id"
        mock_session_service.update_session_title.return_value = False

        # Act
        response = client.put(
            f"/api/v1/sessions/{session_id}", json={"title": "新しいタイトル"}
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "セッションが見つかりません"

    def test_delete_session_success(self, client, mock_session_service):
        """セッション削除成功のテスト"""
        # Arrange
        session_id = "test-session-id"
        mock_session_service.delete_session.return_value = True

        # Act
        response = client.delete(f"/api/v1/sessions/{session_id}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "セッションが削除されました"
        mock_session_service.delete_session.assert_called_once_with(session_id)

    def test_delete_session_not_found(self, client, mock_session_service):
        """存在しないセッション削除のテスト"""
        # Arrange
        session_id = "non-existent-id"
        mock_session_service.delete_session.return_value = False

        # Act
        response = client.delete(f"/api/v1/sessions/{session_id}")

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "セッションが見つかりません"

    def test_get_session_messages_success(self, client, mock_session_service):
        """セッションメッセージ取得成功のテスト"""
        # Arrange
        session_id = "test-session-id"
        mock_session_service.get_session.return_value = {
            "id": session_id,
            "title": "テストセッション",
            "created_at": "2023-01-01T12:00:00",
            "updated_at": "2023-01-01T12:00:00",
        }
        mock_session_service.get_messages.return_value = [
            {
                "id": "message-1",
                "session_id": session_id,
                "role": "user",
                "content": "こんにちは",
                "created_at": "2023-01-01T12:00:00",
                "metadata": {},
            },
            {
                "id": "message-2",
                "session_id": session_id,
                "role": "assistant",
                "content": "こんにちは！何かご質問はありますか？",
                "created_at": "2023-01-01T12:01:00",
                "metadata": {"confidence": 0.95},
            },
        ]

        # Act
        response = client.get(f"/api/v1/sessions/{session_id}/messages")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["role"] == "user"
        assert data[1]["role"] == "assistant"
        mock_session_service.get_session.assert_called_once_with(session_id)
        mock_session_service.get_messages.assert_called_once_with(session_id)

    def test_get_session_messages_session_not_found(self, client, mock_session_service):
        """存在しないセッションのメッセージ取得のテスト"""
        # Arrange
        session_id = "non-existent-id"
        mock_session_service.get_session.return_value = None

        # Act
        response = client.get(f"/api/v1/sessions/{session_id}/messages")

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "セッションが見つかりません"
