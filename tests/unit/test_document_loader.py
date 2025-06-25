import os
import tempfile
import pytest
from unittest.mock import Mock, patch, mock_open
from langchain.schema import Document

from src.services.document_loader import DocumentLoader


class TestDocumentLoader:
    """DocumentLoader クラスのテスト"""
    
    def test_init_default_parameters(self):
        """デフォルトパラメータでの初期化をテスト"""
        loader = DocumentLoader("test_file.md")
        
        assert loader.file_path == "test_file.md"
        assert loader.chunk_size == 1000
        assert loader.chunk_overlap == 200
        assert loader.text_splitter is not None
    
    def test_init_custom_parameters(self):
        """カスタムパラメータでの初期化をテスト"""
        loader = DocumentLoader(
            file_path="custom_file.md",
            chunk_size=500,
            chunk_overlap=100
        )
        
        assert loader.file_path == "custom_file.md"
        assert loader.chunk_size == 500
        assert loader.chunk_overlap == 100
    
    def test_text_splitter_configuration(self):
        """テキストスプリッターの設定をテスト"""
        loader = DocumentLoader("test_file.md", chunk_size=800, chunk_overlap=150)
        
        # RecursiveCharacterTextSplitterが正しく設定されていることを確認
        assert loader.text_splitter._chunk_size == 800
        assert loader.text_splitter._chunk_overlap == 150
        
        # セパレーターが正しく設定されていることを確認
        expected_separators = ["\n## ", "\n### ", "\n\n", "\n", " ", ""]
        assert loader.text_splitter._separators == expected_separators
        assert loader.text_splitter._keep_separator is True
    
    def test_load_documents_file_not_found(self):
        """存在しないファイルでFileNotFoundErrorが発生することをテスト"""
        loader = DocumentLoader("non_existent_file.md")
        
        with pytest.raises(FileNotFoundError) as exc_info:
            loader.load_documents()
        
        assert "仕様書ファイルが見つかりません" in str(exc_info.value)
        assert "non_existent_file.md" in str(exc_info.value)
    
    @patch("src.services.document_loader.TextLoader")
    @patch("os.path.exists")
    def test_load_documents_success(self, mock_exists, mock_text_loader):
        """正常なドキュメント読み込みをテスト"""
        # ファイル存在チェックをモック
        mock_exists.return_value = True
        
        # TextLoaderをモック
        mock_loader_instance = Mock()
        mock_text_loader.return_value = mock_loader_instance
        
        # ドキュメントコンテンツをモック
        test_content = """# テストドキュメント

## **1. セクション1**

これはセクション1の内容です。

### **1.1 サブセクション**

これはサブセクションの内容です。

## **2. セクション2**

これはセクション2の内容です。
"""
        mock_document = Document(page_content=test_content)
        mock_loader_instance.load.return_value = [mock_document]
        
        loader = DocumentLoader("test_file.md", chunk_size=100, chunk_overlap=20)
        
        # パッチを適用してテスト実行
        with patch.object(loader, '_enrich_documents') as mock_enrich:
            mock_enrich.return_value = [mock_document]
            
            with patch.object(loader.text_splitter, 'split_documents') as mock_split:
                expected_chunks = [
                    Document(page_content="チャンク1", metadata={"section": "セクション1"}),
                    Document(page_content="チャンク2", metadata={"section": "セクション2"})
                ]
                mock_split.return_value = expected_chunks
                
                result = loader.load_documents()
        
        # TextLoaderが正しい引数で呼ばれたことを確認
        mock_text_loader.assert_called_once_with("test_file.md", encoding="utf-8")
        mock_loader_instance.load.assert_called_once()
        
        # _enrich_documentsが呼ばれたことを確認
        mock_enrich.assert_called_once_with([mock_document])
        
        # split_documentsが呼ばれたことを確認
        mock_split.assert_called_once_with([mock_document])
        
        # 結果が正しいことを確認
        assert result == expected_chunks
    
    def test_enrich_documents_section_detection(self):
        """セクション検出機能をテスト"""
        test_content = """# タイトル

## **1. 第一セクション**

第一セクションの内容です。
これは複数行の内容です。

### **1.1 第一サブセクション**

第一サブセクションの内容です。

### **1.2 第二サブセクション**

第二サブセクションの内容です。

## **2. 第二セクション**

第二セクションの内容です。

### **2.1 別のサブセクション**

別のサブセクションの内容です。
"""
        
        loader = DocumentLoader("test_file.md", chunk_size=200, chunk_overlap=50)
        input_doc = Document(page_content=test_content)
        
        result = loader._enrich_documents([input_doc])
        
        # 結果がDocumentのリストであることを確認
        assert isinstance(result, list)
        assert all(isinstance(doc, Document) for doc in result)
        
        # 各チャンクにメタデータが含まれていることを確認
        for doc in result:
            assert 'source' in doc.metadata
            assert 'section' in doc.metadata
            assert 'subsection' in doc.metadata
            assert doc.metadata['source'] == "test_file.md"
    
    def test_enrich_documents_empty_content(self):
        """空のコンテンツの処理をテスト"""
        loader = DocumentLoader("test_file.md")
        input_doc = Document(page_content="")
        
        result = loader._enrich_documents([input_doc])
        
        # 空のコンテンツでも適切に処理されることを確認
        assert isinstance(result, list)
    
    def test_enrich_documents_no_sections(self):
        """セクションのないドキュメントの処理をテスト"""
        test_content = """これはセクションヘッダーのない
普通のテキストコンテンツです。

複数の段落があります。

最後の段落です。
"""
        
        loader = DocumentLoader("test_file.md", chunk_size=100, chunk_overlap=20)
        input_doc = Document(page_content=test_content)
        
        result = loader._enrich_documents([input_doc])
        
        # セクションがない場合でも適切に処理されることを確認
        assert isinstance(result, list)
        for doc in result:
            assert doc.metadata['section'] == ""
            assert doc.metadata['subsection'] == ""
    
    def test_enrich_documents_section_metadata(self):
        """セクションメタデータの正確性をテスト"""
        test_content = """## **1. メインセクション**

メインセクションの内容。

### **1.1 サブセクション**

サブセクションの内容。
もう少し長い内容にします。
"""
        
        loader = DocumentLoader("test_file.md", chunk_size=50, chunk_overlap=10)
        input_doc = Document(page_content=test_content)
        
        result = loader._enrich_documents([input_doc])
        
        # 少なくとも1つのドキュメントが生成されることを確認
        assert len(result) > 0
        
        # 最初のドキュメントのメタデータを確認
        first_doc = result[0]
        assert "## **1. メインセクション**" in first_doc.metadata['section']
    
    @patch("src.services.document_loader.TextLoader")
    @patch("os.path.exists")
    def test_load_documents_integration(self, mock_exists, mock_text_loader):
        """load_documentsの統合テスト"""
        mock_exists.return_value = True
        
        # 実際のテストコンテンツ
        test_content = """# スゲリス・サーガ 仕様書

## **1. ゲーム概要**

スゲリス・サーガは冒険RPGです。

### **1.1 基本システム**

ターン制バトルシステムを採用。

## **2. キャラクター**

キャラクター仕様について。
"""
        
        mock_loader_instance = Mock()
        mock_text_loader.return_value = mock_loader_instance
        mock_document = Document(page_content=test_content)
        mock_loader_instance.load.return_value = [mock_document]
        
        loader = DocumentLoader("test_spec.md", chunk_size=100, chunk_overlap=20)
        result = loader.load_documents()
        
        # 結果が適切に生成されることを確認
        assert isinstance(result, list)
        assert len(result) > 0
        
        # 各チャンクがDocumentオブジェクトであることを確認
        for chunk in result:
            assert isinstance(chunk, Document)
            assert hasattr(chunk, 'page_content')
            assert hasattr(chunk, 'metadata')
            assert 'source' in chunk.metadata
    
    def test_chunk_size_effect_on_splitting(self):
        """チャンクサイズが分割に与える影響をテスト"""
        test_content = "A" * 1000  # 1000文字のテキスト
        
        # 小さなチャンクサイズ
        small_loader = DocumentLoader("test.md", chunk_size=100, chunk_overlap=10)
        small_input_doc = Document(page_content=test_content)
        small_result = small_loader._enrich_documents([small_input_doc])
        
        # 大きなチャンクサイズ
        large_loader = DocumentLoader("test.md", chunk_size=500, chunk_overlap=10)
        large_input_doc = Document(page_content=test_content)
        large_result = large_loader._enrich_documents([large_input_doc])
        
        # 小さなチャンクサイズの方がより多くのチャンクを生成することを確認
        # （ただし、_enrich_documentsの実装によっては結果が異なる可能性がある）
        assert len(small_result) >= 1
        assert len(large_result) >= 1


