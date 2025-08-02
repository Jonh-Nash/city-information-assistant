"""
Database connection and setup
"""
import logging
from contextlib import contextmanager
from psycopg2.pool import ThreadedConnectionPool

logger = logging.getLogger(__name__)


class DatabaseConnectionPool:
    """データベース接続プール管理"""

    def __init__(self, database_url: str):
        self.database_url = database_url
        self.pool: ThreadedConnectionPool = None

    def initialize(self):
        """接続プールを初期化"""
        logger.info("PostgreSQL connection pool initialising …")
        try:
            self.pool = ThreadedConnectionPool(minconn=1, maxconn=10, dsn=self.database_url)
            
            # 接続テスト
            conn = self.pool.getconn()
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")
            self.pool.putconn(conn)
            logger.info("✓ Connection pool established")
        except Exception as e:
            logger.error(f"✗ Connection pool init failed: {e}")
            raise

    def close(self):
        """接続プールを閉じる"""
        if self.pool:
            self.pool.closeall()
            logger.info("Connection pool closed")

    @contextmanager
    def get_connection(self):
        """プールからコネクションを借りて返す同期 contextmanager"""
        if not self.pool:
            raise RuntimeError("Connection pool not initialized")
        
        conn = self.pool.getconn()
        try:
            yield conn
        finally:
            self.pool.putconn(conn)