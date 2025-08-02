"""
Chat UseCase
"""
import uuid
from datetime import datetime
from typing import Optional
from ..domain.entities import Message
from ..domain.repositories import ConversationRepository, MessageRepository
from .dtos import MessageInputDTO, MessageResponseOutputDTO, MessageOutputDTO


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
    ) -> Optional[MessageResponseOutputDTO]:
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

        # AIレスポンスを生成（モック実装）
        assistant_content = self._generate_mock_response(input_dto.content)
        assistant_message = Message(
            id=f"msg-{uuid.uuid4()}",
            conversation_id=conversation_id,
            content=assistant_content,
            role="assistant",
            created_at=datetime.now()
        )

        # メッセージを保存
        saved_messages = await self.message_repository.save_batch([user_message, assistant_message])

        return MessageResponseOutputDTO(
            user_message=MessageOutputDTO.from_entity(saved_messages[0]),
            assistant_message=MessageOutputDTO.from_entity(saved_messages[1])
        )

    def _generate_mock_response(self, user_content: str) -> str:
        """
        ユーザーの入力に基づいてモックAIレスポンスを生成
        TODO: 実際の実装ではChatAgentドメインサービスを使用
        """
        content_lower = user_content.lower()
        
        if "天気" in content_lower:
            return "天気情報を取得します。現在、晴れで気温は快適です。詳細な天気予報をお調べしますか？"
        elif "時間" in content_lower or "時刻" in content_lower:
            return "現在の時刻を確認します。日本時間で午後2時30分です。"
        elif "旅行" in content_lower or "観光" in content_lower:
            return "素晴らしい旅行プランを立てるお手伝いをします。どちらの都市に興味がおありですか？"
        elif "情報" in content_lower:
            return "都市の基本情報をお調べします。人口、気候、名所などの詳細情報をご提供できます。"
        else:
            return f"ご質問「{user_content}」について調べています。都市の天気、時刻、基本情報、旅行計画などのご相談を承ります。"