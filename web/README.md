# ゲーム仕様問い合わせBOT - WebUI

ゲーム仕様問い合わせBOTのWebアプリケーションフロントエンドです。Remixを使用してブラウザベースのチャットインターフェースを提供します。

## 概要

このWebアプリケーションは、FastAPIバックエンドと連携してゲーム仕様に関する質問に答えるチャットボットのユーザーインターフェースです。

### 主な機能

- 📱 **レスポンシブチャットUI**: PC・モバイル対応のチャットインターフェース
- 💬 **リアルタイムチャット**: スムーズなメッセージ送受信
- 📋 **ソース情報表示**: 回答の参照元情報を展開可能
- 🎯 **信頼度表示**: AIの回答信頼度を視覚的に表示
- 🌙 **ダークモード対応**: Tailwindのdark:クラスで対応済み
- ⌨️ **キーボードショートカット**: Enter送信、Shift+Enter改行

## 技術スタック

- **Framework**: [Remix](https://remix.run/) - フルスタックWebフレームワーク
- **UI Library**: [React](https://react.dev/) - UIライブラリ
- **Language**: [TypeScript](https://www.typescriptlang.org/) - 型安全なJavaScript
- **Styling**: [Tailwind CSS](https://tailwindcss.com/) - ユーティリティファーストCSS
- **Package Manager**: [Bun](https://bun.sh/) - 高速なJavaScriptランタイム
- **Build Tool**: [Vite](https://vitejs.dev/) - 高速ビルドツール

## 前提条件

- Node.js 20以上
- Bun パッケージマネージャー
- 稼働中のFastAPIバックエンド（localhost:8000）

## セットアップ

### 1. 依存関係のインストール

```bash
# webディレクトリに移動
cd web

# 依存関係をインストール
bun install
```

### 2. バックエンドの起動

Webアプリケーションを使用する前に、FastAPIバックエンドが稼働している必要があります：

```bash
# プロジェクトルートで実行
uv run python -m src.main
```

バックエンドが http://localhost:8000 で稼働していることを確認してください。

## 開発

### 開発サーバーの起動

```bash
# 開発サーバーを起動
bun run dev
```

開発サーバーは http://localhost:5173 で起動します。

### 利用可能なスクリプト

```bash
# 開発サーバー起動
bun run dev

# 本番ビルド
bun run build

# 本番サーバー起動（ビルド後）
bun run start

# 型チェック
bun run typecheck

# リンター実行
bun run lint
```

## プロジェクト構造

```
web/
├── app/                          # Remixアプリケーション
│   ├── components/              # Reactコンポーネント
│   │   ├── ChatInterface.tsx    # メインチャット画面
│   │   ├── MessageBubble.tsx    # メッセージ表示コンポーネント
│   │   ├── SourceInfo.tsx       # ソース情報表示
│   │   └── LoadingSpinner.tsx   # ローディング表示
│   ├── lib/                     # ユーティリティライブラリ
│   │   ├── api.ts              # APIクライアント
│   │   └── types.ts            # TypeScript型定義
│   ├── routes/                  # ページルート
│   │   └── _index.tsx          # ホームページ（チャット画面）
│   ├── root.tsx                # アプリケーションルート
│   └── tailwind.css            # Tailwindベーススタイル
├── public/                      # 静的ファイル
│   ├── favicon.ico
│   ├── logo-light.png
│   └── logo-dark.png
├── package.json                 # 依存関係定義
├── tailwind.config.ts          # Tailwind設定
├── tsconfig.json               # TypeScript設定
└── vite.config.ts              # Vite設定
```

## API統合

### APIクライアント

`app/lib/api.ts`のApiClientクラスを使用してバックエンドと通信：

```typescript
import { apiClient } from '../lib/api';

// チャットメッセージ送信
const response = await apiClient.chat({
  question: "質問内容",
  max_results: 3
});

// ヘルスチェック
const health = await apiClient.healthCheck();
```

### 型定義

`app/lib/types.ts`でAPIレスポンスの型が定義されています：

- `ChatRequest`: チャットリクエスト
- `ChatResponse`: チャット応答
- `SourceDocument`: ソース文書情報
- `Message`: UIメッセージ型

## スタイリング

### Tailwind CSS

- ユーティリティファーストアプローチ
- レスポンシブデザイン対応
- ダークモード対応（`dark:`プレフィックス）

### カスタマイズ

カスタマイズは`tailwind.config.ts`で行います：

```typescript
export default {
  content: ["./app/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      // カスタムテーマ設定
    },
  },
  plugins: [],
} satisfies Config;
```

## 開発ガイドライン

### コンポーネント設計

1. **単一責任**: 各コンポーネントは1つの責任を持つ
2. **再利用性**: 汎用的なコンポーネントは分離
3. **型安全性**: PropTypesではなくTypeScriptインターフェースを使用

### 状態管理

- シンプルな状態は`useState`を使用
- 複雑な状態は`useReducer`を検討
- グローバル状態が必要な場合はContext APIを使用

### エラーハンドリング

```typescript
try {
  const response = await apiClient.chat(request);
  // 成功処理
} catch (error) {
  // エラーハンドリング
  console.error('API Error:', error);
}
```

## デプロイ

### ビルド

```bash
# 本番ビルド
bun run build
```

### 本番実行

```bash
# 本番サーバー起動
bun run start
```

ビルド成果物は`build/`ディレクトリに生成されます。

## トラブルシューティング

### よくある問題

1. **APIが応答しない**
   - バックエンドが起動しているか確認
   - http://localhost:8000/health でヘルスチェック

2. **型エラー**
   - `bun run typecheck`で型チェック実行
   - `app/lib/types.ts`の型定義を確認

3. **スタイルが適用されない**
   - Tailwindクラスが正しいか確認
   - `tailwind.config.ts`の`content`パスを確認

### デバッグ

```bash
# 詳細ログ付きで開発サーバー起動
DEBUG=* bun run dev

# 型チェックのみ実行
bun run typecheck

# リンターでコード品質チェック
bun run lint
```

## 貢献

1. フィーチャーブランチを作成
2. 変更を実装
3. `bun run typecheck`と`bun run lint`を実行
4. プルリクエストを作成

## ライセンス

このプロジェクトは親プロジェクトと同じライセンスの下で公開されています。