from fastapi import APIRouter, HTTPException, Depends
from typing import Annotated, List
import logging

from src.models.schemas import (
    SessionCreate,
    SessionResponse,
    SessionUpdate,
    MessageResponse,
)
from src.services.session_service import SessionService
from src.models.database import get_database_manager_singleton

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["sessions"])


class SessionServiceContainer:
    """セッションサービスのコンテナクラス（シングルトンパターン）"""

    _instance: "SessionServiceContainer" = None
    _session_service: SessionService = None

    def __new__(cls) -> "SessionServiceContainer":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_or_create_session_service(self) -> SessionService:
        """セッションサービスを取得または作成"""
        if self._session_service is None:
            logger.info("新しいセッションサービスインスタンスを作成中...")
            db_manager = get_database_manager_singleton().get_database_manager()
            self._session_service = SessionService(db_manager)
            logger.info("セッションサービスインスタンスの作成が完了しました")
        return self._session_service

    def reset(self) -> None:
        """テスト用: インスタンスをリセット"""
        self._session_service = None


def get_session_service_container() -> SessionServiceContainer:
    """セッションサービスコンテナを取得"""
    return SessionServiceContainer()


def get_session_service(
    container: Annotated[
        SessionServiceContainer, Depends(get_session_service_container)
    ],
) -> SessionService:
    """セッションサービスのインスタンスを取得"""
    return container.get_or_create_session_service()


@router.post("/sessions", response_model=SessionResponse)
async def create_session(
    request: SessionCreate,
    session_service: Annotated[SessionService, Depends(get_session_service)],
) -> SessionResponse:
    """
    新規セッションを作成します。

    - **title**: セッションタイトル（省略可、自動生成されます）
    """
    try:
        logger.info(f"新規セッション作成リクエスト: {request.title}")
        session_data = session_service.create_session(request.title)
        logger.info(f"セッションを作成しました: {session_data['id']}")
        return SessionResponse(**session_data)
    except Exception as e:
        logger.error(f"セッション作成中にエラーが発生しました: {e}")
        raise HTTPException(status_code=500, detail="セッション作成に失敗しました")


@router.get("/sessions", response_model=List[SessionResponse])
async def get_sessions(
    session_service: Annotated[SessionService, Depends(get_session_service)],
) -> List[SessionResponse]:
    """
    セッション一覧を取得します。
    """
    try:
        sessions = session_service.get_sessions()
        return [SessionResponse(**session) for session in sessions]
    except Exception as e:
        logger.error(f"セッション一覧取得中にエラーが発生しました: {e}")
        raise HTTPException(
            status_code=500, detail="セッション一覧の取得に失敗しました"
        )


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    session_service: Annotated[SessionService, Depends(get_session_service)],
) -> SessionResponse:
    """
    指定されたセッションの詳細を取得します。

    - **session_id**: セッションID
    """
    try:
        session_data = session_service.get_session(session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail="セッションが見つかりません")
        return SessionResponse(**session_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"セッション取得中にエラーが発生しました: {e}")
        raise HTTPException(status_code=500, detail="セッションの取得に失敗しました")


@router.put("/sessions/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: str,
    request: SessionUpdate,
    session_service: Annotated[SessionService, Depends(get_session_service)],
) -> SessionResponse:
    """
    セッションのタイトルを更新します。

    - **session_id**: セッションID
    - **title**: 新しいタイトル
    """
    try:
        success = session_service.update_session_title(session_id, request.title)
        if not success:
            raise HTTPException(status_code=404, detail="セッションが見つかりません")

        session_data = session_service.get_session(session_id)
        return SessionResponse(**session_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"セッション更新中にエラーが発生しました: {e}")
        raise HTTPException(status_code=500, detail="セッションの更新に失敗しました")


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    session_service: Annotated[SessionService, Depends(get_session_service)],
) -> dict:
    """
    セッションを削除します。

    - **session_id**: セッションID
    """
    try:
        success = session_service.delete_session(session_id)
        if not success:
            raise HTTPException(status_code=404, detail="セッションが見つかりません")

        return {"message": "セッションが削除されました"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"セッション削除中にエラーが発生しました: {e}")
        raise HTTPException(status_code=500, detail="セッションの削除に失敗しました")


@router.get("/sessions/{session_id}/messages", response_model=List[MessageResponse])
async def get_session_messages(
    session_id: str,
    session_service: Annotated[SessionService, Depends(get_session_service)],
) -> List[MessageResponse]:
    """
    指定されたセッションのメッセージ履歴を取得します。

    - **session_id**: セッションID
    """
    try:
        # セッション存在確認
        session_data = session_service.get_session(session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail="セッションが見つかりません")

        messages = session_service.get_messages(session_id)
        return [MessageResponse(**message) for message in messages]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"メッセージ履歴取得中にエラーが発生しました: {e}")
        raise HTTPException(
            status_code=500, detail="メッセージ履歴の取得に失敗しました"
        )
