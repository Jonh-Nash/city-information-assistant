"""
Chat UseCase
"""
import uuid
from datetime import datetime
from typing import Optional
from ..domain.entity.message import Message
from ..domain.repositories import ConversationRepository, MessageRepository
from .dtos import MessageInputDTO, MessageResponseOutputDTO, MessageOutputDTO
from .dtos import ChatInputDTO, ChatResponseOutputDTO

class ChatUseCase:
    """チャットユースケース"""

    def __init__(
        self,
        conversation_repository: ConversationRepository,
        message_repository: MessageRepository
    ):
        self.conversation_repository = conversation_repository
        self.message_repository = message_repository

    async def send_message(
        self, 
        conversation_id: str, 
        input_dto: MessageInputDTO
    ) -> MessageResponseOutputDTO:
        """
        メッセージを送信してAIレスポンスを取得
        """
        # 会話が存在するか確認
        conversation = await self.conversation_repository.find_by_id(conversation_id)
        if conversation is None:
            return None

        # ユーザーメッセージを作成
        user_message = Message(
            id=f"msg-{uuid.uuid4()}",
            conversation_id=conversation_id,
            content=input_dto.content,
            role="user",
            created_at=datetime.now()
        )

        # AIレスポンスを生成
        assistant_content = await self.generate_ai_response(ChatInputDTO(content=input_dto.content))
        assistant_message = Message(
            id=f"msg-{uuid.uuid4()}",
            conversation_id=conversation_id,
            content=assistant_content.response,
            role="assistant",
            created_at=datetime.now()
        )

        # メッセージを保存
        saved_messages = await self.message_repository.save_batch([user_message, assistant_message])

        return MessageResponseOutputDTO(
            user_message=MessageOutputDTO.from_entity(saved_messages[0]),
            assistant_message=assistant_content
        )

    async def generate_ai_response(self, input_dto: ChatInputDTO) -> ChatResponseOutputDTO:
        content_lower = input_dto.content.lower()
        # domain/agentのAgentを呼び出して、回答を生成。domain/agent/toolやdomain/agent/llmにあるインターフェースを使用する。ToolやLLMの実装は、infrastructure/toolやinfrastructure/llmにある。
        return ChatResponseOutputDTO(
            thinking="こんにちは！",
            function_calls=[],
            response="こんにちは！"
        )
        