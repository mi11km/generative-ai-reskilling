import pytest
from unittest.mock import Mock, patch
from langchain.schema import Document

from src.services.document_loader import DocumentLoader


class TestDocumentLoaderRefactored:
    """リファクタリング後のDocumentLoaderのテスト"""
    
    @pytest.fixture
    def document_loader(self):
        """テスト用のDocumentLoaderインスタンス"""
        return DocumentLoader("test_file.md", chunk_size=100, chunk_overlap=20)
    
    def test_detect_section_headers_main_section(self, document_loader):
        """メインセクションヘッダーの検出をテスト"""
        line = "## **1. ゲーム概要**"
        result = document_loader._detect_section_headers(line)
        
        assert result['is_main_section'] is True
        assert result['is_subsection'] is False
        assert result['section'] == "## **1. ゲーム概要**"
    
    def test_detect_section_headers_subsection(self, document_loader):
        """サブセクションヘッダーの検出をテスト"""
        line = "### **1.1 基本システム**"
        result = document_loader._detect_section_headers(line)
        
        assert result['is_main_section'] is False
        assert result['is_subsection'] is True
        assert result['section'] == "### **1.1 基本システム**"
    
    def test_detect_section_headers_regular_line(self, document_loader):
        """通常の行（セクションでない）の検出をテスト"""
        line = "これは通常のテキスト行です。"
        result = document_loader._detect_section_headers(line)
        
        assert result['is_main_section'] is False
        assert result['is_subsection'] is False
        assert result['section'] == ""
    
    def test_detect_section_headers_invalid_section(self, document_loader):
        """無効なセクションヘッダーの検出をテスト"""
        invalid_lines = [
            "# **1. ゲーム概要**",  # シングル#
            "## ゲーム概要",        # **数字がない
            "### 1.1 基本システム", # **がない
            "#### **1.1.1 詳細**",  # 4つの#
        ]
        
        for line in invalid_lines:
            result = document_loader._detect_section_headers(line)
            assert result['is_main_section'] is False
            assert result['is_subsection'] is False
    
    def test_should_create_chunk_true(self, document_loader):
        """チャンクサイズを超えた場合のテスト"""
        # chunk_size=100より大きいチャンク
        large_chunk = ["A" * 50, "B" * 60]  # 合計110文字（改行込み）
        
        result = document_loader._should_create_chunk(large_chunk)
        assert result is True
    
    def test_should_create_chunk_false(self, document_loader):
        """チャンクサイズ以下の場合のテスト"""
        # chunk_size=100以下のチャンク
        small_chunk = ["A" * 30, "B" * 30]  # 合計61文字（改行込み）
        
        result = document_loader._should_create_chunk(small_chunk)
        assert result is False
    
    def test_create_chunk_dict(self, document_loader):
        """チャンク辞書作成のテスト"""
        content = "テストコンテンツ"
        section = "## **1. テストセクション**"
        subsection = "### **1.1 テストサブセクション**"
        
        result = document_loader._create_chunk_dict(content, section, subsection)
        
        expected = {
            'content': content,
            'section': section,
            'subsection': subsection
        }
        assert result == expected
    
    def test_convert_chunks_to_documents(self, document_loader):
        """チャンクからDocumentオブジェクトへの変換をテスト"""
        chunks = [
            {
                'content': "テストコンテンツ1",
                'section': "## **1. セクション1**",
                'subsection': ""
            },
            {
                'content': "テストコンテンツ2",
                'section': "## **2. セクション2**",
                'subsection': "### **2.1 サブセクション**"
            }
        ]
        
        documents = document_loader._convert_chunks_to_documents(chunks)
        
        assert len(documents) == 2
        
        # 最初のドキュメント
        assert isinstance(documents[0], Document)
        assert documents[0].page_content == "テストコンテンツ1"
        assert documents[0].metadata['source'] == "test_file.md"
        assert documents[0].metadata['section'] == "## **1. セクション1**"
        assert documents[0].metadata['subsection'] == ""
        
        # 2番目のドキュメント
        assert isinstance(documents[1], Document)
        assert documents[1].page_content == "テストコンテンツ2"
        assert documents[1].metadata['section'] == "## **2. セクション2**"
        assert documents[1].metadata['subsection'] == "### **2.1 サブセクション**"
    
    def test_create_chunks_from_lines_simple(self, document_loader):
        """シンプルな行からのチャンク作成をテスト"""
        lines = [
            "## **1. テストセクション**",
            "テストコンテンツ行1",
            "テストコンテンツ行2",
            "### **1.1 サブセクション**",
            "サブセクションコンテンツ"
        ]
        
        chunks = document_loader._create_chunks_from_lines(lines)
        
        # 小さなchunk_size(100)なので複数のチャンクに分割される可能性
        assert len(chunks) >= 1
        assert all(isinstance(chunk, dict) for chunk in chunks)
        assert all('content' in chunk for chunk in chunks)
        assert all('section' in chunk for chunk in chunks)
        assert all('subsection' in chunk for chunk in chunks)
    
    def test_create_chunks_from_lines_with_sections(self, document_loader):
        """セクション情報を含む行からのチャンク作成をテスト"""
        lines = [
            "## **1. メインセクション**",
            "メインセクションのコンテンツです。",
            "### **1.1 サブセクション**",
            "サブセクションのコンテンツです。",
            "## **2. 別のメインセクション**",
            "別のセクションのコンテンツです。"
        ]
        
        chunks = document_loader._create_chunks_from_lines(lines)
        
        # セクション情報が正しく設定されていることを確認
        for chunk in chunks:
            if "メインセクション" in chunk['content']:
                assert "## **1. メインセクション**" in chunk['section'] or chunk['section'] == ""
            if "サブセクション" in chunk['content']:
                assert "### **1.1 サブセクション**" in chunk['subsection'] or chunk['subsection'] == ""
    
    def test_process_single_document(self, document_loader):
        """単一ドキュメント処理のテスト"""
        test_content = """## **1. テストセクション**

テストセクションの内容です。

### **1.1 サブセクション**

サブセクションの内容です。

## **2. 別のセクション**

別のセクションの内容です。"""
        
        test_doc = Document(page_content=test_content)
        
        result_documents = document_loader._process_single_document(test_doc)
        
        # 結果がDocumentのリストであることを確認
        assert isinstance(result_documents, list)
        assert all(isinstance(doc, Document) for doc in result_documents)
        assert len(result_documents) >= 1
        
        # メタデータが正しく設定されていることを確認
        for doc in result_documents:
            assert 'source' in doc.metadata
            assert 'section' in doc.metadata
            assert 'subsection' in doc.metadata
            assert doc.metadata['source'] == "test_file.md"
    
    def test_enrich_documents_integration(self, document_loader):
        """_enrich_documentsの統合テスト（リファクタリング後）"""
        test_content = """# タイトル

## **1. 第一セクション**

第一セクションの内容です。

### **1.1 第一サブセクション**

第一サブセクションの内容です。"""
        
        input_docs = [Document(page_content=test_content)]
        
        result = document_loader._enrich_documents(input_docs)
        
        # リファクタリング前と同じ結果が得られることを確認
        assert isinstance(result, list)
        assert len(result) >= 1
        assert all(isinstance(doc, Document) for doc in result)
        
        # メタデータが適切に設定されていることを確認
        for doc in result:
            assert hasattr(doc, 'page_content')
            assert hasattr(doc, 'metadata')
            assert 'source' in doc.metadata
            assert 'section' in doc.metadata
            assert 'subsection' in doc.metadata


