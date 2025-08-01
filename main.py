"""
Main application entry point
"""
import os
import sys
import psycopg2
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
import logging

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    """Application settings"""
    database_url: str = Field(..., env="DATABASE_URL", description="PostgreSQL接続URL")
    openai_api_key: str = Field(..., env="OPENAI_API_KEY", description="OpenAI APIキー（オプション）")
    
    class Config:
        env_file = ".env"

def check_environment_variables():
    """環境変数の設定確認"""
    logger.info("環境変数の確認を開始...")
    
    try:
        settings = Settings()
        logger.info("✓ 環境変数の読み込み成功")
        logger.info(f"✓ DATABASE_URL: {settings.database_url[:20]}...")
        logger.info(f"✓ OPENAI_API_KEY: {settings.openai_api_key[:20]}...")
            
        return settings
    except Exception as e:
        logger.error(f"✗ 環境変数の設定に問題があります: {e}")
        logger.error("必要な環境変数が設定されていません。.envファイルまたは環境変数を確認してください。")
        sys.exit(1)

def check_postgresql_connection(database_url: str):
    """PostgreSQL接続確認"""
    logger.info("PostgreSQL接続確認を開始...")
    
    try:
        # 接続テスト
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # 簡単なクエリテスト
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        logger.info(f"✓ PostgreSQL接続成功: {version[0][:50]}...")
        
        # 接続をクローズ
        cursor.close()
        conn.close()
        logger.info("✓ PostgreSQL接続テスト完了")
        
    except psycopg2.OperationalError as e:
        logger.error(f"✗ PostgreSQL接続エラー: {e}")
        logger.error("PostgreSQLサーバーが起動していない、または接続設定が間違っている可能性があります。")
        logger.error("docker-compose up -d postgres を実行してPostgreSQLを起動してください。")
        sys.exit(1)
    except Exception as e:
        logger.error(f"✗ 予期しないエラー: {e}")
        sys.exit(1)

# 起動時の確認処理
logger.info("=== City Information Assistant 起動確認 ===")
settings = check_environment_variables()
check_postgresql_connection(settings.database_url)
logger.info("✓ 全ての確認が完了しました。アプリケーションを起動します。")

# FastAPIアプリケーション設定
app = FastAPI(
    title="City Information Assistant",
    description="AI-powered city information and travel planning assistant",
    version="1.0.0"
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "City Information Assistant API", "status": "running"}

@app.get("/health")
async def health_check():
    """ヘルスチェックエンドポイント"""
    try:
        # PostgreSQL接続確認
        conn = psycopg2.connect(settings.database_url)
        cursor = conn.cursor()
        cursor.execute("SELECT 1;")
        cursor.close()
        conn.close()
        
        return {
            "status": "healthy",
            "database": "connected",
            "environment": "configured"
        }
    except Exception as e:
        logger.error(f"ヘルスチェックエラー: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)