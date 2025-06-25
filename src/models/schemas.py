from pydantic import BaseModel, Field
from typing import List, Optional


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, description="ユーザーからの質問")
    max_results: int = Field(3, ge=1, le=10, description="検索結果の最大数")


class SourceDocument(BaseModel):
    content: str = Field(..., description="ソースドキュメントの内容")
    section: str = Field(..., description="ドキュメントのセクション名")
    metadata: Optional[dict] = Field(default={}, description="追加のメタデータ")


class ChatResponse(BaseModel):
    answer: str = Field(..., description="AIによる回答")
    sources: List[SourceDocument] = Field(..., description="参照したソース情報")
    confidence: float = Field(..., ge=0.0, le=1.0, description="回答の信頼度スコア")


class HealthResponse(BaseModel):
    status: str = Field(..., description="サービスの状態")
    version: str = Field(..., description="APIバージョン")
    vector_store_ready: bool = Field(..., description="ベクトルストアの準備状態")