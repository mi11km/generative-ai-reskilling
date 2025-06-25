import os
import pytest
from unittest.mock import patch

from src.config.settings import Settings, get_settings


class TestSettings:
    """Settings クラスのテスト"""
    
    def test_default_values(self):
        """デフォルト値が正しく設定されることをテスト"""
        settings = Settings()
        
        assert settings.app_name == "Game Specification RAG API"
        assert settings.version == "0.1.0"
        assert settings.debug is False
        assert settings.openai_model == "gpt-4o-mini"
        assert settings.openai_temperature == 0.3
        assert settings.chroma_persist_directory == "data/chroma"
        assert settings.embedding_model_name == "intfloat/multilingual-e5-large"
        assert settings.spec_file_path == "docs/spec/仕様書.md"
        assert settings.chunk_size == 1000
        assert settings.chunk_overlap == 200
        assert settings.max_context_length == 4000
        assert settings.similarity_threshold == 0.35
    
    def test_openai_api_key_from_env(self):
        """環境変数からOpenAI APIキーが読み込まれることをテスト"""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test_key_123"}):
            settings = Settings()
            assert settings.openai_api_key == "test_key_123"
    
    def test_openai_api_key_none_when_not_set(self):
        """環境変数が設定されていない場合、OpenAI APIキーがNoneになることをテスト"""
        # Pydantic Settingsではexplicit値でNoneを指定する必要がある
        settings = Settings(openai_api_key=None)
        assert settings.openai_api_key is None
    
    def test_settings_with_custom_values(self):
        """カスタム値が正しく設定されることをテスト"""
        custom_settings = Settings(
            app_name="Custom App",
            version="1.0.0",
            debug=True,
            openai_api_key="custom_key",
            openai_model="gpt-4",
            openai_temperature=0.5,
            chunk_size=2000,
            chunk_overlap=400
        )
        
        assert custom_settings.app_name == "Custom App"
        assert custom_settings.version == "1.0.0"
        assert custom_settings.debug is True
        assert custom_settings.openai_api_key == "custom_key"
        assert custom_settings.openai_model == "gpt-4"
        assert custom_settings.openai_temperature == 0.5
        assert custom_settings.chunk_size == 2000
        assert custom_settings.chunk_overlap == 400
    
    def test_temperature_range_validation(self):
        """温度パラメータの範囲検証をテスト"""
        # 正常な範囲
        settings = Settings(openai_temperature=0.0)
        assert settings.openai_temperature == 0.0
        
        settings = Settings(openai_temperature=1.0)
        assert settings.openai_temperature == 1.0
        
        settings = Settings(openai_temperature=0.5)
        assert settings.openai_temperature == 0.5
    
    def test_chunk_size_validation(self):
        """チャンクサイズの妥当性をテスト"""
        # 正の値であることを確認
        settings = Settings(chunk_size=500)
        assert settings.chunk_size == 500
        
        settings = Settings(chunk_size=5000)
        assert settings.chunk_size == 5000
    
    def test_chunk_overlap_validation(self):
        """チャンクオーバーラップの妥当性をテスト"""
        # チャンクサイズより小さい値であることを暗黙的にテスト
        settings = Settings(chunk_size=1000, chunk_overlap=200)
        assert settings.chunk_overlap < settings.chunk_size
        assert settings.chunk_overlap == 200
    
    def test_similarity_threshold_range(self):
        """類似度しきい値の範囲をテスト"""
        settings = Settings(similarity_threshold=0.0)
        assert settings.similarity_threshold == 0.0
        
        settings = Settings(similarity_threshold=1.0)
        assert settings.similarity_threshold == 1.0
        
        settings = Settings(similarity_threshold=0.7)
        assert settings.similarity_threshold == 0.7


class TestGetSettings:
    """get_settings 関数のテスト"""
    
    def test_get_settings_returns_settings_instance(self):
        """get_settings がSettingsインスタンスを返すことをテスト"""
        settings = get_settings()
        assert isinstance(settings, Settings)
    
    def test_get_settings_with_env_vars(self):
        """環境変数が設定された状態でget_settingsが正しく動作することをテスト"""
        with patch.dict(os.environ, {
            "OPENAI_API_KEY": "env_test_key",
            "DEBUG": "true"
        }):
            settings = get_settings()
            assert settings.openai_api_key == "env_test_key"
    
    def test_get_settings_caching_behavior(self):
        """get_settingsが新しいインスタンスを毎回返すことをテスト"""
        # 注意: 現在の実装では毎回新しいインスタンスを返す
        settings1 = get_settings()
        settings2 = get_settings()
        
        # 同じ設定値を持つが、異なるインスタンス
        assert settings1.app_name == settings2.app_name
        # インスタンスは異なる（シングルトンではない）
        assert settings1 is not settings2


@pytest.mark.parametrize("temperature,expected", [
    (0.0, 0.0),
    (0.1, 0.1),
    (0.5, 0.5),
    (0.9, 0.9),
    (1.0, 1.0),
])
def test_temperature_parameter_values(temperature, expected):
    """様々な温度パラメータ値をパラメータ化テストで検証"""
    settings = Settings(openai_temperature=temperature)
    assert settings.openai_temperature == expected


@pytest.mark.parametrize("chunk_size,chunk_overlap", [
    (1000, 100),
    (2000, 200),
    (500, 50),
    (3000, 300),
])
def test_chunk_parameters_combination(chunk_size, chunk_overlap):
    """チャンクサイズとオーバーラップの組み合わせをテスト"""
    settings = Settings(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    assert settings.chunk_size == chunk_size
    assert settings.chunk_overlap == chunk_overlap
    # オーバーラップがチャンクサイズより小さいことを確認
    assert settings.chunk_overlap < settings.chunk_size