import pytest

from src.usecase.conversation_usecase import ConversationUseCase
from src.infrastructure.memory_repositories import (
    MemoryConversationRepository,
    MemoryMessageRepository,
)
from src.usecase.dtos import ConversationCreateInputDTO

# 共通で使用するユーザーID（MemoryConversationRepository で既に存在する）
USER_ID = "user-123"

@pytest.fixture()
def usecase():
    conv_repo = MemoryConversationRepository()
    msg_repo = MemoryMessageRepository()
    return ConversationUseCase(conv_repo, msg_repo)


@pytest.mark.asyncio
async def test_get_conversations(usecase):
    """ユーザーの会話一覧を取得できることを確認"""
    conversations = await usecase.get_conversations(USER_ID)

    # MemoryConversationRepository では３件の会話が用意されている
    assert len(conversations) == 3
    titles = [c.title for c in conversations]
    assert "東京の天気について" in titles
    assert "大阪の旅行計画" in titles


@pytest.mark.asyncio
async def test_get_conversation_success(usecase):
    """特定の会話を取得できることを確認"""
    conv = await usecase.get_conversation("conv-1")

    assert conv is not None
    assert conv.id == "conv-1"
    assert conv.title == "東京の天気について"


@pytest.mark.asyncio
async def test_get_conversation_not_found(usecase):
    """存在しない会話IDの場合 None が返却されることを確認"""
    conv = await usecase.get_conversation("unknown")
    assert conv is None


@pytest.mark.asyncio
async def test_get_messages_success(usecase):
    """会話に紐づくメッセージ一覧が取得できることを確認"""
    messages = await usecase.get_messages("conv-1")
    assert messages is not None
    # MemoryMessageRepository では conv-1 に２件のメッセージがある
    assert len(messages) == 2
    assert messages[0].role == "user"
    assert messages[1].role == "assistant"


@pytest.mark.asyncio
async def test_get_messages_conversation_not_found(usecase):
    """存在しない会話IDの場合 None が返却されることを確認"""
    messages = await usecase.get_messages("unknown")
    assert messages is None


@pytest.mark.asyncio
async def test_create_conversation(usecase):
    """新しい会話を作成できることを確認"""
    input_dto = ConversationCreateInputDTO(title="新しい会話タイトル")
    conv_dto = await usecase.create_conversation(USER_ID, input_dto)

    assert conv_dto.title == "新しい会話タイトル"
    assert conv_dto.user_id == USER_ID

    # 作成した会話がリポジトリに保存されていることを確認
    saved_conv = await usecase.conversation_repository.find_by_id(conv_dto.id)
    assert saved_conv is not None
