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
        
        # ChatAgentを使ってレスポンスを生成（レスポンス、thinking、function_callsを含む辞書を取得）
        chat_result = await self.chat_agent.chat(input_dto.content, conversation_history)
        
        return ChatResponseOutputDTO(
            thinking=chat_result["thinking"],
            function_calls=chat_result["function_calls"],
            response=chat_result["response"]
        )

    async def send_message_stream(self, conversation_id: str, input_dto: MessageInputDTO):
        """
        ストリーミング対応のメッセージ送信
        
        Args:
            conversation_id: 会話ID
            input_dto: メッセージ入力DTO
            
        Yields:
            各ノードの実行結果
        """
        # 会話が存在するか確認
        conversation = await self.conversation_repository.find_by_id(conversation_id)
        if conversation is None:
            yield {
                "event_type": "error",
                "node_name": "system",
                "status": "error",
                "message": "会話が見つかりません",
                "data": {"error": "Conversation not found"}
            }
            return
        
        # ユーザーメッセージを作成・保存
        user_message = Message(
            id=f"msg-{uuid.uuid4()}",
            conversation_id=conversation_id,
            content=input_dto.content,
            role="user",
            created_at=datetime.now()
        )
        await self.message_repository.save(user_message)
        
        # 会話履歴を取得
        messages = await self.message_repository.find_by_conversation_id(conversation_id)
        conversation_history = []
        if messages:
            for msg in messages:
                if msg.role == "user":
                    conversation_history.append({"role": "user", "content": msg.content})
                elif msg.role == "assistant":
                    conversation_history.append({"role": "assistant", "content": msg.content})
        
        # アシスタントの回答を格納する変数
        assistant_response = ""
        
        # ChatAgentのストリーミング処理を実行
        async for event in self.chat_agent.chat_stream(
            message=input_dto.content,
            conversation_history=conversation_history
        ):
            # final_responseイベントからアシスタントの回答を取得
            if event.get("event_type") == "final_response" and event.get("data", {}).get("response"):
                assistant_response = event["data"]["response"]
            yield event
        
        # アシスタントメッセージを保存
        if assistant_response:
            assistant_message = Message(
                id=f"msg-{uuid.uuid4()}",
                conversation_id=conversation_id,
                content=assistant_response,
                role="assistant",
                created_at=datetime.now()
            )
            await self.message_repository.save(assistant_message)
        
        # ストリーミング終了イベントを送信
        yield {
            "event_type": "completed",
            "node_name": "system", 
            "status": "completed",
            "message": "ストリーミング完了",
            "data": {}
        }
