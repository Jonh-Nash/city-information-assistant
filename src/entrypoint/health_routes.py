"""
Health check API routes
"""
import logging
from fastapi import APIRouter, HTTPException, Depends
from ..infrastructure.database import DatabaseConnectionPool
from .dependencies import get_db_pool

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])

@router.get("/health")
def health_check(db_pool: DatabaseConnectionPool = Depends(get_db_pool)):
    """
    ヘルスチェックAPI
    """
    try:
        if db_pool:
            with db_pool.get_connection() as conn:
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


@router.get("/")
async def root():
    """
    ルートエンドポイント
    """
    return {"message": "City Information Assistant API", "status": "running"}