"""
Conversation API routes
"""
import logging
from typing import List
from fastapi import APIRouter, HTTPException, Depends
from ..usecase.dtos import (
    ConversationOutputDTO,
    ConversationCreateInputDTO,
    MessageOutputDTO,
    MessageInputDTO,
    MessageResponseOutputDTO,
    ChatResponseOutputDTO,
)
from ..usecase.conversation_usecase import ConversationUseCase
from ..usecase.chat_usecase import ChatUseCase
from ..infrastructure.memory_repositories import (
    MemoryConversationRepository,
    MemoryMessageRepository
)
from ..infrastructure.llm.llm_factory import OpenAIFactory
from ..infrastructure.tool.wheather_tool_impl import WeatherToolImpl
from ..domain.agent.chat_agent import ChatAgent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/conversations", tags=["conversations"])


def get_conversation_usecase() -> ConversationUseCase:
    """会話ユースケースの依存性注入"""
    conversation_repository = MemoryConversationRepository()
    message_repository = MemoryMessageRepository()
    return ConversationUseCase(conversation_repository, message_repository)


def get_chat_agent() -> ChatAgent:
    """チャットエージェントの依存性注入"""
    # LLMインスタンスを作成
    llm = OpenAIFactory.create_llm_instance()
    
    # ツールのリストを作成
    tools = [
        WeatherToolImpl(),
        # 他のツールもここで追加可能
    ]
    
    return ChatAgent(llm, tools)


def get_chat_usecase() -> ChatUseCase:
    """チャットユースケースの依存性注入"""
    conversation_repository = MemoryConversationRepository()
    message_repository = MemoryMessageRepository()
    chat_agent = get_chat_agent()
    return ChatUseCase(conversation_repository, message_repository, chat_agent)


@router.get("", response_model=List[ConversationOutputDTO])
async def get_conversations(
    conversation_usecase: ConversationUseCase = Depends(get_conversation_usecase)
):
    """
    会話一覧取得API
    """
    logger.info("会話一覧を取得")
    
    # TODO: 実際の実装では認証情報からuser_idを取得
    user_id = "user-123"
    
    conversations = await conversation_usecase.get_conversations(user_id)
    return conversations


@router.post("", response_model=ConversationOutputDTO)
async def create_conversation(
    request: ConversationCreateInputDTO,
    conversation_usecase: ConversationUseCase = Depends(get_conversation_usecase)
):
    """
    会話作成API
    """
    logger.info(f"新しい会話を作成: title={request.title}")
    
    # TODO: 実際の実装では認証情報からuser_idを取得
    user_id = "user-123"
    
    conversation = await conversation_usecase.create_conversation(user_id, request)
    return conversation


@router.get("/{conversation_id}", response_model=ConversationOutputDTO)
async def get_conversation(
    conversation_id: str,
    conversation_usecase: ConversationUseCase = Depends(get_conversation_usecase)
):
    """
    特定の会話取得API
    """
    logger.info(f"会話を取得: conversation_id={conversation_id}")
    
    conversation = await conversation_usecase.get_conversation(conversation_id)
    
    if conversation is None:
        logger.warning(f"会話が見つかりません: conversation_id={conversation_id}")
        raise HTTPException(status_code=404, detail="会話が見つかりません")
    
    return conversation

@router.get("/{conversation_id}/messages", response_model=List[MessageOutputDTO])
async def get_messages(
    conversation_id: str,
    conversation_usecase: ConversationUseCase = Depends(get_conversation_usecase)
):
    """
    会話のメッセージ一覧取得API
    """
    logger.info(f"メッセージ一覧を取得: conversation_id={conversation_id}")
    
    messages = await conversation_usecase.get_messages(conversation_id)
    
    if messages is None:
        logger.warning(f"会話が見つかりません: conversation_id={conversation_id}")
        raise HTTPException(status_code=404, detail="会話が見つかりません")
    
    return messages


@router.post("/{conversation_id}/messages", response_model=MessageResponseOutputDTO)
async def create_message(
    conversation_id: str,
    request: MessageInputDTO,
    chat_usecase: ChatUseCase = Depends(get_chat_usecase)
):
    """
    メッセージ作成API
    """
    logger.info(f"メッセージを作成: conversation_id={conversation_id}, content={request.content}")
    
    result = await chat_usecase.send_message(conversation_id, request)
    
    if result is None:
        logger.warning(f"会話が見つかりません: conversation_id={conversation_id}")
        raise HTTPException(status_code=404, detail="会話が見つかりません")
    
    logger.info(f"メッセージを作成しました: user_message_id={result.user_message.id}")
    return result