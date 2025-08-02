"""
Conversation UseCase
"""
from typing import List, Optional
import uuid
from datetime import datetime
from ..domain.entities import Conversation, Message
from ..domain.repositories import ConversationRepository, MessageRepository
from ..infrastructure.dtos import (
    ConversationOutputDTO,
    MessageOutputDTO,
    ConversationCreateInputDTO,
)


class ConversationUseCase:
    """会話ユースケース"""

    def __init__(
        self,
        conversation_repository: ConversationRepository,
        message_repository: MessageRepository
    ):
        self.conversation_repository = conversation_repository
        self.message_repository = message_repository

    async def get_conversations(self, user_id: str) -> List[ConversationOutputDTO]:
        """
        ユーザーの会話一覧を取得
        """
        conversations = await self.conversation_repository.find_by_user_id(user_id)
        return [ConversationOutputDTO.from_entity(conv) for conv in conversations]

    async def get_conversation(self, conversation_id: str) -> Optional[ConversationOutputDTO]:
        """
        特定の会話を取得
        """
        conversation = await self.conversation_repository.find_by_id(conversation_id)
        if conversation is None:
            return None
        return ConversationOutputDTO.from_entity(conversation)

    async def get_messages(self, conversation_id: str) -> Optional[List[MessageOutputDTO]]:
        """
        会話のメッセージ一覧を取得
        """
        # 会話が存在するか確認
        conversation = await self.conversation_repository.find_by_id(conversation_id)
        if conversation is None:
            return None
        
        # メッセージ一覧を取得
        messages = await self.message_repository.find_by_conversation_id(conversation_id)
        return [MessageOutputDTO.from_entity(msg) for msg in messages]


    async def create_conversation(self, user_id: str, input_dto: ConversationCreateInputDTO) -> ConversationOutputDTO:
        """
        会話を新規作成
        """
        new_conversation = Conversation(
            id=f"conv-{uuid.uuid4()}",
            user_id=user_id,
            title=input_dto.title,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        saved = await self.conversation_repository.save(new_conversation)
        return ConversationOutputDTO.from_entity(saved)