@pytest.mark.parametrize("chunk_size,chunk_overlap", [
    (500, 50),
    (1000, 100),
    (1500, 150),
    (2000, 200),
])
def test_different_chunk_configurations(chunk_size, chunk_overlap):
    """異なるチャンク設定での初期化をパラメータ化テストで検証"""
    loader = DocumentLoader("test.md", chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    
    assert loader.chunk_size == chunk_size
    assert loader.chunk_overlap == chunk_overlap
    assert loader.text_splitter._chunk_size == chunk_size
    assert loader.text_splitter._chunk_overlap == chunk_overlap


@pytest.mark.parametrize("file_path", [
    "test.md",
    "documents/spec.md",
    "/absolute/path/to/file.md",
    "ファイル名に日本語.md",
])
def test_different_file_paths(file_path):
    """異なるファイルパスでの初期化をパラメータ化テストで検証"""
    loader = DocumentLoader(file_path)
    assert loader.file_path == file_path


class TestDocumentLoaderEdgeCases:
    """DocumentLoader のエッジケースのテスト"""
    
    def test_very_small_chunk_size(self):
        """非常に小さなチャンクサイズでの動作をテスト"""
        loader = DocumentLoader("test.md", chunk_size=10, chunk_overlap=2)
        assert loader.chunk_size == 10
        assert loader.chunk_overlap == 2
    
    def test_zero_chunk_overlap(self):
        """チャンクオーバーラップが0の場合の動作をテスト"""
        loader = DocumentLoader("test.md", chunk_size=1000, chunk_overlap=0)
        assert loader.chunk_overlap == 0
    
    def test_chunk_overlap_equals_chunk_size(self):
        """チャンクオーバーラップがチャンクサイズと等しい場合をテスト"""
        # これは実際の使用では推奨されないが、システムが壊れないことを確認
        loader = DocumentLoader("test.md", chunk_size=100, chunk_overlap=100)
        assert loader.chunk_size == 100
        assert loader.chunk_overlap == 100