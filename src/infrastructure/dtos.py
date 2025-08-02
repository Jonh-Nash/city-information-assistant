"""
Data Transfer Objects for input/output
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List
from ..domain.entities import User, Conversation, Message


# Input DTOs
class LoginInputDTO(BaseModel):
    """ログイン入力DTO"""
    username: str = Field(..., description="ユーザー名")
    password: str = Field(..., description="パスワード")


class MessageInputDTO(BaseModel):
    """メッセージ作成入力DTO"""
    content: str = Field(..., description="メッセージ内容")


# Output DTOs
class UserOutputDTO(BaseModel):
    """ユーザー出力DTO"""
    id: str = Field(..., description="ユーザーID")
    username: str = Field(..., description="ユーザー名")
    email: str = Field(..., description="メールアドレス")
    created_at: datetime = Field(..., description="作成日時")

    @classmethod
    def from_entity(cls, entity: User) -> "UserOutputDTO":
        return cls(
            id=entity.id,
            username=entity.username,
            email=entity.email,
            created_at=entity.created_at
        )


class ConversationOutputDTO(BaseModel):
    """会話出力DTO"""
    id: str = Field(..., description="会話ID")
    user_id: str = Field(..., description="ユーザーID")
    title: str = Field(..., description="会話タイトル")
    created_at: datetime = Field(..., description="作成日時")
    updated_at: datetime = Field(..., description="更新日時")

    @classmethod
    def from_entity(cls, entity: Conversation) -> "ConversationOutputDTO":
        return cls(
            id=entity.id,
            user_id=entity.user_id,
            title=entity.title,
            created_at=entity.created_at,
            updated_at=entity.updated_at
        )


class MessageOutputDTO(BaseModel):
    """メッセージ出力DTO"""
    id: str = Field(..., description="メッセージID")
    conversation_id: str = Field(..., description="会話ID")
    content: str = Field(..., description="メッセージ内容")
    role: str = Field(..., description="メッセージの役割（user/assistant）")
    created_at: datetime = Field(..., description="作成日時")

    @classmethod
    def from_entity(cls, entity: Message) -> "MessageOutputDTO":
        return cls(
            id=entity.id,
            conversation_id=entity.conversation_id,
            content=entity.content,
            role=entity.role,
            created_at=entity.created_at
        )


class LoginOutputDTO(BaseModel):
    """ログイン出力DTO"""
    access_token: str = Field(..., description="アクセストークン")
    user: UserOutputDTO = Field(..., description="ユーザー情報")


class MessageResponseOutputDTO(BaseModel):
    """メッセージ作成レスポンス出力DTO"""
    user_message: MessageOutputDTO = Field(..., description="ユーザーメッセージ")
    assistant_message: MessageOutputDTO = Field(..., description="AIアシスタントメッセージ")