import pytest
from unittest.mock import Mock, patch
from langchain.schema import Document

from src.services.rag_service import RAGService
from src.models.schemas import ChatResponse
from src.config.settings import Settings


class TestRAGService:
    """RAGService クラスのテスト"""

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

    @patch("src.services.rag_service.EmbeddingService")
    @patch("src.services.rag_service.ChatOpenAI")
    @patch("src.services.rag_service.RAGService._initialize_vector_store")
    def test_init_successful(
        self, mock_init, mock_chat_openai, mock_embedding_service, mock_settings
    ):
        """正常な初期化をテスト"""
        mock_embedding_instance = Mock()
        mock_embedding_service.return_value = mock_embedding_instance

        mock_llm_instance = Mock()
        mock_chat_openai.return_value = mock_llm_instance

        service = RAGService(mock_settings)

        # EmbeddingServiceが正しく初期化されることを確認
        mock_embedding_service.assert_called_once_with("test/embedding-model")
        assert service.embedding_service == mock_embedding_instance

        # ChatOpenAIが正しく初期化されることを確認
        mock_chat_openai.assert_called_once_with(
            api_key="test_api_key", model="gpt-4o-mini", temperature=0.1
        )
        assert service.llm == mock_llm_instance

        # _initialize_vector_storeが呼ばれることを確認
        mock_init.assert_called_once()

        # 設定が保存されることを確認
        assert service.settings == mock_settings
        assert service.vector_store is None  # 初期化メソッドをモックしているため

    @patch("src.services.rag_service.EmbeddingService")
    @patch("src.services.rag_service.ChatOpenAI")
    @patch("os.path.exists")
    @patch("src.services.rag_service.Chroma")
    def test_initialize_vector_store_existing_directory(
        self,
        mock_chroma,
        mock_exists,
        mock_chat_openai,
        mock_embedding_service,
        mock_settings,
    ):
        """既存のベクトルストアディレクトリの場合の初期化をテスト"""
        # 既存ディレクトリのシミュレーション
        mock_exists.return_value = True

        mock_embedding_instance = Mock()
        mock_embedding_service.return_value = mock_embedding_instance

        mock_vector_store = Mock()
        mock_chroma.return_value = mock_vector_store

        service = RAGService(mock_settings)

        # Chromaが正しい引数で呼ばれることを確認
        mock_chroma.assert_called_once_with(
            persist_directory="test_data/chroma",
            embedding_function=mock_embedding_instance.embeddings,
        )

        # ベクトルストアが設定されることを確認
        assert service.vector_store == mock_vector_store

    @patch("src.services.rag_service.EmbeddingService")
    @patch("src.services.rag_service.ChatOpenAI")
    @patch("os.path.exists")
    @patch("src.services.rag_service.RAGService._create_vector_store")
    def test_initialize_vector_store_new_directory(
        self,
        mock_create,
        mock_exists,
        mock_chat_openai,
        mock_embedding_service,
        mock_settings,
    ):
        """新規ベクトルストアディレクトリの場合の初期化をテスト"""
        # 新規ディレクトリのシミュレーション
        mock_exists.return_value = False

        _service = RAGService(mock_settings)

        # _create_vector_storeが呼ばれることを確認
        mock_create.assert_called_once()

    @patch("src.services.rag_service.EmbeddingService")
    @patch("src.services.rag_service.ChatOpenAI")
    @patch("os.path.exists")
    @patch("src.services.rag_service.DocumentLoader")
    @patch("src.services.rag_service.Chroma")
    def test_create_vector_store(
        self,
        mock_chroma,
        mock_document_loader,
        mock_exists,
        mock_chat_openai,
        mock_embedding_service,
        mock_settings,
    ):
        """ベクトルストア作成をテスト"""
        mock_exists.return_value = False

        mock_embedding_instance = Mock()
        mock_embedding_service.return_value = mock_embedding_instance

        # DocumentLoaderのモック
        mock_loader_instance = Mock()
        mock_document_loader.return_value = mock_loader_instance

        test_documents = [
            Document(page_content="テスト内容1", metadata={"section": "セクション1"}),
            Document(page_content="テスト内容2", metadata={"section": "セクション2"}),
        ]
        mock_loader_instance.load_documents.return_value = test_documents

        # Chromaのモック
        mock_vector_store = Mock()
        mock_chroma.from_documents.return_value = mock_vector_store

        service = RAGService(mock_settings)

        # DocumentLoaderが正しく初期化されることを確認
        mock_document_loader.assert_called_once_with("test_spec.md", 500, 100)

        # load_documentsが呼ばれることを確認
        mock_loader_instance.load_documents.assert_called_once()

        # Chroma.from_documentsが正しく呼ばれることを確認
        mock_chroma.from_documents.assert_called_once_with(
            documents=test_documents,
            embedding=mock_embedding_instance.embeddings,
            persist_directory="test_data/chroma",
        )

        # persistが呼ばれることを確認
        mock_vector_store.persist.assert_called_once()

        # ベクトルストアが設定されることを確認
        assert service.vector_store == mock_vector_store

    @patch("src.services.rag_service.EmbeddingService")
    @patch("src.services.rag_service.ChatOpenAI")
    @patch("src.services.rag_service.RAGService._initialize_vector_store")
    def test_search_successful(
        self, mock_init, mock_chat_openai, mock_embedding_service, mock_settings
    ):
        """正常な検索をテスト"""
        service = RAGService(mock_settings)

        # モックベクトルストアを設定
        mock_vector_store = Mock()
        service.vector_store = mock_vector_store

        # 検索結果のモック
        test_documents = [
            (Document(page_content="内容1", metadata={"section": "セクション1"}), 0.8),
            (Document(page_content="内容2", metadata={"section": "セクション2"}), 0.6),
        ]
        mock_vector_store.similarity_search_with_score.return_value = test_documents

        result = service.search("テストクエリ", max_results=2)

        # similarity_search_with_scoreが正しく呼ばれることを確認
        mock_vector_store.similarity_search_with_score.assert_called_once_with(
            "テストクエリ", k=2
        )

        # 結果が正しくフィルタリングされることを確認（similarity_threshold=0.5）
        assert len(result) == 2
        assert result[0][1] == 0.8  # スコアが0.5以上
        assert result[1][1] == 0.6  # スコアが0.5以上

    @patch("src.services.rag_service.EmbeddingService")
    @patch("src.services.rag_service.ChatOpenAI")
    @patch("src.services.rag_service.RAGService._initialize_vector_store")
    def test_search_with_threshold_filtering(
        self, mock_init, mock_chat_openai, mock_embedding_service, mock_settings
    ):
        """類似度しきい値でのフィルタリングをテスト"""
        service = RAGService(mock_settings)

        mock_vector_store = Mock()
        service.vector_store = mock_vector_store

        # しきい値以下の結果を含む検索結果
        test_documents = [
            (Document(page_content="内容1", metadata={"section": "セクション1"}), 0.8),
            (
                Document(page_content="内容2", metadata={"section": "セクション2"}),
                0.3,
            ),  # しきい値以下
        ]
        mock_vector_store.similarity_search_with_score.return_value = test_documents

        result = service.search("テストクエリ")

        # しきい値以上の結果のみが返されることを確認
        assert len(result) == 1
        assert result[0][1] == 0.8

    @patch("src.services.rag_service.EmbeddingService")
    @patch("src.services.rag_service.ChatOpenAI")
    @patch("src.services.rag_service.RAGService._initialize_vector_store")
    def test_search_vector_store_not_initialized(
        self, mock_init, mock_chat_openai, mock_embedding_service, mock_settings
    ):
        """ベクトルストアが初期化されていない場合のエラーをテスト"""
        service = RAGService(mock_settings)
        service.vector_store = None

        with pytest.raises(ValueError) as exc_info:
            service.search("テストクエリ")

        assert "ベクトルストアが初期化されていません" in str(exc_info.value)

    @patch("src.services.rag_service.EmbeddingService")
    @patch("src.services.rag_service.ChatOpenAI")
    @patch("src.services.rag_service.RAGService._initialize_vector_store")
    @patch("src.services.rag_service.LLMChain")
    def test_generate_answer(
        self,
        mock_llm_chain,
        mock_init,
        mock_chat_openai,
        mock_embedding_service,
        mock_settings,
    ):
        """回答生成をテスト"""
        service = RAGService(mock_settings)

        # テストドキュメント
        test_documents = [
            Document(page_content="テスト内容1", metadata={"section": "セクション1"}),
            Document(page_content="テスト内容2", metadata={"section": "セクション2"}),
        ]

        # LLMChainのモック
        mock_chain_instance = Mock()
        mock_llm_chain.return_value = mock_chain_instance
        mock_chain_instance.run.return_value = "生成された回答です。"

        result = service.generate_answer("テスト質問", test_documents)

        # LLMChainが正しく初期化されることを確認
        mock_llm_chain.assert_called_once()

        # runメソッドが正しい引数で呼ばれることを確認
        mock_chain_instance.run.assert_called_once()
        call_args = mock_chain_instance.run.call_args[1]

        assert "question" in call_args
        assert call_args["question"] == "テスト質問"
        assert "context" in call_args
        assert "【セクション1】" in call_args["context"]
        assert "【セクション2】" in call_args["context"]

        # 結果が正しいことを確認
        assert result == "生成された回答です。"

    @patch("src.services.rag_service.EmbeddingService")
    @patch("src.services.rag_service.ChatOpenAI")
    @patch("src.services.rag_service.RAGService._initialize_vector_store")
    @patch("src.services.rag_service.LLMChain")
    def test_generate_answer_long_context(
        self,
        mock_llm_chain,
        mock_init,
        mock_chat_openai,
        mock_embedding_service,
        mock_settings,
    ):
        """長いコンテキストの切り詰めをテスト"""
        service = RAGService(mock_settings)

        # 長いドキュメント（max_context_lengthを超える）
        long_content = "A" * 3000  # max_context_length=2000より大きい
        test_documents = [
            Document(page_content=long_content, metadata={"section": "長いセクション"}),
        ]

        mock_chain_instance = Mock()
        mock_llm_chain.return_value = mock_chain_instance
        mock_chain_instance.run.return_value = "切り詰められた回答"

        _result = service.generate_answer("質問", test_documents)

        # runメソッドが呼ばれることを確認
        mock_chain_instance.run.assert_called_once()
        call_args = mock_chain_instance.run.call_args[1]

        # コンテキストが切り詰められていることを確認
        context = call_args["context"]
        assert len(context) <= 2000 + 3  # "..."を含む
        assert context.endswith("...")

    @patch("src.services.rag_service.EmbeddingService")
    @patch("src.services.rag_service.ChatOpenAI")
    @patch("src.services.rag_service.DatabaseManager")
    @patch("src.services.rag_service.SessionService")
    @patch("src.services.rag_service.RAGService._initialize_vector_store")
    def test_chat_successful(
        self,
        mock_init,
        mock_session_service_class,
        mock_db_manager,
        mock_chat_openai,
        mock_embedding_service,
        mock_settings,
    ):
        """正常なチャット処理をテスト"""
        # SessionServiceのモック
        mock_session_service = Mock()
        mock_session_service_class.return_value = mock_session_service
        mock_session_service.create_session.return_value = {"id": "test-session-id"}
        mock_session_service.get_conversation_history.return_value = []
        mock_session_service.add_message.return_value = {"id": "msg-1"}

        service = RAGService(mock_settings)

        # searchメソッドのモック
        test_search_results = [
            (
                Document(
                    page_content="テスト内容1", metadata={"section": "セクション1"}
                ),
                0.8,
            ),
            (
                Document(
                    page_content="テスト内容2", metadata={"section": "セクション2"}
                ),
                0.6,
            ),
        ]

        with patch.object(service, "search") as mock_search:
            mock_search.return_value = test_search_results

            with patch.object(service, "generate_answer") as mock_generate:
                mock_generate.return_value = "生成された回答です。"

                result = service.chat("テスト質問", max_results=2)

        # searchが正しく呼ばれることを確認
        mock_search.assert_called_once_with("テスト質問", 2)

        # generate_answerが正しく呼ばれることを確認
        mock_generate.assert_called_once()

        # 結果がChatResponseオブジェクトであることを確認
        assert isinstance(result, ChatResponse)
        assert result.answer == "生成された回答です。"
        assert len(result.sources) == 2

        # ソース情報が正しく設定されることを確認
        assert result.sources[0].section == "セクション1"
        assert result.sources[1].section == "セクション2"

        # 信頼度スコアが正しく計算されることを確認
        expected_confidence = 1.0 - 0.8  # 最高スコアから計算
        assert result.confidence == expected_confidence

    @patch("src.services.rag_service.EmbeddingService")
    @patch("src.services.rag_service.ChatOpenAI")
    @patch("src.services.rag_service.DatabaseManager")
    @patch("src.services.rag_service.SessionService")
    @patch("src.services.rag_service.RAGService._initialize_vector_store")
    def test_chat_no_results(
        self,
        mock_init,
        mock_session_service_class,
        mock_db_manager,
        mock_chat_openai,
        mock_embedding_service,
        mock_settings,
    ):
        """検索結果がない場合のチャット処理をテスト"""
        # SessionServiceのモック
        mock_session_service = Mock()
        mock_session_service_class.return_value = mock_session_service
        mock_session_service.create_session.return_value = {"id": "test-session-id"}
        mock_session_service.get_conversation_history.return_value = []
        mock_session_service.add_message.return_value = {"id": "msg-1"}

        service = RAGService(mock_settings)

        with patch.object(service, "search") as mock_search:
            mock_search.return_value = []

            result = service.chat("見つからない質問")

        # 結果がChatResponseオブジェクトであることを確認
        assert isinstance(result, ChatResponse)
        assert "情報が仕様書内で見つかりませんでした" in result.answer
        assert len(result.sources) == 0
        assert result.confidence == 0.0

    @patch("src.services.rag_service.EmbeddingService")
    @patch("src.services.rag_service.ChatOpenAI")
    @patch("src.services.rag_service.DatabaseManager")
    @patch("src.services.rag_service.SessionService")
    @patch("src.services.rag_service.RAGService._initialize_vector_store")
    def test_chat_with_truncated_source_content(
        self,
        mock_init,
        mock_session_service_class,
        mock_db_manager,
        mock_chat_openai,
        mock_embedding_service,
        mock_settings,
    ):
        """長いソース内容の切り詰めをテスト"""
        # SessionServiceのモック
        mock_session_service = Mock()
        mock_session_service_class.return_value = mock_session_service
        mock_session_service.create_session.return_value = {"id": "test-session-id"}
        mock_session_service.get_conversation_history.return_value = []
        mock_session_service.add_message.return_value = {"id": "msg-1"}

        service = RAGService(mock_settings)

        # 長い内容のドキュメント
        long_content = "A" * 500  # 300文字制限を超える
        test_search_results = [
            (
                Document(
                    page_content=long_content, metadata={"section": "長いセクション"}
                ),
                0.8,
            ),
        ]

        with patch.object(service, "search") as mock_search:
            mock_search.return_value = test_search_results

            with patch.object(service, "generate_answer") as mock_generate:
                mock_generate.return_value = "回答"

                result = service.chat("質問")

        # ソース内容が切り詰められていることを確認
        assert len(result.sources) == 1
        source_content = result.sources[0].content
        assert len(source_content) <= 300 + 3  # "..."を含む
        assert source_content.endswith("...")

    @patch("src.services.rag_service.EmbeddingService")
    @patch("src.services.rag_service.ChatOpenAI")
    @patch("src.services.rag_service.RAGService._initialize_vector_store")
    def test_is_ready_true(
        self, mock_init, mock_chat_openai, mock_embedding_service, mock_settings
    ):
        """ベクトルストアが準備できている場合のis_readyをテスト"""
        service = RAGService(mock_settings)
        service.vector_store = Mock()  # モックベクトルストアを設定

        assert service.is_ready() is True

    @patch("src.services.rag_service.EmbeddingService")
    @patch("src.services.rag_service.ChatOpenAI")
    @patch("src.services.rag_service.RAGService._initialize_vector_store")
    def test_is_ready_false(
        self, mock_init, mock_chat_openai, mock_embedding_service, mock_settings
    ):
        """ベクトルストアが準備できていない場合のis_readyをテスト"""
        service = RAGService(mock_settings)
        service.vector_store = None

        assert service.is_ready() is False


