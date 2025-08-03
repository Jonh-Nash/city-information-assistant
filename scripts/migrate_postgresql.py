"""
PostgreSQL データベースマイグレーションスクリプト

このスクリプトはアプリケーションコードに依存せず、独立して実行できます。
コンテナ内でマイグレーションを実行する際に使用します。
pydantic-settingsを使用して.envファイルから環境変数を読み取ります。
"""
import logging
import psycopg2
from contextlib import contextmanager
from pydantic import Field
from pydantic_settings import BaseSettings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MigrationSettings(BaseSettings):
    """マイグレーション設定"""
    
    database_url: str = Field(..., env="DATABASE_URL", description="PostgreSQL 接続 URL")
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore"  # 余分なフィールドを無視
    }


# 設定を読み込み
settings = MigrationSettings()
logger.info("設定を読み込みました")

# テーブル作成SQL
CREATE_TABLES_SQL = """
-- ユーザーテーブル
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(50) PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(200) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 会話テーブル
CREATE TABLE IF NOT EXISTS conversations (
    id VARCHAR(50) PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,
    title VARCHAR(500) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- メッセージテーブル
CREATE TABLE IF NOT EXISTS messages (
    id VARCHAR(50) PRIMARY KEY,
    conversation_id VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
);

-- インデックス作成
CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_created_at ON conversations(created_at);
CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);

-- updated_at自動更新のためのトリガー関数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- conversations テーブルの updated_at 自動更新トリガー
DROP TRIGGER IF EXISTS update_conversations_updated_at ON conversations;
CREATE TRIGGER update_conversations_updated_at
    BEFORE UPDATE ON conversations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
"""

# テーブル削除SQL（ロールバック用）
DROP_TABLES_SQL = """
DROP TRIGGER IF EXISTS update_conversations_updated_at ON conversations;
DROP FUNCTION IF EXISTS update_updated_at_column();
DROP TABLE IF EXISTS messages CASCADE;
DROP TABLE IF EXISTS conversations CASCADE; 
DROP TABLE IF EXISTS users CASCADE;
"""

@contextmanager
def get_db_connection(database_url: str):
    """データベース接続のコンテキストマネージャー"""
    conn = None
    try:
        logger.info("PostgreSQL接続中...")
        conn = psycopg2.connect(database_url)
        logger.info("✓ PostgreSQL接続完了")
        yield conn
    except Exception as e:
        logger.error(f"✗ PostgreSQL接続失敗: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()
            logger.info("PostgreSQL接続終了")

def run_migration():
    """マイグレーションを実行"""
    try:
        database_url = settings.database_url
    except Exception as e:
        logger.error(f"DATABASE_URL 設定の読み込みに失敗しました: {e}")
        return False
    
    try:
        logger.info("マイグレーション開始...")
        
        with get_db_connection(database_url) as conn:
            with conn.cursor() as cur:
                # テーブル作成実行
                cur.execute(CREATE_TABLES_SQL)
                conn.commit()
                logger.info("✓ テーブル作成完了")
                
                # テーブル一覧を表示
                cur.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    ORDER BY table_name;
                """)
                tables = cur.fetchall()
                logger.info(f"作成されたテーブル: {[table[0] for table in tables]}")
        
        logger.info("✓ マイグレーション完了")
        return True
        
    except Exception as e:
        logger.error(f"✗ マイグレーション失敗: {e}")
        return False

def rollback_migration():
    """マイグレーションをロールバック"""
    try:
        database_url = settings.database_url
    except Exception as e:
        logger.error(f"DATABASE_URL 設定の読み込みに失敗しました: {e}")
        return False
    
    try:
        logger.info("ロールバック開始...")
        
        with get_db_connection(database_url) as conn:
            with conn.cursor() as cur:
                # テーブル削除実行
                cur.execute(DROP_TABLES_SQL)
                conn.commit()
                logger.info("✓ テーブル削除完了")
        
        logger.info("✓ ロールバック完了")
        return True
        
    except Exception as e:
        logger.error(f"✗ ロールバック失敗: {e}")
        return False

def main():
    """メイン関数"""
    import argparse
    parser = argparse.ArgumentParser(description="PostgreSQL マイグレーション")
    parser.add_argument("--rollback", action="store_true", help="マイグレーションをロールバック")
    args = parser.parse_args()
    
    if args.rollback:
        success = rollback_migration()
    else:
        success = run_migration()
    
    return 0 if success else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())