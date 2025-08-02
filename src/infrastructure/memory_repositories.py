"""
In-memory repository implementations for mocking
"""
from typing import List, Optional, Dict
from datetime import datetime
from ..domain.entities import User, Conversation, Message
from ..domain.repositories import UserRepository, ConversationRepository, MessageRepository


class MemoryUserRepository(UserRepository):
    """メモリ上でユーザーを管理するリポジトリ"""

    def __init__(self):
        # モックユーザーを初期化
        self._users: Dict[str, User] = {
            "testuser": User(
                id="user-123",
                username="testuser",
                email="test@example.com",
                created_at=datetime.now()
            )
        }

    async def find_by_username(self, username: str) -> Optional[User]:
        """ユーザー名でユーザーを検索"""
        return self._users.get(username)

    async def save(self, user: User) -> User:
        """ユーザーを保存"""
        self._users[user.username] = user
        return user


class MemoryConversationRepository(ConversationRepository):
    """メモリ上で会話を管理するリポジトリ"""

    def __init__(self):
        # モック会話を初期化
        self._conversations: Dict[str, Conversation] = {
            "conv-1": Conversation(
                id="conv-1",
                user_id="user-123",
                title="東京の天気について",
                created_at=datetime.now(),
                updated_at=datetime.now()
            ),
            "conv-2": Conversation(
                id="conv-2",
                user_id="user-123",
                title="大阪の旅行計画",
                created_at=datetime.now(),
                updated_at=datetime.now()
            ),
            "conv-3": Conversation(
                id="conv-3",
                user_id="user-123",
                title="札幌の基本情報",
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        }

    async def find_by_user_id(self, user_id: str) -> List[Conversation]:
        """ユーザーIDで会話一覧を取得"""
        return [conv for conv in self._conversations.values() if conv.user_id == user_id]

    async def find_by_id(self, conversation_id: str) -> Optional[Conversation]:
        """IDで会話を検索"""
        return self._conversations.get(conversation_id)

    async def save(self, conversation: Conversation) -> Conversation:
        """会話を保存"""
        self._conversations[conversation.id] = conversation
        return conversation

    async def delete(self, conversation_id: str) -> bool:
        """会話を削除"""
        if conversation_id in self._conversations:
            del self._conversations[conversation_id]
            return True
        return False


class MemoryMessageRepository(MessageRepository):
    """メモリ上でメッセージを管理するリポジトリ"""

    def __init__(self):
        # モックメッセージを初期化
        self._messages: Dict[str, List[Message]] = {
            "conv-1": [
                Message(
                    id="msg-1-1",
                    conversation_id="conv-1",
                    content="東京の天気を教えてください",
                    role="user",
                    created_at=datetime.now()
                ),
                Message(
                    id="msg-1-2",
                    conversation_id="conv-1",
                    content="東京の現在の天気は晴れで、気温は25度です。今日は一日晴れの予報となっています。",
                    role="assistant",
                    created_at=datetime.now()
                )
            ],
            "conv-2": [
                Message(
                    id="msg-2-1",
                    conversation_id="conv-2",
                    content="大阪の2日間の旅行プランを立ててください",
                    role="user",
                    created_at=datetime.now()
                ),
                Message(
                    id="msg-2-2",
                    conversation_id="conv-2",
                    content="大阪の2日間旅行プランをご提案します。1日目：大阪城、道頓堀、心斎橋。2日目：ユニバーサル・スタジオ・ジャパンです。",
                    role="assistant",
                    created_at=datetime.now()
                )
            ],
            "conv-3": [
                Message(
                    id="msg-3-1",
                    conversation_id="conv-3",
                    content="札幌の基本情報を教えてください",
                    role="user",
                    created_at=datetime.now()
                ),
                Message(
                    id="msg-3-2",
                    conversation_id="conv-3",
                    content="札幌は北海道の道庁所在地で、人口約195万人の大都市です。時計台やすすきの、雪まつりで有名です。",
                    role="assistant",
                    created_at=datetime.now()
                )
            ]
        }

    async def find_by_conversation_id(self, conversation_id: str) -> List[Message]:
        """会話IDでメッセージ一覧を取得"""
        return self._messages.get(conversation_id, [])

    async def save(self, message: Message) -> Message:
        """メッセージを保存"""
        if message.conversation_id not in self._messages:
            self._messages[message.conversation_id] = []
        self._messages[message.conversation_id].append(message)
        return message

    async def save_batch(self, messages: List[Message]) -> List[Message]:
        """メッセージを一括保存"""
        saved_messages = []
        for message in messages:
            saved_message = await self.save(message)
            saved_messages.append(saved_message)
        return saved_messages