from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy import desc, asc

from src.models.database import DatabaseManager, Session, Message


class SessionService:
    """セッション管理サービス"""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def create_session(self, title: Optional[str] = None) -> Dict[str, Any]:
        """新規セッション作成"""
        if not title:
            title = f"新しい会話 - {datetime.now().strftime('%Y/%m/%d %H:%M')}"

        with self.db_manager.get_session() as db:
            db_session = Session(title=title)
            db.add(db_session)
            db.commit()
            db.refresh(db_session)

            return {
                "id": db_session.id,
                "title": db_session.title,
                "created_at": db_session.created_at.isoformat(),
                "updated_at": db_session.updated_at.isoformat(),
            }

    def get_sessions(self) -> List[Dict[str, Any]]:
        """セッション一覧取得"""
        with self.db_manager.get_session() as db:
            sessions = db.query(Session).order_by(desc(Session.updated_at)).all()

            return [
                {
                    "id": session.id,
                    "title": session.title,
                    "created_at": session.created_at.isoformat(),
                    "updated_at": session.updated_at.isoformat(),
                }
                for session in sessions
            ]

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """セッション詳細取得"""
        with self.db_manager.get_session() as db:
            session = db.query(Session).filter(Session.id == session_id).first()

            if not session:
                return None

            return {
                "id": session.id,
                "title": session.title,
                "created_at": session.created_at.isoformat(),
                "updated_at": session.updated_at.isoformat(),
            }

    def delete_session(self, session_id: str) -> bool:
        """セッション削除"""
        with self.db_manager.get_session() as db:
            session = db.query(Session).filter(Session.id == session_id).first()

            if not session:
                return False

            db.delete(session)
            db.commit()
            return True

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """メッセージ追加"""
        with self.db_manager.get_session() as db:
            # セッション存在確認
            session = db.query(Session).filter(Session.id == session_id).first()
            if not session:
                return None

            # メッセージ作成
            message = Message(session_id=session_id, role=role, content=content)

            if metadata:
                message.set_metadata_dict(metadata)

            db.add(message)

            # セッションの更新日時を更新
            session.updated_at = datetime.utcnow()

            db.commit()
            db.refresh(message)

            return {
                "id": message.id,
                "session_id": message.session_id,
                "role": message.role,
                "content": message.content,
                "created_at": message.created_at.isoformat(),
                "metadata": message.get_metadata_dict(),
            }

    def get_messages(self, session_id: str) -> List[Dict[str, Any]]:
        """セッションのメッセージ一覧取得"""
        with self.db_manager.get_session() as db:
            messages = (
                db.query(Message)
                .filter(Message.session_id == session_id)
                .order_by(asc(Message.created_at))
                .all()
            )

            return [
                {
                    "id": message.id,
                    "session_id": message.session_id,
                    "role": message.role,
                    "content": message.content,
                    "created_at": message.created_at.isoformat(),
                    "metadata": message.get_metadata_dict(),
                }
                for message in messages
            ]

    def get_conversation_history(
        self, session_id: str, limit: Optional[int] = None
    ) -> List[Dict[str, str]]:
        """会話履歴を取得（RAG用フォーマット）"""
        with self.db_manager.get_session() as db:
            query = (
                db.query(Message)
                .filter(Message.session_id == session_id)
                .order_by(desc(Message.created_at))
            )

            if limit:
                query = query.limit(limit)

            messages = query.all()

            # 新しい順で取得したものを古い順に並び替え
            messages.reverse()

            return [
                {"role": message.role, "content": message.content}
                for message in messages
            ]

    def update_session_title(self, session_id: str, title: str) -> bool:
        """セッションタイトル更新"""
        with self.db_manager.get_session() as db:
            session = db.query(Session).filter(Session.id == session_id).first()

            if not session:
                return False

            session.title = title
            session.updated_at = datetime.utcnow()
            db.commit()
            return True