@pytest.mark.parametrize("max_results", [1, 2, 3, 5, 10])
@patch("src.services.rag_service.EmbeddingService")
@patch("src.services.rag_service.ChatOpenAI")
@patch("src.services.rag_service.RAGService._initialize_vector_store")
def test_search_max_results_parameter(
    mock_init, mock_chat_openai, mock_embedding_service, max_results
):
    """異なるmax_results値での検索をパラメータ化テストで検証"""
    # テスト用設定を作成
    mock_settings = Settings(
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

    service = RAGService(mock_settings)

    mock_vector_store = Mock()
    service.vector_store = mock_vector_store

    # max_results分のテストドキュメントを生成
    test_documents = [
        (Document(page_content=f"内容{i}", metadata={"section": f"セクション{i}"}), 0.8)
        for i in range(max_results)
    ]
    mock_vector_store.similarity_search_with_score.return_value = test_documents

    result = service.search("テストクエリ", max_results=max_results)

    # similarity_search_with_scoreが正しいk値で呼ばれることを確認
    mock_vector_store.similarity_search_with_score.assert_called_once_with(
        "テストクエリ", k=max_results
    )

    # 結果の数が正しいことを確認
    assert len(result) == max_results


@pytest.mark.parametrize("similarity_threshold", [0.0, 0.3, 0.5, 0.7, 1.0])
@patch("src.services.rag_service.EmbeddingService")
@patch("src.services.rag_service.ChatOpenAI")
@patch("src.services.rag_service.RAGService._initialize_vector_store")
def test_search_similarity_threshold_filtering(
    mock_init, mock_chat_openai, mock_embedding_service, similarity_threshold
):
    """異なる類似度しきい値でのフィルタリングをパラメータ化テストで検証"""
    # テスト用設定を作成（similarity_thresholdを変更）
    mock_settings = Settings(
        openai_api_key="test_api_key",
        openai_model="gpt-4o-mini",
        openai_temperature=0.1,
        chroma_persist_directory="test_data/chroma",
        embedding_model_name="test/embedding-model",
        spec_file_path="test_spec.md",
        chunk_size=500,
        chunk_overlap=100,
        max_context_length=2000,
        similarity_threshold=similarity_threshold,
    )

    service = RAGService(mock_settings)

    mock_vector_store = Mock()
    service.vector_store = mock_vector_store

    # 様々なスコアのテストドキュメント
    test_documents = [
        (Document(page_content="内容1", metadata={"section": "セクション1"}), 0.9),
        (Document(page_content="内容2", metadata={"section": "セクション2"}), 0.6),
        (Document(page_content="内容3", metadata={"section": "セクション3"}), 0.3),
        (Document(page_content="内容4", metadata={"section": "セクション4"}), 0.1),
    ]
    mock_vector_store.similarity_search_with_score.return_value = test_documents

    result = service.search("テストクエリ")

    # しきい値以上の結果のみが返されることを確認
    for doc, score in result:
        assert score >= similarity_threshold
