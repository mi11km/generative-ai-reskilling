# CLAUDE.md

※日本語で対応お願いします

## プロジェクト概要

このプロジェクトは、ゲーム開発チームメンバーがチャット形式でゲーム仕様を問い合わせできるRAG（Retrieval-Augmented Generation）チャットボットです。大容量のゲーム仕様書（268KB+の日本語マークダウン）から最新情報を検索・抽出し、コンテキストに基づいた回答を提供します。

**構成**: FastAPI バックエンド + Remix フロントエンドによるフルスタックWebアプリケーション

## 開発環境セットアップと実行コマンド

### 全体
```bash
# フォーマット
mise run format

# リント
mise run lint

# テストの実行
mise run test

# 開発サーバーの起動
mise run run-api
mise run run-web
```

### バックエンド（FastAPI）

```bash
# 依存関係のインストール（仮想環境の作成と依存パッケージのインストール）
uv sync

# メインアプリケーションの実行（FastAPIサーバー起動）
uv run python -m src.main

# フォーマット
uv run ruff format

# リント
uv run ruff check --fix

# Testの実行
uv run pytest tests/

# 新しい依存関係の追加
uv add <package-name>

# 依存関係の削除
uv remove <package-name>

# 依存関係の更新
uv lock --upgrade

# 環境変数の設定（必須）
# .env.exampleをコピーして.envファイルを作成し、APIキーを設定
cp .env.example .env
# .envファイルを編集してOPENAI_API_KEYを設定
```

### フロントエンド（Remix）

```bash
# webディレクトリに移動
cd web

# 依存関係のインストール
bun install

# 開発サーバーの起動
bun run dev

# 型チェック
bun run typecheck

# リンター実行
bun run lint

# フォーマット実行
bun run format

# テストの実行
bun run test

# ビルド
bun run build

# プロダクション実行
bun run start
```

## 開発フロー
基本的にテスト駆動開発を行ってください。
また、機能を追加する際は docs/design/ に設計ドキュメントを作成してから実装を行ってください。

### バックエンド開発
Pytestを用いたテスト駆動開発で開発を行ってください。 テストは`tests/`ディレクトリに配置されます。

下記点に注意して開発を進めてください。
- 可能な限り単体テストでカバーできるように、アーキテクチャや設計に配慮すること
- 外部APIとの接続をする必要があるテストは、モック化してテストを行うこと

### フロントエンド開発
- **パッケージマネージャー**: bunを使用（npmではなく）
- **型安全性**: TypeScriptで厳密な型定義を行う
- **スタイリング**: Tailwind CSSを使用
- **状態管理**: React hooksを基本とし、複雑な場合のみ外部ライブラリを検討
- **API通信**: web/app/lib/api.tsのApiClientクラスを使用
- **リンター・フォーマッター**: Biomeを使用（ESLintから移行済み）


## アーキテクチャ概要

### レイヤード構造
```
Presentation Layer (Remix WebUI)
    ↓
API Layer (FastAPI)
    ↓
Business Logic Layer (RAG Service)
    ↓
Data Layer (ChromaDB + Document Loader)
```

### 主要コンポーネント

**プレゼンテーション層（WebUI）**:
- `web/app/components/ChatInterface.tsx`: メインチャット画面
- `web/app/components/MessageBubble.tsx`: メッセージ表示コンポーネント
- `web/app/components/SourceInfo.tsx`: ソース情報表示
- `web/app/lib/api.ts`: APIクライアント
- `web/app/lib/types.ts`: TypeScript型定義

**API層**: 
- `src/api/chat.py`: チャットエンドポイント（`/api/v1/chat`）とヘルスチェック（`/api/v1/health`）
- `src/main.py`: FastAPIアプリケーションのエントリーポイント、CORS設定、ライフサイクル管理

**ビジネスロジック層**:
- `src/services/rag_service.py`: RAG実装のコア、ベクトル検索とLLM統合
- `src/services/document_loader.py`: マークダウンドキュメントの読み込みとインテリジェントチャンキング
- `src/services/embeddings.py`: 多言語埋め込みサービス（multilingual-e5-large使用）

