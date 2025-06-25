import pytest
from unittest.mock import Mock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.main import create_app, main, lifespan


class TestCreateApp:
    """create_app 関数のテスト"""

    @patch("src.main.get_settings")
    def test_create_app_basic_configuration(self, mock_get_settings):
        """基本的なアプリケーション設定をテスト"""
        mock_settings = Mock()
        mock_settings.app_name = "Test Game RAG API"
        mock_settings.version = "1.0.0"
        mock_get_settings.return_value = mock_settings

        app = create_app()

        # FastAPIアプリケーションが作成されることを確認
        assert isinstance(app, FastAPI)
        assert app.title == "Test Game RAG API"
        assert app.version == "1.0.0"
        assert app.description == "ゲーム仕様書に基づいて質問に回答するRAG API"

    @patch("src.main.get_settings")
    def test_create_app_middleware_configuration(self, mock_get_settings):
        """CORS ミドルウェアの設定をテスト"""
        mock_settings = Mock()
        mock_settings.app_name = "Test API"
        mock_settings.version = "0.1.0"
        mock_get_settings.return_value = mock_settings

        app = create_app()

        # CORS ミドルウェアが追加されていることを確認
        # FastAPIのuser_middlewareから確認
        middleware_found = False
        for middleware in app.user_middleware:
            if hasattr(middleware, "cls"):
                from fastapi.middleware.cors import CORSMiddleware

                if middleware.cls == CORSMiddleware:
                    middleware_found = True
                    break

        assert middleware_found, "CORSMiddleware should be configured"

    @patch("src.main.get_settings")
    def test_create_app_router_inclusion(self, mock_get_settings):
        """ルーターが正しく含まれることをテスト"""
        mock_settings = Mock()
        mock_settings.app_name = "Test API"
        mock_settings.version = "0.1.0"
        mock_get_settings.return_value = mock_settings

        app = create_app()

        # ルートが登録されていることを確認
        routes = [route.path for route in app.routes]

        # チャットAPIルートが含まれていることを確認
        assert "/api/v1/chat" in routes
        assert "/api/v1/health" in routes
        assert "/" in routes  # ルートエンドポイント

    @patch("src.main.get_settings")
    def test_create_app_root_endpoint(self, mock_get_settings):
        """ルートエンドポイントの動作をテスト"""
        mock_settings = Mock()
        mock_settings.app_name = "Test API"
        mock_settings.version = "1.2.3"
        mock_get_settings.return_value = mock_settings

        app = create_app()
        client = TestClient(app)

        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Game Specification RAG API"
        assert data["version"] == "1.2.3"
        assert data["docs"] == "/docs"


class TestLifespan:
    """lifespan コンテキストマネージャーのテスト"""

    @patch("src.main.get_settings")
    @patch("src.main.RAGService")
    @patch("src.main.logger")
    async def test_lifespan_successful_startup(
        self, mock_logger, mock_rag_service, mock_get_settings
    ):
        """正常な起動プロセスをテスト"""
        mock_settings = Mock()
        mock_get_settings.return_value = mock_settings

        mock_rag_instance = Mock()
        mock_rag_service.return_value = mock_rag_instance

        app = Mock()

        # ライフサイクルマネージャーを実行
        async with lifespan(app):
            # 起動処理が完了した状態
            pass

        # 適切なログが出力されることを確認
        mock_logger.info.assert_any_call("アプリケーションを起動しています...")
        mock_logger.info.assert_any_call("RAGサービスを初期化中...")
        mock_logger.info.assert_any_call("RAGサービスの初期化が完了しました")
        mock_logger.info.assert_any_call("アプリケーションを終了しています...")

        # RAGServiceが設定で初期化されることを確認
        mock_rag_service.assert_called_once_with(mock_settings)

    @patch("src.main.get_settings")
    @patch("src.main.RAGService")
    @patch("src.main.logger")
    async def test_lifespan_rag_service_initialization_failure(
        self, mock_logger, mock_rag_service, mock_get_settings
    ):
        """RAGサービス初期化失敗時の処理をテスト"""
        mock_settings = Mock()
        mock_get_settings.return_value = mock_settings

        # RAGService初期化で例外が発生
        mock_rag_service.side_effect = Exception("初期化エラー")

        app = Mock()

        # 例外が再発生することを確認
        with pytest.raises(Exception) as exc_info:
            async with lifespan(app):
                pass

        assert "初期化エラー" in str(exc_info.value)

        # エラーログが出力されることを確認
        mock_logger.error.assert_called_once()
        error_call_args = mock_logger.error.call_args[0][0]
        assert "RAGサービスの初期化に失敗しました" in error_call_args

    @patch("src.main.get_settings")
    @patch("src.main.RAGService")
    @patch("src.main.logger")
    async def test_lifespan_startup_and_shutdown_logs(
        self, mock_logger, mock_rag_service, mock_get_settings
    ):
        """起動と終了時のログ出力をテスト"""
        mock_settings = Mock()
        mock_get_settings.return_value = mock_settings

        mock_rag_instance = Mock()
        mock_rag_service.return_value = mock_rag_instance

        app = Mock()

        async with lifespan(app):
            # 起動ログが出力されていることを確認
            startup_calls = [
                call for call in mock_logger.info.call_args_list if "起動" in str(call)
            ]
            assert len(startup_calls) > 0

        # 終了ログが出力されていることを確認
        shutdown_calls = [
            call for call in mock_logger.info.call_args_list if "終了" in str(call)
        ]
        assert len(shutdown_calls) > 0


