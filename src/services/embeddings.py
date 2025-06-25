from langchain_huggingface import HuggingFaceEmbeddings
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class EmbeddingService:
    def __init__(self, model_name: str = "intfloat/multilingual-e5-large"):
        self.model_name = model_name
        self._embeddings: Optional[HuggingFaceEmbeddings] = None

    @property
    def embeddings(self) -> HuggingFaceEmbeddings:
        """遅延初期化で埋め込みモデルを取得"""
        if self._embeddings is None:
            logger.info(f"埋め込みモデルを初期化中: {self.model_name}")
            self._embeddings = HuggingFaceEmbeddings(
                model_name=self.model_name,
                model_kwargs={"device": "cpu"},
                encode_kwargs={"normalize_embeddings": True},
            )
            logger.info("埋め込みモデルの初期化が完了しました")
        return self._embeddings

    def embed_query(self, text: str) -> list:
        """テキストを埋め込みベクトルに変換"""
        return self.embeddings.embed_query(text)

    def embed_documents(self, texts: list) -> list:
        """複数のテキストを埋め込みベクトルに変換"""
        return self.embeddings.embed_documents(texts)
