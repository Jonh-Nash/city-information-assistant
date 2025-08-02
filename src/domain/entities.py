"""
Domain entities
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class User:
    """ユーザーエンティティ"""
    id: str
    username: str
    email: str
    created_at: datetime


@dataclass
class Conversation:
    """会話エンティティ"""
    id: str
    user_id: str
    title: str
    created_at: datetime
    updated_at: datetime


@dataclass
class Message:
    """メッセージエンティティ"""
    id: str
    conversation_id: str
    content: str
    role: str  # "user" or "assistant"
    created_at: datetime