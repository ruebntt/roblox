from typing import List, Optional, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete
from sqlalchemy.sql import func
from models import User, CaptchaAttempt, UserSession

class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: int) -> Optional[User]:
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalars().first()

    async def get_by_username(self, username: str) -> Optional[User]:
        result = await self.session.execute(select(User).where(User.username == username))
        return result.scalars().first()

    async def create(self, **kwargs) -> User:
        user = User(**kwargs)
        self.session.add(user)
        await self.session.flush()
        return user

    async def update(self, user_id: int, **kwargs) -> Optional[User]:
        await self.session.execute(update(User).where(User.id == user_id).values(**kwargs))
        return await self.get_by_id(user_id)

    async def delete(self, user_id: int) -> bool:
        result = await self.session.execute(delete(User).where(User.id == user_id))
        return result.rowcount > 0

    async def list_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        result = await self.session.execute(select(User).offset(skip).limit(limit))
        return result.scalars().all()

class CaptchaAttemptRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def log_attempt(self, user_id: Optional[int], captcha_type: str, success: bool,
                          response_data: dict, error_message: Optional[str], processing_time_ms: int) -> CaptchaAttempt:
        attempt = CaptchaAttempt(
            user_id=user_id,
            captcha_type=captcha_type,
            success=success,
            response_data=response_data,
            error_message=error_message,
            processing_time_ms=processing_time_ms,
            attempt_time=func.now()
        )
        self.session.add(attempt)
        await self.session.flush()
        return attempt

    async def get_recent_attempts(self, user_id: int, limit: int = 50) -> List[CaptchaAttempt]:
        result = await self.session.execute(
            select(CaptchaAttempt).where(CaptchaAttempt.user_id == user_id).order_by(CaptchaAttempt.attempt_time.desc()).limit(limit)
        )
        return result.scalars().all()

class UserSessionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_session(self, user_id: int, session_token: str, expires_at: datetime, metadata: dict) -> UserSession:
        new_session = UserSession(
            user_id=user_id,
            session_token=session_token,
            expires_at=expires_at,
            metadata=metadata,
            created_at=func.now(),
            is_active=True
        )
        self.session.add(new_session)
        await self.session.flush()
        return new_session

    async def get_by_token(self, token: str) -> Optional[UserSession]:
        result = await self.session.execute(select(UserSession).where(UserSession.session_token == token))
        return result.scalars().first()

    async def invalidate_session(self, session_id: int) -> bool:
        result = await self.session.execute(update(UserSession).where(UserSession.id == session_id).values(is_active=False))
        return result.rowcount > 0

    async def get_active_sessions(self, user_id: int) -> List[UserSession]:
        result = await self.session.execute(
            select(UserSession).where(UserSession.user_id == user_id, UserSession.is_active == True)
        )
        return result.scalars().all()