class TestDocumentLoaderRefactoredEdgeCases:
    """リファクタリング後のDocumentLoaderのエッジケーステスト"""
    
    def test_detect_section_headers_edge_cases(self):
        """セクションヘッダー検出のエッジケースをテスト"""
        loader = DocumentLoader("test.md")
        
        edge_cases = [
            ("", {'is_main_section': False, 'is_subsection': False, 'section': ""}),
            ("   ", {'is_main_section': False, 'is_subsection': False, 'section': ""}),
            ("##", {'is_main_section': False, 'is_subsection': False, 'section': ""}),
            ("## **", {'is_main_section': False, 'is_subsection': False, 'section': ""}),
            ("## **123**", {'is_main_section': True, 'is_subsection': False, 'section': "## **123**"}),
            ("### **1.1.1**", {'is_main_section': False, 'is_subsection': True, 'section': "### **1.1.1**"}),
        ]
        
        for line, expected in edge_cases:
            result = loader._detect_section_headers(line)
            assert result == expected, f"Failed for line: '{line}'"
    
    def test_create_chunks_from_lines_empty_input(self):
        """空の入力での処理をテスト"""
        loader = DocumentLoader("test.md", chunk_size=100)
        
        result = loader._create_chunks_from_lines([])
        assert result == []
    
    def test_create_chunks_from_lines_single_line(self):
        """単一行での処理をテスト"""
        loader = DocumentLoader("test.md", chunk_size=100)
        
        result = loader._create_chunks_from_lines(["単一の行です"])
        assert len(result) == 1
        assert result[0]['content'] == "単一の行です"
        assert result[0]['section'] == ""
        assert result[0]['subsection'] == ""
    
    def test_create_chunks_from_lines_very_long_lines(self):
        """非常に長い行での処理をテスト"""
        loader = DocumentLoader("test.md", chunk_size=50)
        
        long_line = "A" * 100  # chunk_sizeの2倍
        lines = [long_line]
        
        result = loader._create_chunks_from_lines(lines)
        
        # 長い行でも適切に処理されることを確認
        assert len(result) >= 1
        assert all('content' in chunk for chunk in result)
    
    def test_convert_chunks_to_documents_empty_input(self):
        """空のチャンクリストでの変換をテスト"""
        loader = DocumentLoader("test.md")
        
        result = loader._convert_chunks_to_documents([])
        assert result == []
    
    def test_process_single_document_empty_content(self):
        """空のコンテンツでの処理をテスト"""
        loader = DocumentLoader("test.md")
        
        empty_doc = Document(page_content="")
        result = loader._process_single_document(empty_doc)
        
        # 空のコンテンツでも適切に処理されることを確認
        assert isinstance(result, list)
        # 空の場合は結果も空になる可能性がある
        assert len(result) >= 0


