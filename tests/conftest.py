import tempfile
import pytest
from typing import Generator
from unittest.mock import Mock, patch

from src.config.settings import Settings


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """テスト用の設定オブジェクトを提供"""
    return Settings(
        openai_api_key="test_api_key",
        openai_model="gpt-4o-mini",
        openai_temperature=0.1,
        chroma_persist_directory="test_data/chroma",
        embedding_model_name="intfloat/multilingual-e5-large",
        spec_file_path="tests/fixtures/test_spec.md",
        chunk_size=500,
        chunk_overlap=100,
        debug=True,
    )


@pytest.fixture
def temp_dir() -> Generator[str, None, None]:
    """一時ディレクトリを提供"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def mock_openai_client():
    """OpenAI APIクライアントのモック"""
    with patch("openai.OpenAI") as mock_client:
        mock_instance = Mock()
        mock_client.return_value = mock_instance

        # ChatCompletion.create のモック応答
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "テスト回答です。"
        mock_instance.chat.completions.create.return_value = mock_response

        yield mock_instance


@pytest.fixture
def mock_embedding_service():
    """埋め込みサービスのモック"""
    with patch("src.services.embeddings.EmbeddingService") as mock_service:
        mock_instance = Mock()
        mock_service.return_value = mock_instance

        # ダミーの埋め込みベクトル
        mock_instance.embed_query.return_value = [0.1] * 1024
        mock_instance.embed_documents.return_value = [[0.1] * 1024, [0.2] * 1024]

        yield mock_instance


@pytest.fixture
def sample_documents():
    """テスト用のサンプルドキュメント"""
    return [
        {
            "content": "## **1. ゲーム概要**\n\nスゲリス・サーガは冒険RPGです。",
            "section": "## **1. ゲーム概要**",
            "subsection": "",
        },
        {
            "content": "### **1.1 基本システム**\n\nターン制バトルシステムを採用しています。",
            "section": "## **1. ゲーム概要**",
            "subsection": "### **1.1 基本システム**",
        },
    ]


@pytest.fixture
def test_spec_content():
    """テスト用の仕様書コンテンツ"""
    return """# スゲリス・サーガ 仕様書

## **1. ゲーム概要**

スゲリス・サーガは、ファンタジー世界を舞台とした冒険RPGゲームです。
プレイヤーは勇者となり、魔王を倒すことが最終目標となります。

### **1.1 基本システム**

- ターン制バトルシステム
- キャラクター成長システム
- アイテム収集・合成システム

### **1.2 ゲームモード**

- ストーリーモード
- フリーバトルモード
- オンライン対戦モード

## **2. キャラクター仕様**

### **2.1 主人公**

- 名前: 自由設定可能
- 職業: 戦士、魔法使い、僧侶から選択
- レベル上限: 99

### **2.2 能力値**

- HP: ヒットポイント
- MP: マジックポイント
- ATK: 攻撃力
- DEF: 防御力
- SPD: 素早さ

## **3. バトルシステム**

### **3.1 基本バトル**

1. プレイヤーターン
2. 敵ターン
3. 勝敗判定

### **3.2 スキルシステム**

- 各職業固有のスキル
- レベルアップで新スキル習得
- スキルポイント消費制
"""
