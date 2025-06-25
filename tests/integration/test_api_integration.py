import pytest
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient

from src.main import create_app
from src.models.schemas import ChatResponse, SourceDocument


@pytest.mark.integration
class TestAPIIntegration:
    """API統合テスト"""
    
    @pytest.fixture
    def app(self):
        """統合テスト用のFastAPIアプリケーション"""
        with patch("src.main.get_settings") as mock_get_settings:
            mock_settings = Mock()
            mock_settings.app_name = "Test Game RAG API"
            mock_settings.version = "0.1.0"
            mock_settings.debug = True
            mock_get_settings.return_value = mock_settings
            
            app = create_app()
            return app
    
    @pytest.fixture
    def client(self, app):
        """統合テスト用のHTTPクライアント"""
        return TestClient(app)
    
    def test_full_chat_api_flow(self, app, client):
        """完全なチャットAPIフローの統合テスト"""
        from src.api.chat import get_rag_service
        
        # RAGサービスのモック
        mock_rag_service = Mock()
        
        # チャットレスポンスのモック
        mock_response = ChatResponse(
            answer="スゲリス・サーガは冒険RPGゲームです。プレイヤーは勇者となり、魔王を倒すことが最終目標となります。",
            sources=[
                SourceDocument(
                    content="スゲリス・サーガは、ファンタジー世界を舞台とした冒険RPGゲームです。",
                    section="## **1. ゲーム概要**",
                    metadata={"score": 0.92}
                ),
                SourceDocument(
                    content="プレイヤーは勇者となり、魔王を倒すことが最終目標となります。",
                    section="## **1. ゲーム概要**",
                    metadata={"score": 0.85}
                )
            ],
            confidence=0.88
        )
        mock_rag_service.chat.return_value = mock_response
        
        # FastAPIの依存関係をオーバーライド
        app.dependency_overrides[get_rag_service] = lambda: mock_rag_service
        
        try:
            # APIリクエスト実行
            response = client.post("/api/v1/chat", json={
                "question": "スゲリス・サーガとはどのようなゲームですか？",
                "max_results": 3
            })
            
            # レスポンス検証
            assert response.status_code == 200
            
            data = response.json()
            assert "answer" in data
            assert "sources" in data
            assert "confidence" in data
            
            # 回答内容の検証（モックされた値で確認）
            assert data["answer"] == "スゲリス・サーガは冒険RPGゲームです。プレイヤーは勇者となり、魔王を倒すことが最終目標となります。"
            
            # ソース情報の検証
            assert len(data["sources"]) == 2
            for source in data["sources"]:
                assert "content" in source
                assert "section" in source
                assert "metadata" in source
                assert "score" in source["metadata"]
            
            # 信頼度の検証
            assert 0.0 <= data["confidence"] <= 1.0
            assert data["confidence"] == 0.88
            
            # RAGサービスが正しく呼ばれたことを確認
            mock_rag_service.chat.assert_called_once_with(
                "スゲリス・サーガとはどのようなゲームですか？", 
                3
            )
        finally:
            # 依存関係のオーバーライドをクリア
            app.dependency_overrides.clear()
    
    def test_health_check_integration(self, app, client):
        """ヘルスチェックAPIの統合テスト"""
        from src.api.chat import get_rag_service
        
        # RAGサービスのモック
        mock_rag_service = Mock()
        mock_rag_service.is_ready.return_value = True
        
        # FastAPIの依存関係をオーバーライド
        app.dependency_overrides[get_rag_service] = lambda: mock_rag_service
        
        try:
            # ヘルスチェックリクエスト実行
            response = client.get("/api/v1/health")
            
            # レスポンス検証
            assert response.status_code == 200
            
            data = response.json()
            assert "status" in data
            assert "version" in data
            assert "vector_store_ready" in data
            
            assert data["status"] == "healthy"
            assert data["version"] == "0.1.0"
            assert data["vector_store_ready"] is True
        finally:
            # 依存関係のオーバーライドをクリア
            app.dependency_overrides.clear()
    
    def test_root_endpoint_integration(self, client):
        """ルートエンドポイントの統合テスト"""
        response = client.get("/")
        
        assert response.status_code == 200
        
        data = response.json()
        assert data["message"] == "Game Specification RAG API"
        assert data["version"] == "0.1.0"
        assert data["docs"] == "/docs"
    
    def test_chat_api_error_handling_integration(self, app, client):
        """チャットAPIエラーハンドリングの統合テスト"""
        from src.api.chat import get_rag_service
        
        # RAGサービスで例外が発生する場合
        mock_rag_service = Mock()
        mock_rag_service.chat.side_effect = Exception("RAGサービスエラー")
        
        # FastAPIの依存関係をオーバーライド
        app.dependency_overrides[get_rag_service] = lambda: mock_rag_service
        
        try:
            response = client.post("/api/v1/chat", json={
                "question": "テスト質問"
            })
            
            # エラーレスポンスの確認
            assert response.status_code == 500
            data = response.json()
            assert "detail" in data
            assert "内部サーバーエラーが発生しました" in data["detail"]
        finally:
            # 依存関係のオーバーライドをクリア
            app.dependency_overrides.clear()
    
    def test_chat_api_validation_integration(self, client):
        """チャットAPIバリデーションの統合テスト"""
        # 無効なリクエスト（質問なし）
        response = client.post("/api/v1/chat", json={
            "max_results": 3
        })
        assert response.status_code == 422
        
        # 無効なリクエスト（max_results範囲外）
        response = client.post("/api/v1/chat", json={
            "question": "テスト質問",
            "max_results": 15
        })
        assert response.status_code == 422
        
        # 無効なリクエスト（空の質問）
        response = client.post("/api/v1/chat", json={
            "question": "",
            "max_results": 3
        })
        assert response.status_code == 422
    
    def test_multiple_concurrent_requests_integration(self, app, client):
        """複数の同時リクエストの統合テスト"""
        import threading
        import time
        from src.api.chat import get_rag_service
        
        # RAGサービスのモック
        mock_rag_service = Mock()
        
        def mock_chat_response(question, max_results):
            # 少し遅延を追加してコンカレンシーをテスト
            time.sleep(0.1)
            return ChatResponse(
                answer=f"回答: {question}",
                sources=[],
                confidence=0.5
            )
        
        mock_rag_service.chat.side_effect = mock_chat_response
        
        # FastAPIの依存関係をオーバーライド
        app.dependency_overrides[get_rag_service] = lambda: mock_rag_service
        
        # 複数のリクエストを同時実行
        def make_request(question_id):
            response = client.post("/api/v1/chat", json={
                "question": f"テスト質問{question_id}"
            })
            return response.status_code, response.json()
        
        # 5つの同時リクエスト
        threads = []
        results = {}
        
        def thread_worker(question_id):
            results[question_id] = make_request(question_id)
        
        for i in range(5):
            thread = threading.Thread(target=thread_worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # すべてのスレッドの完了を待機
        for thread in threads:
            thread.join()
        
        # 結果の検証
        assert len(results) == 5
        for question_id, (status_code, data) in results.items():
            assert status_code == 200
            assert "answer" in data
            assert f"テスト質問{question_id}" in data["answer"]
        
        # 依存関係のオーバーライドをクリア
        app.dependency_overrides.clear()
    
    def test_japanese_content_integration(self, app, client):
        """日本語コンテンツの統合テスト"""
        from src.api.chat import get_rag_service
        
        # RAGサービスのモック
        mock_rag_service = Mock()
        
        japanese_response = ChatResponse(
            answer="ターン制バトルシステムでは、プレイヤーと敵が交互に行動します。各ターンでプレイヤーは攻撃、防御、スキル使用などのアクションを選択できます。",
            sources=[
                SourceDocument(
                    content="ターン制バトルシステムを採用しています。",
                    section="### **1.1 基本システム**",
                    metadata={"score": 0.89}
                )
            ],
            confidence=0.78
        )
        mock_rag_service.chat.return_value = japanese_response
        
        # FastAPIの依存関係をオーバーライド
        app.dependency_overrides[get_rag_service] = lambda: mock_rag_service
        
        try:
            # 日本語でのAPIリクエスト
            response = client.post("/api/v1/chat", json={
                "question": "バトルシステムの仕組みについて詳しく教えてください。",
                "max_results": 2
            })
            
            # レスポンス検証
            assert response.status_code == 200
            
            data = response.json()
            assert "ターン制バトル" in data["answer"]
            assert len(data["sources"]) == 1
            assert "### **1.1 基本システム**" in data["sources"][0]["section"]
        finally:
            # 依存関係のオーバーライドをクリア
            app.dependency_overrides.clear()
    
    def test_no_results_scenario_integration(self, app, client):
        """検索結果がない場合のシナリオ統合テスト"""
        from src.api.chat import get_rag_service
        
        # RAGサービスのモック
        mock_rag_service = Mock()
        
        no_results_response = ChatResponse(
            answer="申し訳ございません。お尋ねの内容に関する情報が仕様書内で見つかりませんでした。",
            sources=[],
            confidence=0.0
        )
        mock_rag_service.chat.return_value = no_results_response
        
        # FastAPIの依存関係をオーバーライド
        app.dependency_overrides[get_rag_service] = lambda: mock_rag_service
        
        try:
            # 見つからない内容でのリクエスト
            response = client.post("/api/v1/chat", json={
                "question": "存在しない機能についての質問"
            })
            
            # レスポンス検証
            assert response.status_code == 200
            
            data = response.json()
            assert "見つかりませんでした" in data["answer"]
            assert len(data["sources"]) == 0
            assert data["confidence"] == 0.0
        finally:
            # 依存関係のオーバーライドをクリア
            app.dependency_overrides.clear()
    
    def test_large_response_handling_integration(self, app, client):
        """大きなレスポンスの処理統合テスト"""
        from src.api.chat import get_rag_service
        
        # RAGサービスのモック
        mock_rag_service = Mock()
        
        # 大きな回答とソースを生成
        large_answer = "詳細な回答です。" * 100
        large_sources = [
            SourceDocument(
                content=f"大容量コンテンツ{i}: " + "内容" * 50,
                section=f"セクション{i}",
                metadata={"score": 0.8 - i * 0.1}
            )
            for i in range(5)
        ]
        
        large_response = ChatResponse(
            answer=large_answer,
            sources=large_sources,
            confidence=0.75
        )
        mock_rag_service.chat.return_value = large_response
        
        # FastAPIの依存関係をオーバーライド
        app.dependency_overrides[get_rag_service] = lambda: mock_rag_service
        
        try:
            # リクエスト実行
            response = client.post("/api/v1/chat", json={
                "question": "詳細な情報を教えて",
                "max_results": 5
            })
            
            # レスポンス検証
            assert response.status_code == 200
            
            data = response.json()
            assert len(data["answer"]) > 1000  # 大きな回答
            assert len(data["sources"]) == 5
            
            # 各ソースが適切に構造化されていることを確認
            for i, source in enumerate(data["sources"]):
                assert f"セクション{i}" in source["section"]
                assert "score" in source["metadata"]
        finally:
            # 依存関係のオーバーライドをクリア
            app.dependency_overrides.clear()


@pytest.mark.integration
class TestAPIWithRealDependencies:
    """実際の依存関係を使用した統合テスト"""
    
    @pytest.fixture
    def app_with_real_dependencies(self):
        """実際の依存関係を使用するアプリケーション"""
        # 注意: これらのテストは実際のOpenAI APIキーが必要
        # 通常はCI/CDパイプラインでスキップされる
        with patch("src.main.get_settings") as mock_get_settings:
            mock_settings = Mock()
            mock_settings.app_name = "Integration Test API"
            mock_settings.version = "0.1.0"
            mock_settings.openai_api_key = "test_key"  # 実際のテストでは環境変数から取得
            mock_settings.debug = True
            mock_get_settings.return_value = mock_settings
            
            app = create_app()
            return app
    
    @pytest.mark.skip(reason="実際の依存関係を使用するテストは手動実行のみ")
    def test_full_stack_integration(self, app_with_real_dependencies):
        """フルスタック統合テスト（実際の依存関係使用）"""
        # このテストは実際のOpenAI APIやHugging Face モデルを使用
        # 通常は手動実行またはE2Eテスト環境でのみ実行
        client = TestClient(app_with_real_dependencies)
        
        # 実際のAPIコールをテスト
        response = client.post("/api/v1/chat", json={
            "question": "ゲーム概要について教えて"
        })
        
        # 基本的なレスポンス構造のみを確認
        # （実際の内容は外部サービスに依存するため）
        assert response.status_code in [200, 500]  # 設定エラーの場合は500も許可


# テスト設定は削除（統合テストファイルではpytest設定を直接定義しない）