import pytest

from src.usecase.auth_usecase import AuthUseCase
from src.infrastructure.memory_repositories import MemoryUserRepository
from src.infrastructure.dtos import LoginInputDTO


@pytest.mark.asyncio
async def test_login_success():
    """正しい資格情報でログインに成功することを確認"""
    user_repo = MemoryUserRepository()
    usecase = AuthUseCase(user_repo)

    input_dto = LoginInputDTO(username="testuser", password="password")
    result = await usecase.login(input_dto)

    assert result is not None, "ログインが成功しNoneが返却されないこと"
    assert result.user.username == "testuser"
    assert result.access_token.startswith("mock-token-")


@pytest.mark.asyncio
async def test_login_failure_wrong_password():
    """パスワードが誤っている場合にNoneが返却されることを確認"""
    user_repo = MemoryUserRepository()
    usecase = AuthUseCase(user_repo)

    input_dto = LoginInputDTO(username="testuser", password="wrong")
    result = await usecase.login(input_dto)

    assert result is None


@pytest.mark.asyncio
async def test_login_failure_user_not_found():
    """存在しないユーザー名の場合にNoneが返却されることを確認"""
    user_repo = MemoryUserRepository()
    usecase = AuthUseCase(user_repo)

    input_dto = LoginInputDTO(username="unknown", password="password")
    result = await usecase.login(input_dto)

    assert result is None
