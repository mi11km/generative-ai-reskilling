import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import create_engine, String, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Mapped, mapped_column
import json

Base = declarative_base()


class Session(Base):
    """セッションテーブル"""

    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    title: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # リレーション
    messages: Mapped[List["Message"]] = relationship(
        "Message", back_populates="session", cascade="all, delete-orphan"
    )


class Message(Base):
    """メッセージテーブル"""

    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    session_id: Mapped[str] = mapped_column(
        String, ForeignKey("sessions.id"), nullable=False
    )
    role: Mapped[str] = mapped_column(String, nullable=False)  # 'user' or 'assistant'
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    message_metadata: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # JSON形式

    # リレーション
    session: Mapped["Session"] = relationship("Session", back_populates="messages")

    def get_metadata_dict(self) -> dict:
        """メタデータをJSON形式で取得"""
        if self.message_metadata:
            try:
                return json.loads(self.message_metadata)
            except json.JSONDecodeError:
                return {}
        return {}

    def set_metadata_dict(self, metadata: dict) -> None:
        """メタデータをJSON形式で設定"""
        self.message_metadata = json.dumps(metadata, ensure_ascii=False)


class DatabaseManager:
    """データベース管理クラス"""

    def __init__(self, database_url: str = "sqlite:///./data/conversations.db"):
        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )
        self.create_tables()

    def create_tables(self):
        """テーブル作成"""
        Base.metadata.create_all(bind=self.engine)

    def get_session(self):
        """データベースセッション取得"""
        return self.SessionLocal()


class DatabaseManagerSingleton:
    """DatabaseManagerのシングルトンクラス"""
    
    _instance: Optional["DatabaseManagerSingleton"] = None
    _db_manager: Optional[DatabaseManager] = None
    
    def __new__(cls) -> "DatabaseManagerSingleton":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def get_database_manager(self, database_url: str = "sqlite:///./data/conversations.db") -> DatabaseManager:
        """DatabaseManagerのインスタンスを取得（シングルトン）"""
        if self._db_manager is None:
            self._db_manager = DatabaseManager(database_url)
        return self._db_manager
    
    def reset(self) -> None:
        """テスト用: インスタンスをリセット"""
        self._db_manager = None


def get_database_manager_singleton() -> DatabaseManagerSingleton:
    """DatabaseManagerSingletonのインスタンスを取得"""
    return DatabaseManagerSingleton()
