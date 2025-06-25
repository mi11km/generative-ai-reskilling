import os
from typing import List, Optional, Tuple
from langchain_chroma import Chroma
from langchain_openai import ChatOpenAI
from langchain.schema import Document
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
import logging

from src.services.document_loader import DocumentLoader
from src.services.embeddings import EmbeddingService
from src.models.schemas import SourceDocument, ChatResponse
from src.config.settings import Settings

logger = logging.getLogger(__name__)


class RAGService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.embedding_service = EmbeddingService(settings.embedding_model_name)
        self.vector_store: Optional[Chroma] = None
        self.llm = ChatOpenAI(
            api_key=settings.openai_api_key,
            model=settings.openai_model,
            temperature=settings.openai_temperature
        )
        self._initialize_vector_store()
    
    def _initialize_vector_store(self):
        """ベクトルストアを初期化"""
        try:
            # 既存のベクトルストアをロード、または新規作成
            if os.path.exists(self.settings.chroma_persist_directory):
                logger.info("既存のベクトルストアをロード中...")
                self.vector_store = Chroma(
                    persist_directory=self.settings.chroma_persist_directory,
                    embedding_function=self.embedding_service.embeddings
                )
            else:
                logger.info("新規ベクトルストアを作成中...")
                self._create_vector_store()
        except Exception as e:
            logger.error(f"ベクトルストアの初期化に失敗しました: {e}")
            raise
    
    def _create_vector_store(self):
        """ドキュメントをロードしてベクトルストアを作成"""
        loader = DocumentLoader(
            self.settings.spec_file_path,
            self.settings.chunk_size,
            self.settings.chunk_overlap
        )
        documents = loader.load_documents()
        
        logger.info(f"{len(documents)}個のドキュメントチャンクをベクトル化中...")
        
        self.vector_store = Chroma.from_documents(
            documents=documents,
            embedding=self.embedding_service.embeddings,
            persist_directory=self.settings.chroma_persist_directory
        )
        self.vector_store.persist()
        logger.info("ベクトルストアの作成が完了しました")
    
    def search(self, query: str, max_results: int = 3) -> List[Tuple[Document, float]]:
        """クエリに関連するドキュメントを検索"""
        if not self.vector_store:
            raise ValueError("ベクトルストアが初期化されていません")
        
        results = self.vector_store.similarity_search_with_score(
            query,
            k=max_results
        )
        
        # デバッグログ: 検索結果のスコアを出力
        logger.info(f"検索クエリ: {query}")
        logger.info(f"検索結果数: {len(results)}")
        for i, (doc, score) in enumerate(results):
            logger.info(f"結果{i+1}: スコア={score:.4f}, 内容={doc.page_content[:100]}...")
        
        # 信頼度しきい値でフィルタリング
        filtered_results = [
            (doc, score) for doc, score in results
            if score >= self.settings.similarity_threshold
        ]
        
        logger.info(f"しきい値({self.settings.similarity_threshold})適用後の結果数: {len(filtered_results)}")
        
        return filtered_results
    
    def generate_answer(self, query: str, context_documents: List[Document]) -> str:
        """コンテキストを基に回答を生成"""
        # 設定からプロンプトテンプレートを取得
        prompt_templates = self.settings.prompt_templates
        
        # プロンプトテンプレートを作成
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", prompt_templates.system_prompt),
            ("human", prompt_templates.human_prompt)
        ])
        
        # コンテキストを整形（設定可能なフォーマットを使用）
        context = "\n\n".join([
            prompt_templates.context_section_format.format(
                section=doc.metadata.get('section', '不明'),
                content=doc.page_content
            )
            for doc in context_documents
        ])
        
        # 最大コンテキスト長を考慮
        if len(context) > self.settings.max_context_length:
            context = context[:self.settings.max_context_length] + "..."
        
        # LLMチェーンを作成して実行
        chain = LLMChain(llm=self.llm, prompt=prompt_template)
        answer = chain.run(context=context, question=query)
        
        return answer.strip()
    
    def chat(self, question: str, max_results: int = 3) -> ChatResponse:
        """ユーザーの質問に対してRAGを使用して回答"""
        try:
            # 関連ドキュメントを検索
            search_results = self.search(question, max_results)
            
            if not search_results:
                return ChatResponse(
                    answer=self.settings.prompt_templates.no_results_message,
                    sources=[],
                    confidence=0.0
                )
            
            # コンテキストドキュメントを抽出
            context_documents = [doc for doc, _ in search_results]
            
            # 回答を生成
            answer = self.generate_answer(question, context_documents)
            
            # ソース情報を整形
            sources = []
            for doc, score in search_results:
                sources.append(SourceDocument(
                    content=doc.page_content[:300] + "..." if len(doc.page_content) > 300 else doc.page_content,
                    section=doc.metadata.get('section', ''),
                    metadata={'score': score}
                ))
            
            # 信頼度スコアを計算（最も関連性の高いドキュメントのスコアを使用）
            confidence = 1.0 - search_results[0][1] if search_results else 0.0
            
            return ChatResponse(
                answer=answer,
                sources=sources,
                confidence=min(max(confidence, 0.0), 1.0)
            )
            
        except Exception as e:
            logger.error(f"チャット処理中にエラーが発生しました: {e}")
            raise
    
    def is_ready(self) -> bool:
        """ベクトルストアが準備できているかチェック"""
        return self.vector_store is not None