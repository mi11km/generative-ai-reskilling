from pydantic import BaseModel, Field
from typing import List, Optional


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, description="ユーザーからの質問")
    max_results: int = Field(3, ge=1, le=10, description="検索結果の最大数")
    session_id: Optional[str] = Field(
        None, description="セッションID（継続会話の場合）"
    )


class SourceDocument(BaseModel):
    content: str = Field(..., description="ソースドキュメントの内容")
    section: str = Field(..., description="ドキュメントのセクション名")
    metadata: Optional[dict] = Field(default={}, description="追加のメタデータ")


class ChatResponse(BaseModel):
    answer: str = Field(..., description="AIによる回答")
    sources: List[SourceDocument] = Field(..., description="参照したソース情報")
    confidence: float = Field(..., ge=0.0, le=1.0, description="回答の信頼度スコア")
    session_id: Optional[str] = Field(None, description="セッションID")


class HealthResponse(BaseModel):
    status: str = Field(..., description="サービスの状態")
    version: str = Field(..., description="APIバージョン")
    vector_store_ready: bool = Field(..., description="ベクトルストアの準備状態")


# セッション管理関連のスキーマ
class SessionCreate(BaseModel):
    title: Optional[str] = Field(None, description="セッションタイトル")


class SessionResponse(BaseModel):
    id: str = Field(..., description="セッションID")
    title: str = Field(..., description="セッションタイトル")
    created_at: str = Field(..., description="作成日時")
    updated_at: str = Field(..., description="更新日時")


class SessionUpdate(BaseModel):
    title: str = Field(..., min_length=1, description="セッションタイトル")


class MessageResponse(BaseModel):
    id: str = Field(..., description="メッセージID")
    session_id: str = Field(..., description="セッションID")
    role: str = Field(..., description="メッセージの役割（user/assistant）")
    content: str = Field(..., description="メッセージ内容")
    created_at: str = Field(..., description="作成日時")
    metadata: Optional[dict] = Field(default={}, description="追加のメタデータ")
