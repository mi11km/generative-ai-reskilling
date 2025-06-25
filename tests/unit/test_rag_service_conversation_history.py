import pytest
from unittest.mock import Mock, patch
from langchain.schema import Document

from src.services.rag_service import RAGService
from src.config.settings import Settings


class TestRAGServiceConversationHistory:
    """RAGServiceの会話履歴機能のテスト"""

    @pytest.fixture
    def mock_settings(self):
        """テスト用のSettings オブジェクト"""
        return Settings(
            openai_api_key="test_api_key",
            openai_model="gpt-4o-mini",
            openai_temperature=0.1,
            chroma_persist_directory="test_data/chroma",
            embedding_model_name="test/embedding-model",
            spec_file_path="test_spec.md",
            chunk_size=500,
            chunk_overlap=100,
            max_context_length=2000,
            similarity_threshold=0.5,
        )

    @pytest.fixture
    def mock_dependencies(self, mock_settings):
        """依存関係のモックを設定"""
        with (
            patch(
                "src.services.rag_service.EmbeddingService"
            ) as mock_embedding_service,
            patch("src.services.rag_service.ChatOpenAI") as mock_chat_openai,
            patch("src.services.rag_service.DatabaseManager") as mock_db_manager,
            patch(
                "src.services.rag_service.SessionService"
            ) as mock_session_service_class,
            patch("src.services.rag_service.RAGService._initialize_vector_store"),
        ):
            # モックインスタンスの作成
            mock_embedding_instance = Mock()
            mock_embedding_service.return_value = mock_embedding_instance

            mock_llm_instance = Mock()
            mock_chat_openai.return_value = mock_llm_instance

            mock_db_instance = Mock()
            mock_db_manager.return_value = mock_db_instance

            mock_session_service = Mock()
            mock_session_service_class.return_value = mock_session_service

            service = RAGService(mock_settings)

            # vector_storeを設定
            service.vector_store = Mock()

            yield {
                "service": service,
                "session_service": mock_session_service,
                "llm": mock_llm_instance,
                "embedding_service": mock_embedding_instance,
            }

    def test_chat_with_new_session(self, mock_dependencies):
        """新規セッションでのチャット処理をテスト"""
        service = mock_dependencies["service"]
        session_service = mock_dependencies["session_service"]

        # 新規セッション作成のモック
        session_service.create_session.return_value = {"id": "new-session-id"}
        session_service.get_conversation_history.return_value = []
        session_service.add_message.return_value = {"id": "msg-1"}

        # 検索結果のモック
        test_search_results = [
            (
                Document(page_content="テスト内容", metadata={"section": "セクション"}),
                0.8,
            )
        ]

        with patch.object(service, "search") as mock_search:
            mock_search.return_value = test_search_results

            with patch.object(service, "generate_answer") as mock_generate:
                mock_generate.return_value = "生成された回答"

                result = service.chat("初回の質問")

        # 新規セッションが作成されたことを確認
        session_service.create_session.assert_called_once()

        # 会話履歴が取得されたことを確認（新規なので空）
        session_service.get_conversation_history.assert_called_once_with(
            "new-session-id", limit=20
        )

        # generate_answerが呼ばれたことを確認（履歴がないので通常の生成）
        mock_generate.assert_called_once()

        # 結果が正しいことを確認
        assert result.session_id == "new-session-id"
        assert result.answer == "生成された回答"

    def test_chat_with_existing_session_and_history(self, mock_dependencies):
        """既存セッションと会話履歴がある場合のチャット処理をテスト"""
        service = mock_dependencies["service"]
        session_service = mock_dependencies["session_service"]

        # 既存の会話履歴
        conversation_history = [
            {"role": "user", "content": "前回の質問"},
            {"role": "assistant", "content": "前回の回答"},
        ]

        session_service.get_conversation_history.return_value = conversation_history
        session_service.add_message.return_value = {"id": "msg-3"}

        # 検索結果のモック
        test_search_results = [
            (
                Document(page_content="テスト内容", metadata={"section": "セクション"}),
                0.8,
            )
        ]

        with patch.object(service, "search") as mock_search:
            mock_search.return_value = test_search_results

            with patch.object(
                service, "generate_answer_with_history"
            ) as mock_generate_history:
                mock_generate_history.return_value = "履歴を考慮した回答"

                result = service.chat(
                    "フォローアップの質問", session_id="existing-session"
                )

        # 会話履歴が取得されたことを確認
        session_service.get_conversation_history.assert_called_once_with(
            "existing-session", limit=20
        )

        # generate_answer_with_historyが呼ばれたことを確認
        mock_generate_history.assert_called_once()
        call_args = mock_generate_history.call_args[0]
        assert call_args[0] == "フォローアップの質問"
        assert call_args[2] == conversation_history  # 履歴全体が渡される

        # 結果が正しいことを確認
        assert result.session_id == "existing-session"
        assert result.answer == "履歴を考慮した回答"

    def test_chat_with_session_not_found(self, mock_dependencies):
        """セッションが見つからない場合の処理をテスト"""
        service = mock_dependencies["service"]
        session_service = mock_dependencies["session_service"]

        # 最初のadd_messageがNoneを返す（セッション不在）
        session_service.add_message.side_effect = [
            None,
            {"id": "msg-1"},
            {"id": "msg-2"},
        ]  # 3回目の呼び出し用も追加
        session_service.create_session.return_value = {"id": "new-session-id"}
        session_service.get_conversation_history.return_value = []

        # 検索結果のモック
        test_search_results = [
            (
                Document(page_content="テスト内容", metadata={"section": "セクション"}),
                0.8,
            )
        ]

        with patch.object(service, "search") as mock_search:
            mock_search.return_value = test_search_results

            with patch.object(service, "generate_answer") as mock_generate:
                mock_generate.return_value = "生成された回答"

                result = service.chat("質問", session_id="invalid-session")

        # 新規セッションが作成されたことを確認
        session_service.create_session.assert_called_once()

        # add_messageが3回呼ばれたことを確認（1回目失敗、2回目成功、3回目アシスタントメッセージ）
        assert session_service.add_message.call_count == 3

        # 結果が正しいことを確認
        assert result.session_id == "new-session-id"

    def test_generate_answer_with_history(self, mock_dependencies):
        """会話履歴を考慮した回答生成のテスト"""
        service = mock_dependencies["service"]

        # テストデータ
        query = "現在の質問"
        context_documents = [
            Document(page_content="関連情報1", metadata={"section": "セクション1"}),
            Document(page_content="関連情報2", metadata={"section": "セクション2"}),
        ]
        conversation_history = [
            {"role": "user", "content": "前回の質問"},
            {"role": "assistant", "content": "前回の回答"},
            {"role": "user", "content": "さらに前の質問"},
            {"role": "assistant", "content": "さらに前の回答"},
        ]

        # LLMChainのモック
        with patch("src.services.rag_service.LLMChain") as mock_llm_chain:
            mock_chain_instance = Mock()
            mock_llm_chain.return_value = mock_chain_instance
            mock_chain_instance.run.return_value = "履歴を考慮した回答です。"

            result = service.generate_answer_with_history(
                query, context_documents, conversation_history
            )

        # LLMChainのrunが呼ばれたことを確認
        mock_chain_instance.run.assert_called_once()
        call_args = mock_chain_instance.run.call_args[1]

        # 質問が正しく渡されていることを確認
        assert call_args["question"] == query

        # コンテキストに関連情報が含まれていることを確認
        assert "【セクション1】" in call_args["context"]
        assert "関連情報1" in call_args["context"]

        # 結果が正しいことを確認
        assert result == "履歴を考慮した回答です。"

    def test_generate_answer_with_long_history(self, mock_dependencies):
        """長い会話履歴の処理をテスト（最新10件のみ使用）"""
        service = mock_dependencies["service"]

        # 20件の会話履歴を作成
        conversation_history = []
        for i in range(20):
            conversation_history.append({"role": "user", "content": f"質問{i}"})
            conversation_history.append({"role": "assistant", "content": f"回答{i}"})

        query = "現在の質問"
        context_documents = [
            Document(page_content="関連情報", metadata={"section": "セクション"})
        ]

        # システムプロンプトをキャプチャするための変数
        captured_system_prompt = None

        # ChatPromptTemplateのモック
        with patch(
            "src.services.rag_service.ChatPromptTemplate"
        ) as mock_prompt_template:
            # from_messagesをモック
            def capture_messages(messages):
                nonlocal captured_system_prompt
                captured_system_prompt = messages[0][
                    1
                ]  # システムプロンプトをキャプチャ
                return Mock()

            mock_prompt_template.from_messages.side_effect = capture_messages

            # LLMChainのモック
            with patch("src.services.rag_service.LLMChain") as mock_llm_chain:
                mock_chain_instance = Mock()
                mock_llm_chain.return_value = mock_chain_instance
                mock_chain_instance.run.return_value = "回答"

                service.generate_answer_with_history(
                    query, context_documents, conversation_history
                )

        # システムプロンプトが正しくキャプチャされたことを確認
        assert captured_system_prompt is not None

        # 最新10件の履歴のみが含まれることを確認
        # 40件の履歴があるので、最後の10件は30-39のインデックス
        assert "質問19" in captured_system_prompt  # 最新の質問
        assert "質問15" in captured_system_prompt  # 10件前の質問
        assert "質問14" not in captured_system_prompt  # 11件前の質問は含まれない

    def test_chat_conversation_flow(self, mock_dependencies):
        """実際の会話フローをシミュレートしたテスト"""
        service = mock_dependencies["service"]
        session_service = mock_dependencies["session_service"]

        # セッションIDを固定
        session_id = "test-session-id"

        # 1回目の質問（新規セッション）
        session_service.create_session.return_value = {"id": session_id}
        session_service.get_conversation_history.return_value = []
        session_service.add_message.return_value = {"id": "msg-1"}

        test_search_results = [
            (
                Document(
                    page_content="ゲームの基本ルール", metadata={"section": "ルール"}
                ),
                0.9,
            )
        ]

        with patch.object(service, "search") as mock_search:
            mock_search.return_value = test_search_results

            with patch.object(service, "generate_answer") as mock_generate:
                mock_generate.return_value = "ゲームの基本ルールは..."

                result1 = service.chat("ゲームのルールを教えて")

        assert result1.session_id == session_id
        assert result1.answer == "ゲームの基本ルールは..."

        # 2回目の質問（履歴あり）
        conversation_history = [
            {"role": "user", "content": "ゲームのルールを教えて"},
            {"role": "assistant", "content": "ゲームの基本ルールは..."},
        ]
        session_service.get_conversation_history.return_value = conversation_history
        session_service.add_message.return_value = {"id": "msg-3"}

        test_search_results2 = [
            (
                Document(
                    page_content="勝利条件の詳細", metadata={"section": "勝利条件"}
                ),
                0.85,
            )
        ]

        with patch.object(service, "search") as mock_search:
            mock_search.return_value = test_search_results2

            with patch.object(
                service, "generate_answer_with_history"
            ) as mock_generate_history:
                mock_generate_history.return_value = (
                    "先ほど説明したルールに加えて、勝利条件は..."
                )

                result2 = service.chat(
                    "勝利条件についてもう少し詳しく", session_id=session_id
                )

        # 会話履歴が正しく取得されたことを確認
        assert session_service.get_conversation_history.call_count == 2

        # generate_answer_with_historyが履歴付きで呼ばれたことを確認
        mock_generate_history.assert_called_once()
        call_args = mock_generate_history.call_args[0]
        assert call_args[2] == conversation_history

        assert result2.session_id == session_id
        assert "先ほど説明したルールに加えて" in result2.answer
