"""
PostgreSQL リポジトリ実装
"""
import logging
from typing import List, Optional
from datetime import datetime
import psycopg2.extras

from ..domain.entity.user import User
from ..domain.entity.conversation import Conversation
from ..domain.entity.message import Message
from ..domain.repositories import UserRepository, ConversationRepository, MessageRepository
from .database import DatabaseConnectionPool

logger = logging.getLogger(__name__)


class PostgreSQLUserRepository(UserRepository):
    """PostgreSQL ユーザーリポジトリ"""

    def __init__(self, db_pool: DatabaseConnectionPool):
        self.db_pool = db_pool

    async def find_by_username(self, username: str) -> Optional[User]:
        """ユーザー名でユーザーを検索"""
        with self.db_pool.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    "SELECT id, username, email, password, created_at FROM users WHERE username = %s",
                    (username,)
                )
                row = cur.fetchone()
                
                if row:
                    return User(
                        id=row['id'],
                        username=row['username'],
                        email=row['email'],
                        password=row['password'],
                        created_at=row['created_at']
                    )
                return None

    async def save(self, user: User) -> User:
        """ユーザーを保存"""
        with self.db_pool.get_connection() as conn:
            with conn.cursor() as cur:
                # UPSERTの実装
                cur.execute("""
                    INSERT INTO users (id, username, email, password, created_at)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        username = EXCLUDED.username,
                        email = EXCLUDED.email,
                        password = EXCLUDED.password
                    """,
                    (user.id, user.username, user.email, user.password, user.created_at)
                )
                conn.commit()
                logger.debug(f"ユーザー保存: {user.username}")
                return user


class PostgreSQLConversationRepository(ConversationRepository):
    """PostgreSQL 会話リポジトリ"""

    def __init__(self, db_pool: DatabaseConnectionPool):
        self.db_pool = db_pool

    async def find_all(self) -> List[Conversation]:
        """全ての会話一覧を取得"""
        with self.db_pool.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT id, title, created_at, updated_at 
                    FROM conversations 
                    ORDER BY updated_at DESC
                    """)
                rows = cur.fetchall()
                
                return [
                    Conversation(
                        id=row['id'],
                        title=row['title'],
                        created_at=row['created_at'],
                        updated_at=row['updated_at']
                    )
                    for row in rows
                ]

    async def find_by_id(self, conversation_id: str) -> Optional[Conversation]:
        """IDで会話を検索"""
        with self.db_pool.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT id, title, created_at, updated_at 
                    FROM conversations 
                    WHERE id = %s
                    """,
                    (conversation_id,)
                )
                row = cur.fetchone()
                
                if row:
                    return Conversation(
                        id=row['id'],
                        title=row['title'],
                        created_at=row['created_at'],
                        updated_at=row['updated_at']
                    )
                return None

    async def save(self, conversation: Conversation) -> Conversation:
        """会話を保存"""
        with self.db_pool.get_connection() as conn:
            with conn.cursor() as cur:
                # UPSERTの実装
                cur.execute("""
                    INSERT INTO conversations (id, title, created_at, updated_at)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        title = EXCLUDED.title,
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    (conversation.id, conversation.title, 
                     conversation.created_at, conversation.updated_at)
                )
                conn.commit()
                logger.debug(f"会話保存: {conversation.title}")
                return conversation


class PostgreSQLMessageRepository(MessageRepository):
    """PostgreSQL メッセージリポジトリ"""

    def __init__(self, db_pool: DatabaseConnectionPool):
        self.db_pool = db_pool

    async def find_by_conversation_id(self, conversation_id: str) -> List[Message]:
        """会話IDでメッセージ一覧を取得"""
        with self.db_pool.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT id, conversation_id, content, role, created_at 
                    FROM messages 
                    WHERE conversation_id = %s 
                    ORDER BY created_at ASC
                    """,
                    (conversation_id,)
                )
                rows = cur.fetchall()
                
                return [
                    Message(
                        id=row['id'],
                        conversation_id=row['conversation_id'],
                        content=row['content'],
                        role=row['role'],
                        created_at=row['created_at']
                    )
                    for row in rows
                ]

    async def save(self, message: Message) -> Message:
        """メッセージを保存"""
        with self.db_pool.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO messages (id, conversation_id, content, role, created_at)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                    """,
                    (message.id, message.conversation_id, message.content, 
                     message.role, message.created_at)
                )
                conn.commit()
                logger.debug(f"メッセージ保存: {message.id}")
                return message

    async def save_batch(self, messages: List[Message]) -> List[Message]:
        """メッセージを一括保存"""
        if not messages:
            return []
            
        with self.db_pool.get_connection() as conn:
            with conn.cursor() as cur:
                # 一括挿入用のデータ準備
                values = [
                    (msg.id, msg.conversation_id, msg.content, msg.role, msg.created_at)
                    for msg in messages
                ]
                
                cur.executemany("""
                    INSERT INTO messages (id, conversation_id, content, role, created_at)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                    """,
                    values
                )
                conn.commit()
                logger.debug(f"メッセージ一括保存: {len(messages)}件")
                return messages