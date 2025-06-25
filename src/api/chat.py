from fastapi import APIRouter, HTTPException, Depends
from typing import Annotated
import logging
from functools import lru_cache

from src.models.schemas import ChatRequest, ChatResponse, HealthResponse
from src.services.rag_service import RAGService
from src.config.settings import Settings, get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["chat"])


class RAGServiceContainer:
    """RAGサービスのコンテナクラス（シングルトンパターン）"""
    
    _instance: 'RAGServiceContainer' = None
    _rag_service: RAGService = None
    
    def __new__(cls) -> 'RAGServiceContainer':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def get_or_create_rag_service(self, settings: Settings) -> RAGService:
        """RAGサービスを取得または作成"""
        if self._rag_service is None:
            logger.info("新しいRAGサービスインスタンスを作成中...")
            self._rag_service = RAGService(settings)
            logger.info("RAGサービスインスタンスの作成が完了しました")
        return self._rag_service
    
    def reset(self) -> None:
        """テスト用: インスタンスをリセット"""
        self._rag_service = None


def get_rag_service_container() -> RAGServiceContainer:
    """RAGサービスコンテナを取得"""
    return RAGServiceContainer()


def get_rag_service(
    settings: Annotated[Settings, Depends(get_settings)],
    container: Annotated[RAGServiceContainer, Depends(get_rag_service_container)]
) -> RAGService:
    """RAGサービスのインスタンスを取得"""
    return container.get_or_create_rag_service(settings)


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    rag_service: Annotated[RAGService, Depends(get_rag_service)]
) -> ChatResponse:
    """
    ユーザーの質問に対して、ゲーム仕様書から関連情報を検索し回答を生成します。
    
    - **question**: ユーザーからの質問
    - **max_results**: 検索結果の最大数（1-10、デフォルト: 3）
    """
    try:
        logger.info(f"チャットリクエストを受信: {request.question[:50]}...")
        response = rag_service.chat(request.question, request.max_results)
        logger.info("チャットレスポンスを生成しました")
        return response
    except Exception as e:
        logger.error(f"チャット処理中にエラーが発生しました: {e}")
        raise HTTPException(status_code=500, detail="内部サーバーエラーが発生しました")


@router.get("/health", response_model=HealthResponse)
async def health_check(
    settings: Annotated[Settings, Depends(get_settings)],
    rag_service: Annotated[RAGService, Depends(get_rag_service)]
) -> HealthResponse:
    """
    APIの健全性をチェックします。
    """
    return HealthResponse(
        status="healthy",
        version=settings.version,
        vector_store_ready=rag_service.is_ready()
    )