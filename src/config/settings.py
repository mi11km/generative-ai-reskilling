from pydantic_settings import BaseSettings
from typing import Optional
import os

from .prompts import PromptTemplates, get_default_prompt_templates


class Settings(BaseSettings):
    # API設定
    app_name: str = "Game Specification RAG API"
    version: str = "0.1.0"
    debug: bool = False
    
    # OpenAI設定
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o-mini"
    openai_temperature: float = 0.3
    
    # ベクトルストア設定
    chroma_persist_directory: str = "data/chroma"
    embedding_model_name: str = "intfloat/multilingual-e5-large"
    
    # ドキュメント設定
    spec_file_path: str = "docs/spec/仕様書.md"
    chunk_size: int = 1000
    chunk_overlap: int = 200
    
    # RAG設定
    max_context_length: int = 4000
    similarity_threshold: float = 0.35
    
    # プロンプト設定
    game_name: str = "スゲリス・サーガ"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
    
    @property
    def prompt_templates(self) -> PromptTemplates:
        """プロンプトテンプレートを取得"""
        return get_default_prompt_templates()


def get_settings() -> Settings:
    return Settings()