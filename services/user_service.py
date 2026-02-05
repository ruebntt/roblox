from typing import Optional
from uuid import UUID

from database.repository import UserRepository
from api.schemas import UserCreate, UserInDB
from services.auth_service import AuthService

import asyncio

class UserService:
    def __init__(self, user_repo: UserRepository, auth_service: AuthService):
        self.user_repo = user_repo
        self.auth_service = auth_service

    async def create_user(self, user_data: UserCreate) -> UserInDB:
        existing_user = await self.user_repo.get_by_username(user_data.username)
        if existing_user:
            raise RuntimeError("Username already exists")
        hashed_password = self.auth_service.get_password_hash(user_data.password)
        user_in_db = await self.user_repo.create_user(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password
        )
        return user_in_db

    async def get_user(self, user_id: UUID) -> Optional[UserInDB]:
        user = await self.user_repo.get_by_id(user_id)
        return user

    async def get_user_by_username(self, username: str) -> Optional[UserInDB]:
        user = await self.user_repo.get_by_username(username)
        return user

    async def update_user(self, user_id: UUID, update_data: dict) -> UserInDB:
        user = await self.user_repo.update_user(user_id, update_data)
        return user

    async def delete_user(self, user_id: UUID):
        await self.user_repo.delete_user(user_id)
