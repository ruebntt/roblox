from fastapi import Depends, HTTPException, Request, Header
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from pydantic import ValidationError
from typing import Optional
import logging
import asyncio

from database.repository import UserRepository
from services.auth_service import AuthService
from captcha_solver.captcha_api import CaptchaAPIClient
from config.config import get_config

logger = logging.getLogger("api_dependencies")
logger.setLevel(logging.INFO)

async def get_db_session() -> "AsyncSession":
    from database.db import async_session_factory
    async with async_session_factory() as session:
        yield session

def get_user_repository(session=Depends(get_db_session)) -> UserRepository:
    return UserRepository(session)

def get_auth_service(
    user_repo: UserRepository = Depends(get_user_repository),
    secret_key: str = Depends(lambda: get_config().SECRET_KEY),
    algorithm: str = "HS256",
    token_expiry: int = 3600
) -> AuthService:
    return AuthService(user_repo, secret_key, algorithm, token_expiry)

# Зависимость для проверки Bearer токена
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token", auto_error=True)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        user_data = await AuthService.verify_token(token, secret=get_config().SECRET_KEY)
        if not user_data:
            raise HTTPException(status_code=401, detail="Некорректный или просроченный токен")
        return user_data
    except ValidationError as e:
        logger.error(f"Validation error during token decoding: {e}")
        raise HTTPException(status_code=401, detail="Ошибка аутентификации")

def get_captcha_client() -> CaptchaAPIClient:
    api_key = get_config().CAPTCHA_API_KEY
    if not api_key:
        raise RuntimeError("CAPTCHA API ключ не настроен")
    return CaptchaAPIClient(api_key=api_key)

async def log_request(request: Request):
    logger.info(f"Incoming request: {request.method} {request.url}")
    response = await request.app.middleware_stack(request)
    logger.info(f"Response status: {response.status_code}")
    return response
