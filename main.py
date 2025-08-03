"""
Main application entry point
"""
import sys
from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.entrypoint.auth_routes import router as auth_router
from src.entrypoint.conversation_routes import router as conversation_router
from src.entrypoint.health_routes import router as health_router
from src.infrastructure.database import DatabaseConnectionPool
from src.infrastructure.settings import Settings

import os

# ---------------------------------------------------------------------------
# ログ設定
# ---------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 設定
# ---------------------------------------------------------------------------
def load_settings() -> Settings:
    """環境変数を読み込み、必須項目が揃っているか確認"""
    try:
        settings = Settings()
        logger.info("✓ 環境変数の読み込み成功")
        logger.info(f"✓ DATABASE_URL: {settings.database_url[:20]}…")
        logger.info(f"✓ OPENAI_API_KEY: {settings.openai_api_key[:20]}…")
        logger.info(f"✓ OPENWEATHER_API_KEY: {settings.openweather_api_key[:20]}…")
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

    # データベース接続プールを初期化
    db_pool = DatabaseConnectionPool(settings.database_url)
    try:
        db_pool.initialize()
        app.state.db_pool = db_pool
    except Exception as e:
        logger.error(f"✗ Database initialization failed: {e}")
        sys.exit(1)

    # --- アプリ稼働 ---
    try:
        yield
    finally:
        # シャットダウン処理
        db_pool.close()


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
# ルーティング登録
# ---------------------------------------------------------------------------
app.include_router(health_router)
#app.include_router(auth_router)
app.include_router(conversation_router)


# ---------------------------------------------------------------------------
# 開発用エントリポイント
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
