import os
from typing import List
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_community.document_loaders import TextLoader
import re


class DocumentLoader:
    def __init__(self, file_path: str, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.file_path = file_path
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n## ", "\n### ", "\n\n", "\n", " ", ""],
            keep_separator=True,
        )
    
    def load_documents(self) -> List[Document]:
        """仕様書ドキュメントを読み込み、チャンクに分割する"""
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"仕様書ファイルが見つかりません: {self.file_path}")
        
        # ドキュメントを読み込む
        loader = TextLoader(self.file_path, encoding="utf-8")
        documents = loader.load()
        
        # メタデータを追加（セクション情報など）
        enriched_documents = self._enrich_documents(documents)
        
        # チャンクに分割
        chunks = self.text_splitter.split_documents(enriched_documents)
        
        return chunks
    
    def _enrich_documents(self, documents: List[Document]) -> List[Document]:
        """ドキュメントにセクション情報などのメタデータを追加"""
        enriched = []
        
        for doc in documents:
            enriched_chunks = self._process_single_document(doc)
            enriched.extend(enriched_chunks)
        
        return enriched
    
    def _process_single_document(self, doc: Document) -> List[Document]:
        """単一ドキュメントを処理してチャンクに分割"""
        content = doc.page_content
        lines = content.split('\n')
        
        chunks = self._create_chunks_from_lines(lines)
        return self._convert_chunks_to_documents(chunks)
    
    def _create_chunks_from_lines(self, lines: List[str]) -> List[dict]:
        """行のリストからチャンクを作成"""
        current_section = ""
        current_subsection = ""
        chunks = []
        current_chunk = []
        
        for line in lines:
            # セクション情報を更新
            section_info = self._detect_section_headers(line)
            if section_info['is_main_section']:
                current_section = section_info['section']
                current_subsection = ""
            elif section_info['is_subsection']:
                current_subsection = section_info['section']
            
            current_chunk.append(line)
            
            # チャンクサイズをチェックして必要に応じて分割
            if self._should_create_chunk(current_chunk):
                chunk_content = '\n'.join(current_chunk[:-1])
                if chunk_content.strip():
                    chunks.append(self._create_chunk_dict(
                        chunk_content, current_section, current_subsection
                    ))
                current_chunk = [line]
        
        # 最後のチャンクを処理
        if current_chunk:
            chunk_content = '\n'.join(current_chunk)
            if chunk_content.strip():
                chunks.append(self._create_chunk_dict(
                    chunk_content, current_section, current_subsection
                ))
        
        return chunks
    
    def _detect_section_headers(self, line: str) -> dict:
        """行がセクションヘッダーかどうかを検出"""
        is_main_section = bool(re.match(r'^## \*\*\d+', line))
        is_subsection = bool(re.match(r'^### \*\*\d+', line))
        
        return {
            'is_main_section': is_main_section,
            'is_subsection': is_subsection,
            'section': line.strip() if (is_main_section or is_subsection) else ""
        }
    
    def _should_create_chunk(self, current_chunk: List[str]) -> bool:
        """現在のチャンクを分割すべきかどうかを判断"""
        return len('\n'.join(current_chunk)) > self.chunk_size
    
    def _create_chunk_dict(self, content: str, section: str, subsection: str) -> dict:
        """チャンク辞書を作成"""
        return {
            'content': content,
            'section': section,
            'subsection': subsection
        }
    
    def _convert_chunks_to_documents(self, chunks: List[dict]) -> List[Document]:
        """チャンク辞書のリストをDocumentオブジェクトのリストに変換"""
        documents = []
        
        for chunk in chunks:
            documents.append(Document(
                page_content=chunk['content'],
                metadata={
                    'source': self.file_path,
                    'section': chunk['section'],
                    'subsection': chunk['subsection']
                }
            ))
        
        return documents