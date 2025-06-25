# 会話履歴機能設計ドキュメント

## 概要

現在の単発質問・回答システムから、継続的な対話が可能なチャットボットへの機能拡張を行う。

## 目的

- 前回の会話内容を考慮した文脈的な回答を実現
- ユーザーが自然な対話形式で質問を続けられるようにする
- 複数のセッションを管理し、話題ごとに会話を分離

## 要件

### 機能要件

1. **セッション管理**
   - 新規セッションの作成
   - 既存セッションの選択・切り替え
   - セッションの削除
   - セッションの一覧表示

2. **会話履歴**
   - 各セッション内の会話履歴の保存
   - 会話履歴を考慮した回答生成
   - 会話履歴の表示

3. **RAG機能拡張**
   - 会話履歴をコンテキストに含めた検索
   - 前回の質問・回答を考慮した回答生成

### 非機能要件

1. **パフォーマンス**
   - 会話履歴が長くなってもレスポンス速度を維持
   - トークン制限への対応

2. **ユーザビリティ**
   - 直感的なセッション管理UI
   - 会話履歴の視認性

## アーキテクチャ設計

### データベース設計

#### sessionsテーブル
```sql
CREATE TABLE sessions (
  id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### messagesテーブル
```sql
CREATE TABLE messages (
  id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL,
  role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
  content TEXT NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  metadata TEXT, -- JSON形式でソース情報等を保存
  FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);
```

### API設計

#### 新規エンドポイント

1. **POST /api/v1/sessions**
   - 新規セッション作成
   - レスポンス: `{"id": "session_id", "title": "自動生成タイトル"}`

2. **GET /api/v1/sessions**
   - セッション一覧取得
   - レスポンス: `[{"id": "session_id", "title": "タイトル", "created_at": "...", "updated_at": "..."}]`

3. **GET /api/v1/sessions/{session_id}/messages**
   - セッションの会話履歴取得
   - レスポンス: `[{"id": "message_id", "role": "user|assistant", "content": "...", "created_at": "...", "metadata": {...}}]`

4. **DELETE /api/v1/sessions/{session_id}**
   - セッション削除

#### 既存エンドポイント拡張

1. **POST /api/v1/chat**
   - リクエストに`session_id`を追加
   - 会話履歴を考慮した回答生成
   - レスポンスに`session_id`を追加

### フロントエンド設計

#### コンポーネント構成

1. **SessionManager**
   - セッション一覧表示
   - 新規セッション作成
   - セッション選択・削除

2. **ChatInterface（拡張）**
   - 現在のセッション表示
   - セッション切り替え機能

3. **SessionSidebar**
   - セッション一覧の表示
   - セッション管理操作

#### 状態管理

```typescript
interface SessionState {
  sessions: Session[];
  currentSessionId: string | null;
  isLoading: boolean;
}

interface Session {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  messages?: Message[];
}
```

## 実装方針

### フェーズ1: バックエンド基盤
1. データベースモデルの実装
2. セッション管理サービスの実装
3. APIエンドポイントの実装

### フェーズ2: RAG機能拡張
1. 会話履歴を考慮したプロンプト生成
2. コンテキスト長制限への対応
3. 既存chatエンドポイントの拡張

### フェーズ3: フロントエンド実装
1. セッション管理UI
2. 既存チャット画面の拡張
3. 状態管理の実装

## 技術的考慮事項

### トークン制限対応
- 会話履歴が長くなった場合の要約機能
- 重要な情報の優先的な保持
- 古い会話の段階的な削除

### セキュリティ
- セッションIDの適切な生成
- 不正なセッションアクセスの防止

### パフォーマンス
- 会話履歴の効率的な取得
- キャッシュ機能の検討
- データベースインデックスの最適化

## 今後の拡張可能性

- セッションの共有機能
- セッションのエクスポート機能
- 会話の検索機能
- ユーザー認証との統合