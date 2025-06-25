import os
import tempfile
import pytest
from unittest.mock import patch, Mock
from langchain.schema import Document

from src.services.rag_service import RAGService
from src.services.document_loader import DocumentLoader
from src.models.schemas import ChatResponse
from src.config.settings import Settings


@pytest.mark.integration
class TestFullRAGPipeline:
    """完全なRAGパイプラインの統合テスト"""

    @pytest.fixture
    def integration_settings(self, temp_dir):
        """統合テスト用の設定"""
        return Settings(
            openai_api_key="test_api_key",
            openai_model="gpt-4o-mini",
            openai_temperature=0.1,
            chroma_persist_directory=os.path.join(temp_dir, "chroma"),
            embedding_model_name="test/embedding-model",
            spec_file_path="tests/fixtures/test_spec.md",
            chunk_size=200,
            chunk_overlap=50,
            max_context_length=1000,
            similarity_threshold=0.3,
        )

    @patch("src.services.rag_service.ChatOpenAI")
    @patch("src.services.rag_service.EmbeddingService")
    @patch("src.services.rag_service.Chroma")
    def test_document_loading_to_vector_store_pipeline(
        self,
        mock_chroma,
        mock_embedding_service,
        mock_chat_openai,
        integration_settings,
    ):
        """ドキュメント読み込みからベクトルストア作成までのパイプラインをテスト"""
        # モックの設定
        mock_embeddings_instance = Mock()
        mock_service = Mock()
        mock_service.embeddings = mock_embeddings_instance
        mock_embedding_service.return_value = mock_service

        mock_vector_store = Mock()
        mock_chroma.from_documents.return_value = mock_vector_store

        mock_llm = Mock()
        mock_chat_openai.return_value = mock_llm

        # ドキュメントローダーのテスト
        loader = DocumentLoader(
            integration_settings.spec_file_path,
            integration_settings.chunk_size,
            integration_settings.chunk_overlap,
        )

        # ドキュメントが正しく読み込まれることを確認
        documents = loader.load_documents()
        assert len(documents) > 0
        assert all(isinstance(doc, Document) for doc in documents)

        # RAGサービスの初期化
        _rag_service = RAGService(integration_settings)

        # Chroma.from_documentsが適切な引数で呼ばれることを確認
        mock_chroma.from_documents.assert_called_once()
        call_args = mock_chroma.from_documents.call_args

        # ドキュメントが渡されていることを確認
        passed_documents = call_args[1]["documents"]
        assert len(passed_documents) > 0
        assert all(isinstance(doc, Document) for doc in passed_documents)

        # 埋め込み関数が渡されていることを確認
        assert call_args[1]["embedding"] == mock_embeddings_instance

        # 永続化ディレクトリが正しく設定されていることを確認
        assert (
            call_args[1]["persist_directory"]
            == integration_settings.chroma_persist_directory
        )

        # persistが呼ばれることを確認
        mock_vector_store.persist.assert_called_once()

    @patch("src.services.rag_service.ChatOpenAI")
    @patch("src.services.rag_service.EmbeddingService")
    @patch("src.services.rag_service.Chroma")
    def test_search_to_answer_generation_pipeline(
        self,
        mock_chroma,
        mock_embedding_service,
        mock_chat_openai,
        integration_settings,
    ):
        """検索から回答生成までのパイプラインをテスト"""
        # モックの設定
        mock_embeddings_instance = Mock()
        mock_service = Mock()
        mock_service.embeddings = mock_embeddings_instance
        mock_embedding_service.return_value = mock_service

        mock_vector_store = Mock()
        mock_chroma.from_documents.return_value = mock_vector_store

        # 検索結果のモック
        test_search_results = [
            (
                Document(
                    page_content="スゲリス・サーガは冒険RPGです。",
                    metadata={"section": "## **1. ゲーム概要**"},
                ),
                0.8,
            ),
            (
                Document(
                    page_content="ターン制バトルシステムを採用しています。",
                    metadata={"section": "### **1.1 基本システム**"},
                ),
                0.6,
            ),
        ]
        mock_vector_store.similarity_search_with_score.return_value = (
            test_search_results
        )

        # LLMの応答モック
        mock_llm = Mock()
        mock_chat_openai.return_value = mock_llm

        # LLMChainのモック
        with patch("src.services.rag_service.LLMChain") as mock_llm_chain:
            mock_chain_instance = Mock()
            mock_llm_chain.return_value = mock_chain_instance
            mock_chain_instance.run.return_value = (
                "スゲリス・サーガは冒険RPGで、ターン制バトルシステムを使用しています。"
            )

            # RAGサービスの初期化
            rag_service = RAGService(integration_settings)
            rag_service.vector_store = mock_vector_store

            # チャット機能のテスト
            response = rag_service.chat(
                "ゲームの基本システムについて教えて", max_results=2
            )

            # 結果の検証
            assert isinstance(response, ChatResponse)
            assert (
                response.answer
                == "スゲリス・サーガは冒険RPGで、ターン制バトルシステムを使用しています。"
            )
            assert len(response.sources) == 2
            assert response.confidence > 0

            # 検索が正しく実行されたことを確認
            mock_vector_store.similarity_search_with_score.assert_called_once_with(
                "ゲームの基本システムについて教えて", k=2
            )

            # LLMChainが正しく実行されたことを確認
            mock_chain_instance.run.assert_called_once()
            call_kwargs = mock_chain_instance.run.call_args[1]
            assert "question" in call_kwargs
            assert "context" in call_kwargs
            assert "ゲームの基本システムについて教えて" in call_kwargs["question"]

    @patch("src.services.rag_service.ChatOpenAI")
    @patch("src.services.rag_service.EmbeddingService")
    @patch("src.services.rag_service.Chroma")
    def test_similarity_threshold_filtering_integration(
        self,
        mock_chroma,
        mock_embedding_service,
        mock_chat_openai,
        integration_settings,
    ):
        """類似度しきい値フィルタリングの統合テスト"""
        # 類似度しきい値を0.5に設定
        integration_settings.similarity_threshold = 0.5

        mock_embeddings_instance = Mock()
        mock_service = Mock()
        mock_service.embeddings = mock_embeddings_instance
        mock_embedding_service.return_value = mock_service

        mock_vector_store = Mock()
        mock_chroma.from_documents.return_value = mock_vector_store

        # 類似度が異なる検索結果（しきい値以下の結果を含む）
        test_search_results = [
            (
                Document(
                    page_content="高関連性コンテンツ",
                    metadata={"section": "セクション1"},
                ),
                0.8,
            ),
            (
                Document(
                    page_content="中関連性コンテンツ",
                    metadata={"section": "セクション2"},
                ),
                0.6,
            ),
            (
                Document(
                    page_content="低関連性コンテンツ",
                    metadata={"section": "セクション3"},
                ),
                0.3,
            ),  # しきい値以下
            (
                Document(
                    page_content="最低関連性コンテンツ",
                    metadata={"section": "セクション4"},
                ),
                0.1,
            ),  # しきい値以下
        ]
        mock_vector_store.similarity_search_with_score.return_value = (
            test_search_results
        )

        mock_llm = Mock()
        mock_chat_openai.return_value = mock_llm

        with patch("src.services.rag_service.LLMChain") as mock_llm_chain:
            mock_chain_instance = Mock()
            mock_llm_chain.return_value = mock_chain_instance
            mock_chain_instance.run.return_value = (
                "フィルタリングされた結果に基づく回答"
            )

            rag_service = RAGService(integration_settings)
            rag_service.vector_store = mock_vector_store

            # 検索実行
            search_results = rag_service.search("テストクエリ", max_results=4)

            # しきい値以上の結果のみが返されることを確認
            assert len(search_results) == 2  # 0.8と0.6のスコアのみ
            assert all(score >= 0.5 for _, score in search_results)
            assert search_results[0][1] == 0.8
            assert search_results[1][1] == 0.6

    @patch("src.services.rag_service.ChatOpenAI")
    @patch("src.services.rag_service.EmbeddingService")
    @patch("src.services.rag_service.Chroma")
    def test_context_length_truncation_integration(
        self,
        mock_chroma,
        mock_embedding_service,
        mock_chat_openai,
        integration_settings,
    ):
        """コンテキスト長制限の統合テスト"""
        # コンテキスト長を小さく設定
        integration_settings.max_context_length = 100

        mock_embeddings_instance = Mock()
        mock_service = Mock()
        mock_service.embeddings = mock_embeddings_instance
        mock_embedding_service.return_value = mock_service

        mock_vector_store = Mock()
        mock_chroma.from_documents.return_value = mock_vector_store

        # 長いコンテンツの検索結果
        long_content = "A" * 200  # max_context_lengthより長い
        test_search_results = [
            (
                Document(
                    page_content=long_content, metadata={"section": "長いセクション"}
                ),
                0.8,
            ),
        ]
        mock_vector_store.similarity_search_with_score.return_value = (
            test_search_results
        )

        mock_llm = Mock()
        mock_chat_openai.return_value = mock_llm

        with patch("src.services.rag_service.LLMChain") as mock_llm_chain:
            mock_chain_instance = Mock()
            mock_llm_chain.return_value = mock_chain_instance
            mock_chain_instance.run.return_value = (
                "切り詰められたコンテキストからの回答"
            )

            rag_service = RAGService(integration_settings)
            rag_service.vector_store = mock_vector_store

            # 回答生成実行
            context_documents = [doc for doc, _ in test_search_results]
            _answer = rag_service.generate_answer("質問", context_documents)

            # LLMChainが呼ばれたことを確認
            mock_chain_instance.run.assert_called_once()
            call_kwargs = mock_chain_instance.run.call_args[1]

            # コンテキストが制限長以下に切り詰められていることを確認
            context = call_kwargs["context"]
            assert (
                len(context) <= integration_settings.max_context_length + 3
            )  # "..."を含む
            assert context.endswith("...")

    @patch("src.services.rag_service.ChatOpenAI")
    @patch("src.services.rag_service.EmbeddingService")
    @patch("src.services.rag_service.Chroma")
    def test_no_search_results_pipeline(
        self,
        mock_chroma,
        mock_embedding_service,
        mock_chat_openai,
        integration_settings,
    ):
        """検索結果がない場合のパイプラインをテスト"""
        mock_embeddings_instance = Mock()
        mock_service = Mock()
        mock_service.embeddings = mock_embeddings_instance
        mock_embedding_service.return_value = mock_service

        mock_vector_store = Mock()
        mock_chroma.from_documents.return_value = mock_vector_store

        # 検索結果なし
        mock_vector_store.similarity_search_with_score.return_value = []

        mock_llm = Mock()
        mock_chat_openai.return_value = mock_llm

        rag_service = RAGService(integration_settings)
        rag_service.vector_store = mock_vector_store

        # チャット実行
        response = rag_service.chat("見つからない質問")

        # 適切なレスポンスが返されることを確認
        assert isinstance(response, ChatResponse)
        assert "情報が仕様書内で見つかりませんでした" in response.answer
        assert len(response.sources) == 0
        assert response.confidence == 0.0

    @patch("src.services.rag_service.ChatOpenAI")
    @patch("src.services.rag_service.EmbeddingService")
    @patch("src.services.rag_service.Chroma")
    def test_multiple_chunks_from_same_section_integration(
        self,
        mock_chroma,
        mock_embedding_service,
        mock_chat_openai,
        integration_settings,
    ):
        """同じセクションからの複数チャンクの統合テスト"""
        mock_embeddings_instance = Mock()
        mock_service = Mock()
        mock_service.embeddings = mock_embeddings_instance
        mock_embedding_service.return_value = mock_service

        mock_vector_store = Mock()
        mock_chroma.from_documents.return_value = mock_vector_store

        # 同じセクションからの複数チャンク
        test_search_results = [
            (
                Document(
                    page_content="バトルシステムの基本説明。",
                    metadata={"section": "## **3. バトルシステム**"},
                ),
                0.9,
            ),
            (
                Document(
                    page_content="バトルシステムの詳細仕様。",
                    metadata={"section": "## **3. バトルシステム**"},
                ),
                0.7,
            ),
            (
                Document(
                    page_content="スキルシステムの説明。",
                    metadata={"section": "### **3.2 スキルシステム**"},
                ),
                0.6,
            ),
        ]
        mock_vector_store.similarity_search_with_score.return_value = (
            test_search_results
        )

        mock_llm = Mock()
        mock_chat_openai.return_value = mock_llm

        with patch("src.services.rag_service.LLMChain") as mock_llm_chain:
            mock_chain_instance = Mock()
            mock_llm_chain.return_value = mock_chain_instance
            mock_chain_instance.run.return_value = (
                "バトルシステムとスキルシステムについての統合回答"
            )

            rag_service = RAGService(integration_settings)
            rag_service.vector_store = mock_vector_store

            # チャット実行
            response = rag_service.chat("バトルシステムについて", max_results=3)

            # 結果の検証
            assert isinstance(response, ChatResponse)
            assert len(response.sources) == 3

            # ソースが正しく設定されていることを確認
            sections = [source.section for source in response.sources]
            assert "## **3. バトルシステム**" in sections
            assert "### **3.2 スキルシステム**" in sections

            # 信頼度が最高スコアから計算されていることを確認
            expected_confidence = 1.0 - 0.9
            assert response.confidence == expected_confidence


