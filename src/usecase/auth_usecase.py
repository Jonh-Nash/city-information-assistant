"""
Authentication UseCase
"""
import uuid
from typing import Optional
from ..domain.entity.user import User
from ..domain.repositories import UserRepository
from .dtos import LoginInputDTO, LoginOutputDTO, UserOutputDTO


class AuthUseCase:
    """認証ユースケース"""

    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def login(self, input_dto: LoginInputDTO) -> Optional[LoginOutputDTO]:
        """
        ログイン処理
        """
        # ユーザーを検索
        user: User = await self.user_repository.find_by_username(input_dto.username)
        
        if user is None:
            return None

        if not user.verify_password(input_dto.password):
            return None
        
        access_token = f"mock-token-{uuid.uuid4()}"
        return LoginOutputDTO(
            access_token=access_token,
            user=UserOutputDTO.from_entity(user)
        )
