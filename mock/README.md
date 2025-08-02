# City Information Assistant - Frontend

このフロントエンドアプリケーションは、City Information Assistant の API を操作するための Next.js ベースの Web アプリケーションです。

## 機能

- 会話一覧の表示
- 新しい会話の作成
- リアルタイムメッセージ送受信（Server-Sent Events 対応）
- レスポンシブデザイン
- MarkDown 形式でのメッセージ表示

## セットアップ

### 1. 依存関係のインストール

```bash
cd mock
npm install
```

### 2. 環境変数の設定

`.env.local`ファイルを作成し、バックエンド API の URL を設定してください：

```bash
# .env.local
API_BASE_URL=http://localhost:8000
```

### 3. 開発サーバーの起動

```bash
npm run dev
```

ブラウザで http://localhost:3000 にアクセスして確認してください。

## バックエンド API の変更

API エンドポイントが変更される場合は、以下の手順で対応してください：

### 1. API ベース URL の変更

`.env.local`ファイルの`API_BASE_URL`を更新：

```bash
# 例: 本番環境のAPIを使用する場合
API_BASE_URL=https://api.example.com
```

### 2. API レスポンス形式の変更

バックエンドの DTO が変更された場合は、以下のファイルを更新してください：

- `types/api.ts` - TypeScript 型定義
- `utils/api.ts` - API 通信ロジック

### 3. 新しい API エンドポイントの追加

新しいエンドポイントを追加する場合：

1. `types/api.ts`に型定義を追加
2. `utils/api.ts`の`ApiClient`クラスにメソッドを追加
3. 必要に応じてコンポーネントを更新

## ディレクトリ構成

```
mock/
├── components/          # Reactコンポーネント
│   ├── Layout.tsx      # 共通レイアウト
│   ├── ConversationList.tsx  # 会話一覧
│   ├── MessageList.tsx       # メッセージ一覧
│   └── MessageInput.tsx      # メッセージ入力
├── pages/              # Next.jsページ
│   ├── _app.tsx       # アプリケーションルート
│   ├── index.tsx      # ホームページ（会話一覧）
│   └── conversations/
│       └── [id].tsx   # 会話詳細ページ
├── styles/            # スタイルシート
│   └── globals.css    # グローバルCSS
├── types/             # TypeScript型定義
│   └── api.ts        # API型定義
├── utils/             # ユーティリティ
│   └── api.ts        # API通信クライアント
└── package.json       # 依存関係とスクリプト
```

## API 仕様

バックエンド API は以下のエンドポイントを提供します：

### 会話管理

- `GET /conversations` - 会話一覧取得
- `POST /conversations` - 新しい会話作成
- `GET /conversations/{id}` - 特定の会話取得

### メッセージ管理

- `GET /conversations/{id}/messages` - メッセージ一覧取得
- `POST /conversations/{id}/messages` - メッセージ送信
- `POST /conversations/{id}/messages/stream` - ストリーミングメッセージ送信（SSE）

## 技術スタック

- **Next.js 14** - React フレームワーク
- **TypeScript** - 型安全な開発
- **Tailwind CSS** - スタイリング
- **Axios** - HTTP 通信（非ストリーミング）
- **Fetch API** - ストリーミング通信（SSE）
- **React Markdown** - マークダウン表示
- **date-fns** - 日付フォーマット

## トラブルシューティング

### バックエンド API に接続できない場合

1. バックエンドサーバーが起動しているか確認
2. `.env.local`の API_BASE_URL が正しいか確認
3. CORS の設定が正しいか確認（バックエンド側）

### ストリーミングメッセージが表示されない場合

1. ブラウザが SSE（Server-Sent Events）をサポートしているか確認
2. ネットワークで SSE がブロックされていないか確認
3. バックエンドのストリーミングエンドポイントが正常に動作しているか確認

## 開発

### ビルド

```bash
npm run build
```

### 本番サーバー起動

```bash
npm run start
```

### リント

```bash
npm run lint
```
