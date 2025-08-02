"""
Repository interfaces
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from .entities import User, Conversation, Message


class UserRepository(ABC):
    """ユーザーリポジトリインターフェース"""

    @abstractmethod
    async def find_by_username(self, username: str) -> Optional[User]:
        """ユーザー名でユーザーを検索"""
        pass

    @abstractmethod
    async def save(self, user: User) -> User:
        """ユーザーを保存"""
        pass


class ConversationRepository(ABC):
    """会話リポジトリインターフェース"""

    @abstractmethod
    async def find_by_user_id(self, user_id: str) -> List[Conversation]:
        """ユーザーIDで会話一覧を取得"""
        pass

    @abstractmethod
    async def find_by_id(self, conversation_id: str) -> Optional[Conversation]:
        """IDで会話を検索"""
        pass

    @abstractmethod
    async def save(self, conversation: Conversation) -> Conversation:
        """会話を保存"""
        pass

    @abstractmethod
    async def delete(self, conversation_id: str) -> bool:
        """会話を削除"""
        pass


class MessageRepository(ABC):
    """メッセージリポジトリインターフェース"""

    @abstractmethod
    async def find_by_conversation_id(self, conversation_id: str) -> List[Message]:
        """会話IDでメッセージ一覧を取得"""
        pass

    @abstractmethod
    async def save(self, message: Message) -> Message:
        """メッセージを保存"""
        pass

    @abstractmethod
    async def save_batch(self, messages: List[Message]) -> List[Message]:
        """メッセージを一括保存"""
        pass