**設定・モデル層**:
- `src/config/settings.py`: Pydantic Settingsを使用した設定管理
- `src/models/schemas.py`: リクエスト/レスポンスのPydanticモデル

### データフロー
1. ユーザークエリ → WebUI（React）
2. WebUI → FastAPI（/api/v1/chat）
3. RAGサービスがクエリを埋め込みベクトルに変換
4. ChromaDBで類似文書を検索
5. 検索結果をコンテキストとしてOpenAI APIに送信
6. 生成された回答 → FastAPI → WebUI → ユーザー表示

## 技術スタック

### バックエンド
- **言語**: Python 3.13+
- **パッケージマネージャー**: UV 0.7.14
- **Webフレームワーク**: FastAPI 0.104.0
- **LLM**: OpenAI API (GPT-4o-mini)
- **ベクトルDB**: ChromaDB 0.5.0
- **埋め込みモデル**: Sentence Transformers (multilingual-e5-large)
- **RAGフレームワーク**: LangChain

### フロントエンド
- **フレームワーク**: Remix (React)
- **言語**: TypeScript
- **スタイリング**: Tailwind CSS
- **パッケージマネージャー**: Bun
- **ビルドツール**: Vite
- **開発サーバー**: Remix Dev Server

## 重要な開発考慮事項

### ドキュメント処理
- `docs/spec/仕様書.md`が主要な知識ベース（268KB+の日本語コンテンツ）
- 日本語テキストの適切なチャンキング戦略が実装済み
- ベクトルストアは`data/`ディレクトリに永続化

### 環境変数
必須の環境変数：
- `OPENAI_API_KEY`: OpenAI APIキー

オプション設定：
- `EMBEDDING_MODEL`: 埋め込みモデル名（デフォルト: intfloat/multilingual-e5-large）
- `CHUNK_SIZE`: ドキュメントチャンクサイズ（デフォルト: 1000）
- `CHUNK_OVERLAP`: チャンクオーバーラップ（デフォルト: 200）

### 日本語対応
- プロジェクト全体が日本語対応
- 多言語埋め込みモデルを使用
- 日本語マークダウン文書の処理に最適化

### データ永続化
- ChromaDBデータは`data/`ディレクトリに保存
- `.gitignore`でベクトルストアファイルを除外
- 初回実行時に自動的にドキュメントをインデックス化

## APIエンドポイント

- `POST /api/v1/chat`: チャット機能（Body: `{"question": "質問内容", "max_results": 3}`）
- `GET /api/v1/health`: ヘルスチェック
- `GET /docs`: Swagger UI（API仕様）
- `GET /openapi.json`: OpenAPI仕様JSON

## 開発時の注意点

### バックエンド
1. **ベクトルストアの初期化**: 初回実行時に`docs/spec/`のドキュメントが自動的にインデックス化される
2. **依存関係管理**: UV を使用、`pip`ではなく`uv add/remove`を使用
3. **環境設定**: `.env`ファイルの設定が必須（OpenAI APIキー）
4. **日本語処理**: 全てのテキスト処理が日本語に対応済み

### フロントエンド
1. **パッケージマネージャー**: bunを使用、`npm`や`yarn`ではなく`bun install/add/remove`を使用
2. **API通信**: `web/app/lib/api.ts`のApiClientを使用してバックエンドと通信
3. **型安全性**: `web/app/lib/types.ts`で定義された型を必ず使用
4. **スタイリング**: Tailwind CSSクラスを使用、カスタムCSSは最小限に
5. **状態管理**: React hooksを基本とし、useStateとuseEffectで十分な場合が多い
6. **リンター・フォーマッター**: Biomeを使用、設定は`web/biome.json`で管理

### 開発サーバー起動順序
1. バックエンド（ポート8000）を先に起動
2. フロントエンド（ポート5173）を後に起動
3. ブラウザで http://localhost:5173/ にアクセス