import pytest
from unittest.mock import Mock, patch, MagicMock

from src.services.embeddings import EmbeddingService


class TestEmbeddingService:
    """EmbeddingService クラスのテスト"""
    
    def test_init_default_model(self):
        """デフォルトモデルでの初期化をテスト"""
        service = EmbeddingService()
        assert service.model_name == "intfloat/multilingual-e5-large"
        assert service._embeddings is None
    
    def test_init_custom_model(self):
        """カスタムモデルでの初期化をテスト"""
        custom_model = "custom/embedding-model"
        service = EmbeddingService(model_name=custom_model)
        assert service.model_name == custom_model
        assert service._embeddings is None
    
    @patch("src.services.embeddings.HuggingFaceEmbeddings")
    def test_embeddings_property_lazy_initialization(self, mock_huggingface_embeddings):
        """埋め込みモデルの遅延初期化をテスト"""
        mock_embeddings_instance = Mock()
        mock_huggingface_embeddings.return_value = mock_embeddings_instance
        
        service = EmbeddingService()
        
        # 初期状態では_embeddingsはNone
        assert service._embeddings is None
        
        # プロパティアクセス時に初期化される
        embeddings = service.embeddings
        
        # HuggingFaceEmbeddingsが正しい引数で呼ばれたことを確認
        mock_huggingface_embeddings.assert_called_once_with(
            model_name="intfloat/multilingual-e5-large",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        
        # 返された値が正しいことを確認
        assert embeddings == mock_embeddings_instance
        assert service._embeddings == mock_embeddings_instance
    
    @patch("src.services.embeddings.HuggingFaceEmbeddings")
    def test_embeddings_property_caching(self, mock_huggingface_embeddings):
        """埋め込みモデルのキャッシュ動作をテスト"""
        mock_embeddings_instance = Mock()
        mock_huggingface_embeddings.return_value = mock_embeddings_instance
        
        service = EmbeddingService()
        
        # 最初のアクセス
        embeddings1 = service.embeddings
        # 2回目のアクセス
        embeddings2 = service.embeddings
        
        # HuggingFaceEmbeddingsは1回だけ呼ばれるべき
        mock_huggingface_embeddings.assert_called_once()
        
        # 同じインスタンスが返されるべき
        assert embeddings1 is embeddings2
        assert embeddings1 == mock_embeddings_instance
    
    @patch("src.services.embeddings.HuggingFaceEmbeddings")
    def test_embed_query(self, mock_huggingface_embeddings):
        """embed_query メソッドのテスト"""
        mock_embeddings_instance = Mock()
        mock_embeddings_instance.embed_query.return_value = [0.1, 0.2, 0.3]
        mock_huggingface_embeddings.return_value = mock_embeddings_instance
        
        service = EmbeddingService()
        
        # テストテキスト
        test_text = "テストクエリです"
        result = service.embed_query(test_text)
        
        # モックメソッドが正しい引数で呼ばれたことを確認
        mock_embeddings_instance.embed_query.assert_called_once_with(test_text)
        
        # 結果が正しいことを確認
        assert result == [0.1, 0.2, 0.3]
    
    @patch("src.services.embeddings.HuggingFaceEmbeddings")
    def test_embed_documents(self, mock_huggingface_embeddings):
        """embed_documents メソッドのテスト"""
        mock_embeddings_instance = Mock()
        mock_embeddings_instance.embed_documents.return_value = [
            [0.1, 0.2, 0.3],
            [0.4, 0.5, 0.6]
        ]
        mock_huggingface_embeddings.return_value = mock_embeddings_instance
        
        service = EmbeddingService()
        
        # テストテキストリスト
        test_texts = ["テストドキュメント1", "テストドキュメント2"]
        result = service.embed_documents(test_texts)
        
        # モックメソッドが正しい引数で呼ばれたことを確認
        mock_embeddings_instance.embed_documents.assert_called_once_with(test_texts)
        
        # 結果が正しいことを確認
        assert result == [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
    
    @patch("src.services.embeddings.HuggingFaceEmbeddings")
    def test_embed_query_empty_string(self, mock_huggingface_embeddings):
        """空文字列でのembed_queryをテスト"""
        mock_embeddings_instance = Mock()
        mock_embeddings_instance.embed_query.return_value = [0.0] * 1024
        mock_huggingface_embeddings.return_value = mock_embeddings_instance
        
        service = EmbeddingService()
        
        result = service.embed_query("")
        
        mock_embeddings_instance.embed_query.assert_called_once_with("")
        assert result == [0.0] * 1024
    
    @patch("src.services.embeddings.HuggingFaceEmbeddings")
    def test_embed_documents_empty_list(self, mock_huggingface_embeddings):
        """空リストでのembed_documentsをテスト"""
        mock_embeddings_instance = Mock()
        mock_embeddings_instance.embed_documents.return_value = []
        mock_huggingface_embeddings.return_value = mock_embeddings_instance
        
        service = EmbeddingService()
        
        result = service.embed_documents([])
        
        mock_embeddings_instance.embed_documents.assert_called_once_with([])
        assert result == []
    
    @patch("src.services.embeddings.HuggingFaceEmbeddings")
    def test_embed_documents_single_item(self, mock_huggingface_embeddings):
        """単一ドキュメントでのembed_documentsをテスト"""
        mock_embeddings_instance = Mock()
        mock_embeddings_instance.embed_documents.return_value = [[0.1, 0.2, 0.3]]
        mock_huggingface_embeddings.return_value = mock_embeddings_instance
        
        service = EmbeddingService()
        
        result = service.embed_documents(["単一ドキュメント"])
        
        mock_embeddings_instance.embed_documents.assert_called_once_with(["単一ドキュメント"])
        assert result == [[0.1, 0.2, 0.3]]
    
    @patch("src.services.embeddings.HuggingFaceEmbeddings")
    def test_japanese_text_embedding(self, mock_huggingface_embeddings):
        """日本語テキストの埋め込みをテスト"""
        mock_embeddings_instance = Mock()
        mock_embeddings_instance.embed_query.return_value = [0.1] * 1024
        mock_huggingface_embeddings.return_value = mock_embeddings_instance
        
        service = EmbeddingService()
        
        japanese_text = "これは日本語のテストテキストです。ゲーム仕様について説明します。"
        result = service.embed_query(japanese_text)
        
        mock_embeddings_instance.embed_query.assert_called_once_with(japanese_text)
        assert len(result) == 1024
    
    @patch("src.services.embeddings.HuggingFaceEmbeddings")
    def test_long_text_embedding(self, mock_huggingface_embeddings):
        """長いテキストの埋め込みをテスト"""
        mock_embeddings_instance = Mock()
        mock_embeddings_instance.embed_query.return_value = [0.1] * 1024
        mock_huggingface_embeddings.return_value = mock_embeddings_instance
        
        service = EmbeddingService()
        
        # 長いテキストを生成
        long_text = "テストテキスト。" * 100
        result = service.embed_query(long_text)
        
        mock_embeddings_instance.embed_query.assert_called_once_with(long_text)
        assert len(result) == 1024
    
    @patch("src.services.embeddings.HuggingFaceEmbeddings")
    @patch("src.services.embeddings.logger")
    def test_logging_during_initialization(self, mock_logger, mock_huggingface_embeddings):
        """初期化時のログ出力をテスト"""
        mock_embeddings_instance = Mock()
        mock_huggingface_embeddings.return_value = mock_embeddings_instance
        
        service = EmbeddingService()
        
        # 埋め込みモデルにアクセスして初期化をトリガー
        _ = service.embeddings
        
        # ログが正しく呼ばれたことを確認
        mock_logger.info.assert_any_call("埋め込みモデルを初期化中: intfloat/multilingual-e5-large")
        mock_logger.info.assert_any_call("埋め込みモデルの初期化が完了しました")
    
    @patch("src.services.embeddings.HuggingFaceEmbeddings")
    def test_custom_model_configuration(self, mock_huggingface_embeddings):
        """カスタムモデル設定での初期化をテスト"""
        mock_embeddings_instance = Mock()
        mock_huggingface_embeddings.return_value = mock_embeddings_instance
        
        custom_model = "sentence-transformers/all-MiniLM-L6-v2"
        service = EmbeddingService(model_name=custom_model)
        
        # 埋め込みモデルにアクセス
        _ = service.embeddings
        
        # カスタムモデル名で初期化されたことを確認
        mock_huggingface_embeddings.assert_called_once_with(
            model_name=custom_model,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )


@pytest.mark.parametrize("model_name", [
    "intfloat/multilingual-e5-large",
    "sentence-transformers/all-MiniLM-L6-v2",
    "custom/model-name"
])
def test_different_model_names(model_name):
    """異なるモデル名での初期化をパラメータ化テストで検証"""
    service = EmbeddingService(model_name=model_name)
    assert service.model_name == model_name


@pytest.mark.parametrize("texts,expected_length", [
    ([], 0),
    (["単一テキスト"], 1),
    (["テキスト1", "テキスト2"], 2),
    (["A", "B", "C", "D", "E"], 5),
])
@patch("src.services.embeddings.HuggingFaceEmbeddings")
def test_embed_documents_various_lengths(mock_huggingface_embeddings, texts, expected_length):
    """様々な長さのテキストリストでのembed_documentsをパラメータ化テストで検証"""
    mock_embeddings_instance = Mock()
    mock_embeddings_instance.embed_documents.return_value = [[0.1] * 1024] * expected_length
    mock_huggingface_embeddings.return_value = mock_embeddings_instance
    
    service = EmbeddingService()
    result = service.embed_documents(texts)
    
    mock_embeddings_instance.embed_documents.assert_called_once_with(texts)
    assert len(result) == expected_length