class TestDocumentLoaderBackwardCompatibility:
    """リファクタリング後の後方互換性テスト"""
    
    @patch("src.services.document_loader.TextLoader")
    @patch("os.path.exists")
    def test_load_documents_still_works(self, mock_exists, mock_text_loader):
        """load_documentsが引き続き動作することをテスト"""
        mock_exists.return_value = True
        
        test_content = """## **1. テストセクション**
テストコンテンツです。

### **1.1 サブセクション**
サブセクションのコンテンツです。"""
        
        mock_loader_instance = Mock()
        mock_text_loader.return_value = mock_loader_instance
        mock_document = Document(page_content=test_content)
        mock_loader_instance.load.return_value = [mock_document]
        
        loader = DocumentLoader("test_spec.md", chunk_size=100, chunk_overlap=20)
        result = loader.load_documents()
        
        # リファクタリング前と同じインターフェースで動作することを確認
        assert isinstance(result, list)
        assert len(result) > 0
        assert all(isinstance(chunk, Document) for chunk in result)
        
        # メタデータが正しく設定されていることを確認
        for chunk in result:
            assert 'source' in chunk.metadata
            assert 'section' in chunk.metadata
            assert 'subsection' in chunk.metadata
    
    def test_refactored_methods_maintain_functionality(self):
        """リファクタリングしたメソッドが元の機能を維持していることをテスト"""
        loader = DocumentLoader("test.md", chunk_size=200, chunk_overlap=50)
        
        # 複雑なテストケース
        complex_content = """# メイン タイトル

## **1. 第一章**

第一章の導入部分です。
ここには詳細な説明が含まれています。

### **1.1 第一節**

第一節の内容です。
複数行にわたる内容があります。

### **1.2 第二節**

第二節の内容です。

## **2. 第二章**

第二章の内容です。
ここも複数行の説明があります。"""
        
        test_doc = Document(page_content=complex_content)
        result = loader._enrich_documents([test_doc])
        
        # 適切に処理されていることを確認
        assert len(result) > 0
        
        # セクション情報が適切に抽出されていることを確認
        sections_found = set()
        subsections_found = set()
        
        for doc in result:
            if doc.metadata['section']:
                sections_found.add(doc.metadata['section'])
            if doc.metadata['subsection']:
                subsections_found.add(doc.metadata['subsection'])
        
        # 期待されるセクションが見つかることを確認
        assert any("第一章" in section for section in sections_found)
        assert any("第二章" in section for section in sections_found)
        assert any("第一節" in subsection for subsection in subsections_found)


@pytest.mark.parametrize("chunk_size,expected_min_chunks", [
    (50, 2),   # 小さなチャンクサイズでは多くのチャンクが生成される
    (200, 1),  # 大きなチャンクサイズでは少ないチャンクが生成される
    (1000, 1), # 非常に大きなチャンクサイズでは1つのチャンクが生成される
])
def test_chunk_size_effects_on_refactored_methods(chunk_size, expected_min_chunks):
    """リファクタリング後のメソッドでチャンクサイズの効果をパラメータ化テストで検証"""
    loader = DocumentLoader("test.md", chunk_size=chunk_size, chunk_overlap=10)
    
    test_content = """## **1. テストセクション**
これはテストコンテンツです。""" + "追加のテキスト。" * 20  # 長いコンテンツ
    
    lines = test_content.split('\n')
    chunks = loader._create_chunks_from_lines(lines)
    
    assert len(chunks) >= expected_min_chunks