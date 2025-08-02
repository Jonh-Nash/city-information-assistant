"""
共通の依存性注入関数
"""
from fastapi import Request
from ..infrastructure.database import DatabaseConnectionPool


def get_db_pool(request: Request) -> DatabaseConnectionPool:
    """FastAPIのapp.stateからデータベース接続プールを取得する依存性注入関数"""
    return request.app.state.db_pool