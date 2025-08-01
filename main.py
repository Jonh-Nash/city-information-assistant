"""
Main application entry point (connection-pool + lifespan)
"""
import sys
from contextlib import contextmanager, asynccontextmanager
import logging

import psycopg2
from psycopg2.pool import ThreadedConnectionPool
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import Field
from pydantic_settings import BaseSettings

# ---------------------------------------------------------------------------
# ログ設定
# ---------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 設定
# ---------------------------------------------------------------------------
class Settings(BaseSettings):
    """Application settings"""

    database_url: str = Field(..., env="DATABASE_URL", description="PostgreSQL 接続 URL")
    openai_api_key: str = Field(..., env="OPENAI_API_KEY", description="OpenAI API キー（オプション）")

    class Config:
        env_file = ".env"


def load_settings() -> 'Settings':
    """環境変数を読み込み、必須項目が揃っているか確認"""
    try:
        settings = Settings()
        logger.info("✓ 環境変数の読み込み成功")
        logger.info(f"✓ DATABASE_URL: {settings.database_url[:20]}…")
        logger.info(f"✓ OPENAI_API_KEY: {settings.openai_api_key[:20]}…")
        return settings
    except Exception as e:
        logger.error(f"✗ 環境変数の設定に問題があります: {e}")
        sys.exit(1)


settings = load_settings()

# ---------------------------------------------------------------------------
# Lifespan – アプリのスタートアップ & シャットダウン
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage startup/shutdown: initialise and close the connection pool."""

    logger.info("PostgreSQL connection pool initialising …")
    try:
        pool = ThreadedConnectionPool(minconn=1, maxconn=10, dsn=settings.database_url)
        # 接続テスト
        conn = pool.getconn()
        with conn.cursor() as cur:
            cur.execute("SELECT 1;")
        pool.putconn(conn)
        app.state.pool = pool
        logger.info("✓ Connection pool established")
    except Exception as e:
        logger.error(f"✗ Connection pool init failed: {e}")
        sys.exit(1)

    # --- アプリ稼働 ---
    try:
        yield
    finally:
        # シャットダウン処理
        pool: ThreadedConnectionPool = app.state.pool
        pool.closeall()
        logger.info("Connection pool closed")


# ---------------------------------------------------------------------------
# FastAPI アプリケーション
# ---------------------------------------------------------------------------
app = FastAPI(
    title="City Information Assistant",
    description="AI-powered city information and travel planning assistant",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# データベース接続依存性
# ---------------------------------------------------------------------------
@contextmanager
def _connection_from_pool():
    """プールからコネクションを借りて返す同期 contextmanager"""
    pool: ThreadedConnectionPool = app.state.pool
    conn = pool.getconn()
    try:
        yield conn
    finally:
        pool.putconn(conn)


def get_db_conn():
    """Depends 用ラッパー（generator based）"""
    with _connection_from_pool() as conn:
        yield conn


# ---------------------------------------------------------------------------
# ルーティング
# ---------------------------------------------------------------------------
@app.get("/")
async def root():
    return {"message": "City Information Assistant API", "status": "running"}


@app.get("/health")
def health_check(conn=Depends(get_db_conn)):
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1;")
        return {
            "status": "healthy",
            "database": "connected",
            "environment": "configured",
        }
    except Exception as e:
        logger.error(f"ヘルスチェックエラー: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")


# ---------------------------------------------------------------------------
# 開発用エントリポイント
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
