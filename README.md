# City Information Assistant

本リポジトリは都市情報を対話形式で提供する Web API のリファレンス実装です。テストはすべてメモリ上のリポジトリを用いており、外部データベースを必要としません。

## ローカルアプリケーション構築手順

### 1. コンテナの立ち上げ

```bash
docker compose up
```

### 2. コンテナ DB へのマイグレーション

ローカルの実行環境からコンテナに接続してマイグレーションを実行します。

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

マイグレーションを実行します。

```bash
python scripts/migrate_postgresql.py
```

テーブルを消したい時は以下コマンドです。

```bash
python scripts/migrate_postgresql.py --rollback
```

Web アプリケーションコンテナ(実態は API) に対して API を実行できるようになります。

### 3. API の実行

以下の流れで API を実行できます。

- POST /conversations: 会話を作成する
- POST /conversations/{conversation_id}/messages: 会話にメッセージを送信する
- GET /conversations/{conversation_id}/messages: 会話のメッセージ一覧を取得する

`/mock` にある Next.js から GUI で確認できます。

## ユースケーステスト

ローカルの実行環境で実行できます。venv などで Python 環境を作成してください。

```bash
pytest -q
```

## フロントエンド込みの実行

1. mock ディレクトリに移動

```bash
cd mock
```

2. 依存関係をインストール

```bash
npm install
```

3. 環境変数ファイルを作成

```bash
echo "API_BASE_URL=http://localhost:8000" > .env.local
```

4. 開発サーバーを起動

```bash
npm run dev

```
