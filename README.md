# ゲーム仕様問い合わせBOT

## 概要
チームメンバーがチャット形式で仕様を問い合わせできるAIチャットボットの開発レポジトリです。
ゲーム「スゲリス・サーガ」の仕様書（docs/spec/仕様書.md）を基に、RAG（Retrieval-Augmented Generation）技術を使用して正確な回答を生成します。

**📱 Webアプリケーション対応**: ブラウザで使いやすいチャットUIを提供し、APIとWebの両方でアクセス可能です。

## 機能

### 🎮 コア機能
- ゲーム仕様書から関連情報を検索
- OpenAI APIを使用した自然な回答生成
- 日本語対応の高精度なセマンティック検索
- 回答の信頼度スコア表示
- 参照元情報の提供

### 🌐 WebUI機能
- ブラウザベースのチャットインターフェース
- リアルタイムチャット体験
- レスポンシブデザイン（PC/モバイル対応）
- ソース情報の展開表示
- 信頼度の視覚的表示

### 🔧 API機能
- FastAPIによる高速なREST API
- OpenAPI/Swagger自動ドキュメント生成
- CORS設定済み（フロントエンド連携対応）

## セットアップ

### 前提条件

#### バックエンド（API）
- Python 3.13以上
- UV パッケージマネージャー
- OpenAI APIキー

#### フロントエンド（WebUI）
- Node.js 20以上
- Bun パッケージマネージャー

### インストール

#### バックエンド（API）
```bash
# 依存関係のインストール
uv sync

# 環境変数の設定
cp .env.example .env
# .envファイルを編集してOPENAI_API_KEYを設定
```

#### フロントエンド（WebUI）
```bash
# Webアプリケーションディレクトリに移動
cd web

# 依存関係のインストール
bun install
```

## 実行方法

### 🚀 クイックスタート（Webアプリケーション）

1. **バックエンドの起動**:
```bash
# APIサーバーの起動
uv run python -m src.main
```

2. **フロントエンドの起動**:
```bash
# 別のターミナルでWebアプリケーションディレクトリに移動
cd web

# 開発サーバーの起動
bun run dev
```

3. **アクセス**:
- **Webアプリケーション**: http://localhost:5173/
- **API**: http://localhost:8000
- **API ドキュメント**: http://localhost:8000/docs
- **ヘルスチェック**: http://localhost:8000/api/v1/health

### 📡 API単体での実行

```bash
# APIサーバーの起動
uv run python -m src.main
```

## API使用例

### チャットエンドポイント

```bash
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "ガチャの天井は何回ですか？",
    "max_results": 3
  }'
```

### レスポンス例

```json
{
  "answer": "ピックアップ召喚において、100回で天井交換が可能です。",
  "sources": [
    {
      "content": "ピックアップ召喚 | 精霊石 × 300 / 1 回 | ... | 100 回で天井交換。",
      "section": "## **2\\. ガチャ / キャラクター獲得**",
      "metadata": {"score": 0.85}
    }
  ],
  "confidence": 0.95
}
```

## プロジェクト構造

```
├── src/                    # バックエンド（API）
│   ├── main.py            # エントリーポイント
│   ├── api/               # APIエンドポイント
│   │   └── chat.py       # チャットエンドポイント
│   ├── services/          # ビジネスロジック
│   │   ├── document_loader.py  # ドキュメント読み込み
│   │   ├── embeddings.py       # 埋め込み生成
│   │   └── rag_service.py      # RAGロジック
│   ├── models/            # データモデル
│   │   └── schemas.py    # Pydanticモデル
│   └── config/            # 設定管理
│       └── settings.py   # 設定管理
├── web/                   # フロントエンド（WebUI）
│   ├── app/              # Remixアプリケーション
│   │   ├── components/   # Reactコンポーネント
│   │   │   ├── ChatInterface.tsx    # メインチャット画面
│   │   │   ├── MessageBubble.tsx    # メッセージ表示
│   │   │   ├── SourceInfo.tsx       # ソース情報表示
│   │   │   └── LoadingSpinner.tsx   # ローディング表示
│   │   ├── lib/          # ユーティリティ
│   │   │   ├── api.ts    # APIクライアント
│   │   │   └── types.ts  # 型定義
│   │   └── routes/       # ページルート
│   │       └── _index.tsx # ホームページ
│   └── package.json      # フロントエンド依存関係
├── docs/                  # ドキュメント
│   └── spec/             # ゲーム仕様書
│       └── 仕様書.md     # 知識ベース
└── data/                 # ベクトルストア（自動生成）
    └── chroma/           # ChromaDBファイル
```

## 技術スタック

### 🐍 バックエンド（API）
- **Python 3.13**: プログラミング言語
- **FastAPI**: Web フレームワーク
- **LangChain**: RAG実装フレームワーク
- **ChromaDB**: ベクトルデータベース
- **OpenAI API**: 言語モデル（GPT-4o-mini）
- **Sentence Transformers**: 日本語対応埋め込みモデル（multilingual-e5-large）
- **UV**: パッケージマネージャー

### 🌐 フロントエンド（WebUI）
- **Remix**: フルスタックWebフレームワーク
- **React**: UIライブラリ
- **TypeScript**: 型安全なJavaScript
- **Tailwind CSS**: CSSフレームワーク
- **Bun**: パッケージマネージャー・タスクランナー
- **Vite**: ビルドツール