class TestMain:
    """main 関数のテスト"""

    @patch("src.main.uvicorn.run")
    @patch("src.main.create_app")
    @patch("src.main.get_settings")
    @patch("src.main.logger")
    def test_main_successful_execution(
        self, mock_logger, mock_get_settings, mock_create_app, mock_uvicorn_run
    ):
        """正常なメイン関数の実行をテスト"""
        mock_settings = Mock()
        mock_settings.openai_api_key = "test_api_key"
        mock_settings.debug = False
        mock_get_settings.return_value = mock_settings

        mock_app = Mock()
        mock_create_app.return_value = mock_app

        main()

        # create_appが呼ばれることを確認
        mock_create_app.assert_called_once()

        # uvicorn.runが正しい引数で呼ばれることを確認
        mock_uvicorn_run.assert_called_once_with(
            mock_app, host="0.0.0.0", port=8000, reload=False
        )

        # 起動ログが出力されることを確認
        mock_logger.info.assert_called_with(
            "サーバーを起動します: http://localhost:8000"
        )

    @patch("src.main.uvicorn.run")
    @patch("src.main.create_app")
    @patch("src.main.get_settings")
    @patch("src.main.logger")
    def test_main_with_debug_mode(
        self, mock_logger, mock_get_settings, mock_create_app, mock_uvicorn_run
    ):
        """デバッグモードでのメイン関数実行をテスト"""
        mock_settings = Mock()
        mock_settings.openai_api_key = "test_api_key"
        mock_settings.debug = True  # デバッグモード
        mock_get_settings.return_value = mock_settings

        mock_app = Mock()
        mock_create_app.return_value = mock_app

        main()

        # reloadがTrueで呼ばれることを確認
        mock_uvicorn_run.assert_called_once_with(
            mock_app, host="0.0.0.0", port=8000, reload=True
        )

    @patch("src.main.uvicorn.run")
    @patch("src.main.create_app")
    @patch("src.main.sys.exit")
    @patch("src.main.get_settings")
    @patch("src.main.logger")
    def test_main_missing_api_key(
        self,
        mock_logger,
        mock_get_settings,
        mock_sys_exit,
        mock_create_app,
        mock_uvicorn_run,
    ):
        """OpenAI APIキーが設定されていない場合のテスト"""
        mock_settings = Mock()
        mock_settings.openai_api_key = None  # APIキーが設定されていない
        mock_get_settings.return_value = mock_settings

        # sys.exit()を実際に例外を投げるように設定
        mock_sys_exit.side_effect = SystemExit(1)

        with pytest.raises(SystemExit):
            main()

        # エラーログが出力されることを確認
        mock_logger.error.assert_called_with(
            "OPENAI_API_KEY環境変数が設定されていません"
        )

        # sys.exit(1)が呼ばれることを確認
        mock_sys_exit.assert_called_once_with(1)

        # uvicorn.runが呼ばれないことを確認
        mock_uvicorn_run.assert_not_called()

    @patch("src.main.uvicorn.run")
    @patch("src.main.create_app")
    @patch("src.main.sys.exit")
    @patch("src.main.get_settings")
    @patch("src.main.logger")
    def test_main_empty_api_key(
        self,
        mock_logger,
        mock_get_settings,
        mock_sys_exit,
        mock_create_app,
        mock_uvicorn_run,
    ):
        """空のOpenAI APIキーの場合のテスト"""
        mock_settings = Mock()
        mock_settings.openai_api_key = ""  # 空のAPIキー
        mock_get_settings.return_value = mock_settings

        # sys.exit()を実際に例外を投げるように設定
        mock_sys_exit.side_effect = SystemExit(1)

        with pytest.raises(SystemExit):
            main()

        # エラーログが出力されることを確認
        mock_logger.error.assert_called_with(
            "OPENAI_API_KEY環境変数が設定されていません"
        )

        # sys.exit(1)が呼ばれることを確認
        mock_sys_exit.assert_called_once_with(1)

        # uvicorn.runが呼ばれないことを確認
        mock_uvicorn_run.assert_not_called()