@pytest.mark.integration
@pytest.mark.slow
class TestRAGPipelinePerformance:
    """RAGパイプラインのパフォーマンステスト"""

    @patch("src.services.rag_service.ChatOpenAI")
    @patch("src.services.rag_service.EmbeddingService")
    @patch("src.services.rag_service.Chroma")
    def test_large_document_processing_performance(
        self, mock_chroma, mock_embedding_service, mock_chat_openai, temp_dir
    ):
        """大容量ドキュメント処理のパフォーマンステスト"""
        import time

        # 大きなテストドキュメントを作成
        large_content = """# 大容量仕様書

## **1. 概要**

""" + ("これは大容量ドキュメントのテストです。" * 1000)

        # 一時ファイルを作成
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            f.write(large_content)
            temp_file_path = f.name

        try:
            # 設定を作成
            integration_settings = Settings(
                openai_api_key="test_api_key",
                openai_model="gpt-4o-mini",
                openai_temperature=0.1,
                chroma_persist_directory=os.path.join(temp_dir, "chroma"),
                embedding_model_name="test/embedding-model",
                spec_file_path=temp_file_path,
                chunk_size=1000,
                chunk_overlap=200,
                max_context_length=1000,
                similarity_threshold=0.3,
            )

            mock_embeddings_instance = Mock()
            mock_service = Mock()
            mock_service.embeddings = mock_embeddings_instance
            mock_embedding_service.return_value = mock_service

            mock_vector_store = Mock()
            mock_chroma.from_documents.return_value = mock_vector_store

            mock_llm = Mock()
            mock_chat_openai.return_value = mock_llm

            # パフォーマンス測定
            start_time = time.time()

            # ドキュメントローダーのテスト
            loader = DocumentLoader(
                integration_settings.spec_file_path,
                integration_settings.chunk_size,
                integration_settings.chunk_overlap,
            )
            documents = loader.load_documents()

            load_time = time.time() - start_time

            # ドキュメントが生成されていることを確認
            assert len(documents) > 10  # 大容量なので多くのチャンクが生成される

            # パフォーマンスの確認（合理的な時間内で完了することを確認）
            assert load_time < 30.0  # 30秒以内で完了

            print(f"Large document processing time: {load_time:.2f} seconds")
            print(f"Generated {len(documents)} document chunks")

        finally:
            # 一時ファイルを削除
            os.unlink(temp_file_path)
