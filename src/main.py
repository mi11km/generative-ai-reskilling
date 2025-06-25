import logging
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from src.api.chat import router as chat_router
from src.config.settings import get_settings
from src.services.rag_service import RAGService

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーションのライフサイクル管理"""
    # 起動時
    logger.info("アプリケーションを起動しています...")
    settings = get_settings()
    
    # ベクトルストアの初期化を事前に実行
    try:
        logger.info("RAGサービスを初期化中...")
        rag_service = RAGService(settings)
        logger.info("RAGサービスの初期化が完了しました")
    except Exception as e:
        logger.error(f"RAGサービスの初期化に失敗しました: {e}")
        raise
    
    yield
    
    # 終了時
    logger.info("アプリケーションを終了しています...")


def create_app() -> FastAPI:
    """FastAPIアプリケーションを作成"""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.version,
        description="ゲーム仕様書に基づいて質問に回答するRAG API",
        lifespan=lifespan
    )
    
    # CORS設定
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # ルーターを登録
    app.include_router(chat_router)
    
    # ルートエンドポイント
    @app.get("/")
    async def root():
        return {
            "message": "Game Specification RAG API",
            "version": settings.version,
            "docs": "/docs"
        }
    
    return app


def main():
    """メインエントリーポイント"""
    settings = get_settings()
    
    # OpenAI APIキーのチェック
    if not settings.openai_api_key:
        logger.error("OPENAI_API_KEY環境変数が設定されていません")
        sys.exit(1)
    
    app = create_app()
    
    logger.info(f"サーバーを起動します: http://localhost:8000")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )


if __name__ == "__main__":
    main()
