"""
Chat UseCase
"""
import uuid
from datetime import datetime
from typing import Optional
from ..domain.entity.message import Message
from ..domain.repositories import ConversationRepository, MessageRepository
from ..domain.agent.chat_agent import ChatAgent
from .dtos import MessageInputDTO, MessageResponseOutputDTO, MessageOutputDTO
from .dtos import ChatInputDTO, ChatResponseOutputDTO

class ChatUseCase:
    """チャットユースケース"""

    def __init__(
        self,
        conversation_repository: ConversationRepository,
        message_repository: MessageRepository,
        chat_agent: ChatAgent
    ):
        self.conversation_repository = conversation_repository
        self.message_repository = message_repository
        self.chat_agent = chat_agent

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
        """
        ChatAgentを使用してAIレスポンスを生成
        """
        # 会話履歴は簡単化のため現在は空で処理
        conversation_history = []
        
        # ChatAgentを使ってレスポンスを生成
        response = await self.chat_agent.chat(input_dto.content, conversation_history)
        
        # 天気関連のメッセージかどうかで思考過程を変える
        thinking = "天気情報を確認しています..." if "天気" in input_dto.content.lower() or "weather" in input_dto.content.lower() else "メッセージを処理しています..."
        
        # 現在は簡単化のためfunction_callsは空
        function_calls = []
        
        return ChatResponseOutputDTO(
            thinking=thinking,
            function_calls=function_calls,
            response=response
        )
        