class TestMainIntegration:
    """main.py の統合テスト"""

    @patch("src.main.uvicorn.run")
    @patch("src.main.RAGService")
    @patch("src.main.get_settings")
    def test_create_app_with_lifespan_integration(
        self, mock_get_settings, mock_rag_service, mock_uvicorn_run
    ):
        """create_appとlifespanの統合をテスト"""
        mock_settings = Mock()
        mock_settings.app_name = "Integration Test API"
        mock_settings.version = "0.1.0"
        mock_settings.openai_api_key = "test_key"
        mock_settings.debug = False
        mock_get_settings.return_value = mock_settings

        mock_rag_instance = Mock()
        mock_rag_service.return_value = mock_rag_instance

        # アプリケーション作成
        app = create_app()

        # ライフサイクルが設定されていることを確認
        assert app.router.lifespan_context is not None

        # クライアントでテスト実行
        client = TestClient(app)

        # ルートエンドポイントが動作することを確認
        response = client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert data["message"] == "Game Specification RAG API"
        assert data["version"] == "0.1.0"


@pytest.mark.parametrize(
    "debug_mode,expected_reload",
    [
        (True, True),
        (False, False),
    ],
)
@patch("src.main.uvicorn.run")
@patch("src.main.create_app")
@patch("src.main.get_settings")
def test_main_debug_mode_parameter(
    mock_get_settings, mock_create_app, mock_uvicorn_run, debug_mode, expected_reload
):
    """デバッグモードパラメータのパラメータ化テスト"""
    mock_settings = Mock()
    mock_settings.openai_api_key = "test_api_key"
    mock_settings.debug = debug_mode
    mock_get_settings.return_value = mock_settings

    mock_app = Mock()
    mock_create_app.return_value = mock_app

    main()

    # reloadパラメータが期待通りの値で呼ばれることを確認
    mock_uvicorn_run.assert_called_once_with(
        mock_app, host="0.0.0.0", port=8000, reload=expected_reload
    )


@pytest.mark.parametrize("api_key", [None, "", "  ", "\t\n"])
@patch("src.main.uvicorn.run")
@patch("src.main.create_app")
@patch("src.main.sys.exit")
@patch("src.main.get_settings")
@patch("src.main.logger")
def test_main_invalid_api_keys_parametrized(
    mock_logger,
    mock_get_settings,
    mock_sys_exit,
    mock_create_app,
    mock_uvicorn_run,
    api_key,
):
    """様々な無効なAPIキーをパラメータ化テストで検証"""
    mock_settings = Mock()
    mock_settings.openai_api_key = api_key
    mock_get_settings.return_value = mock_settings

    # sys.exit()を実際に例外を投げるように設定
    mock_sys_exit.side_effect = SystemExit(1)

    with pytest.raises(SystemExit):
        main()

    # エラーログとsys.exitが呼ばれることを確認
    mock_logger.error.assert_called_with("OPENAI_API_KEY環境変数が設定されていません")
    mock_sys_exit.assert_called_once_with(1)

    # uvicorn.runが呼ばれないことを確認
    mock_uvicorn_run.assert_not_called()
