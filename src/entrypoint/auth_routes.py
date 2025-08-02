"""
Authentication API routes
"""
import logging
from fastapi import APIRouter, HTTPException, Depends
from ..infrastructure.dtos import LoginInputDTO, LoginOutputDTO
from ..usecase.auth_usecase import AuthUseCase
from ..infrastructure.memory_repositories import MemoryUserRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["authentication"])


def get_auth_usecase() -> AuthUseCase:
    """認証ユースケースの依存性注入"""
    user_repository = MemoryUserRepository()
    return AuthUseCase(user_repository)


@router.post("/login", response_model=LoginOutputDTO)
async def login(
    request: LoginInputDTO,
    auth_usecase: AuthUseCase = Depends(get_auth_usecase)
):
    """
    ユーザーログインAPI
    """
    logger.info(f"ログイン試行: username={request.username}")
    
    result = await auth_usecase.login(request)
    
    if result is None:
        logger.warning(f"ログイン失敗: username={request.username}")
        raise HTTPException(status_code=401, detail="認証に失敗しました")
    
    logger.info(f"ログイン成功: user_id={result.user.id}")
    return result