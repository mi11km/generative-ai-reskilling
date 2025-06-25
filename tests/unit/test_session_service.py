import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from src.services.session_service import SessionService
from src.models.database import DatabaseManager, Session, Message


class TestSessionService:
    """セッションサービスのテスト"""

    @pytest.fixture
    def mock_db_manager(self):
        """モックデータベースマネージャー"""
        return Mock(spec=DatabaseManager)

    @pytest.fixture
    def session_service(self, mock_db_manager):
        """セッションサービスのインスタンス"""
        return SessionService(mock_db_manager)

    @pytest.fixture
    def mock_db_session(self):
        """モックデータベースセッション"""
        mock_session = Mock()
        mock_session.__enter__ = Mock(return_value=mock_session)
        mock_session.__exit__ = Mock(return_value=False)
        return mock_session

    def test_create_session_with_title(
        self, session_service, mock_db_manager, mock_db_session
    ):
        """タイトル指定でセッション作成のテスト"""
        # Arrange
        mock_db_manager.get_session.return_value = mock_db_session
        mock_db_session_obj = Mock(spec=Session)
        mock_db_session_obj.id = "test-session-id"
        mock_db_session_obj.title = "テストセッション"
        mock_db_session_obj.created_at = datetime(2023, 1, 1, 12, 0, 0)
        mock_db_session_obj.updated_at = datetime(2023, 1, 1, 12, 0, 0)

        mock_db_session.add = Mock()
        mock_db_session.commit = Mock()
        mock_db_session.refresh = Mock()

        with patch("src.services.session_service.Session") as mock_session_class:
            mock_session_class.return_value = mock_db_session_obj

            # Act
            result = session_service.create_session("テストセッション")

            # Assert
            assert result["id"] == "test-session-id"
            assert result["title"] == "テストセッション"
            assert result["created_at"] == "2023-01-01T12:00:00"
            mock_session_class.assert_called_once_with(title="テストセッション")
            mock_db_session.add.assert_called_once()
            mock_db_session.commit.assert_called_once()

    def test_create_session_without_title(
        self, session_service, mock_db_manager, mock_db_session
    ):
        """タイトル未指定でセッション作成のテスト"""
        # Arrange
        mock_db_manager.get_session.return_value = mock_db_session
        mock_db_session_obj = Mock(spec=Session)
        mock_db_session_obj.id = "test-session-id"
        mock_db_session_obj.title = "新しい会話 - 2023/01/01 12:00"
        mock_db_session_obj.created_at = datetime(2023, 1, 1, 12, 0, 0)
        mock_db_session_obj.updated_at = datetime(2023, 1, 1, 12, 0, 0)

        mock_db_session.add = Mock()
        mock_db_session.commit = Mock()
        mock_db_session.refresh = Mock()

        with (
            patch("src.services.session_service.Session") as mock_session_class,
            patch("src.services.session_service.datetime") as mock_datetime,
        ):
            mock_datetime.now.return_value.strftime.return_value = "2023/01/01 12:00"
            mock_session_class.return_value = mock_db_session_obj

            # Act
            result = session_service.create_session()

            # Assert
            assert result["id"] == "test-session-id"
            assert "新しい会話 -" in result["title"]
            mock_session_class.assert_called_once()

    def test_get_sessions(self, session_service, mock_db_manager, mock_db_session):
        """セッション一覧取得のテスト"""
        # Arrange
        mock_db_manager.get_session.return_value = mock_db_session
        mock_session1 = Mock(spec=Session)
        mock_session1.id = "session-1"
        mock_session1.title = "セッション1"
        mock_session1.created_at = datetime(2023, 1, 1, 12, 0, 0)
        mock_session1.updated_at = datetime(2023, 1, 1, 12, 0, 0)

        mock_session2 = Mock(spec=Session)
        mock_session2.id = "session-2"
        mock_session2.title = "セッション2"
        mock_session2.created_at = datetime(2023, 1, 2, 12, 0, 0)
        mock_session2.updated_at = datetime(2023, 1, 2, 12, 0, 0)

        mock_query = Mock()
        mock_query.order_by.return_value.all.return_value = [
            mock_session2,
            mock_session1,
        ]
        mock_db_session.query.return_value = mock_query

        # Act
        result = session_service.get_sessions()

        # Assert
        assert len(result) == 2
        assert result[0]["id"] == "session-2"
        assert result[1]["id"] == "session-1"
        assert result[0]["title"] == "セッション2"

    def test_get_session_exists(
        self, session_service, mock_db_manager, mock_db_session
    ):
        """存在するセッション取得のテスト"""
        # Arrange
        mock_db_manager.get_session.return_value = mock_db_session
        mock_session_obj = Mock(spec=Session)
        mock_session_obj.id = "test-session-id"
        mock_session_obj.title = "テストセッション"
        mock_session_obj.created_at = datetime(2023, 1, 1, 12, 0, 0)
        mock_session_obj.updated_at = datetime(2023, 1, 1, 12, 0, 0)

        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_session_obj
        mock_db_session.query.return_value = mock_query

        # Act
        result = session_service.get_session("test-session-id")

        # Assert
        assert result is not None
        assert result["id"] == "test-session-id"
        assert result["title"] == "テストセッション"

    def test_get_session_not_exists(
        self, session_service, mock_db_manager, mock_db_session
    ):
        """存在しないセッション取得のテスト"""
        # Arrange
        mock_db_manager.get_session.return_value = mock_db_session
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db_session.query.return_value = mock_query

        # Act
        result = session_service.get_session("non-existent-id")

        # Assert
        assert result is None

    def test_delete_session_success(
        self, session_service, mock_db_manager, mock_db_session
    ):
        """セッション削除成功のテスト"""
        # Arrange
        mock_db_manager.get_session.return_value = mock_db_session
        mock_session_obj = Mock(spec=Session)

        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_session_obj
        mock_db_session.query.return_value = mock_query
        mock_db_session.delete = Mock()
        mock_db_session.commit = Mock()

        # Act
        result = session_service.delete_session("test-session-id")

        # Assert
        assert result is True
        mock_db_session.delete.assert_called_once_with(mock_session_obj)
        mock_db_session.commit.assert_called_once()

    def test_delete_session_not_found(
        self, session_service, mock_db_manager, mock_db_session
    ):
        """存在しないセッション削除のテスト"""
        # Arrange
        mock_db_manager.get_session.return_value = mock_db_session
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db_session.query.return_value = mock_query

        # Act
        result = session_service.delete_session("non-existent-id")

        # Assert
        assert result is False

    def test_add_message_success(
        self, session_service, mock_db_manager, mock_db_session
    ):
        """メッセージ追加成功のテスト"""
        # Arrange
        mock_db_manager.get_session.return_value = mock_db_session
        mock_session_obj = Mock(spec=Session)
        mock_message_obj = Mock(spec=Message)
        mock_message_obj.id = "message-id"
        mock_message_obj.session_id = "session-id"
        mock_message_obj.role = "user"
        mock_message_obj.content = "テストメッセージ"
        mock_message_obj.created_at = datetime(2023, 1, 1, 12, 0, 0)
        mock_message_obj.get_metadata_dict.return_value = {}

        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_session_obj
        mock_db_session.query.return_value = mock_query
        mock_db_session.add = Mock()
        mock_db_session.commit = Mock()
        mock_db_session.refresh = Mock()

        with (
            patch("src.services.session_service.Message") as mock_message_class,
            patch("src.services.session_service.datetime") as mock_datetime,
        ):
            mock_message_class.return_value = mock_message_obj
            mock_datetime.utcnow.return_value = datetime(2023, 1, 1, 12, 5, 0)

            # Act
            result = session_service.add_message(
                session_id="session-id", role="user", content="テストメッセージ"
            )

            # Assert
            assert result is not None
            assert result["id"] == "message-id"
            assert result["role"] == "user"
            assert result["content"] == "テストメッセージ"
            mock_message_class.assert_called_once_with(
                session_id="session-id", role="user", content="テストメッセージ"
            )

    def test_add_message_session_not_found(
        self, session_service, mock_db_manager, mock_db_session
    ):
        """存在しないセッションへのメッセージ追加のテスト"""
        # Arrange
        mock_db_manager.get_session.return_value = mock_db_session
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db_session.query.return_value = mock_query

        # Act
        result = session_service.add_message(
            session_id="non-existent-session", role="user", content="テストメッセージ"
        )

        # Assert
        assert result is None
