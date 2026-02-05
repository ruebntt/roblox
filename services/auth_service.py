from typing import Optional
from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer

from database.repository import UserRepository
from config.config import settings

from api.schemas import UserCreate, UserInDB

import aioredis

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class JWTManager:
    def __init__(self, secret_key: str, algorithm: str = "HS256", expiration_minutes: int = 60):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.expiration_minutes = expiration_minutes

    def create_access_token(self, data: dict) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.expiration_minutes)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def verify_token(self, token: str) -> dict:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError as e:
            raise HTTPException(status_code=401, detail="Invalid token") from e

jwt_manager = JWTManager(settings.SECRET_KEY)

class AuthService:
    def __init__(self, user_repo: UserRepository, redis_client: aioredis.Redis):
        self.user_repo = user_repo
        self.redis = redis_client

    async def authenticate_user(self, username: str, password: str) -> Optional[UserInDB]:
        user = await self.user_repo.get_by_username(username)
        if not user:
            return None
        if not self.verify_password(password, user.hashed_password):
            return None
        return user

    async def login(self, username: str, password: str) -> str:
        user = await self.authenticate_user(username, password)
        if not user:
            raise HTTPException(status_code=400, detail="Incorrect username or password")
        token = jwt_manager.create_access_token({"sub": user.username, "user_id": str(user.id)})
        await self.redis.set(f"user_session:{user.id}", token, ex=3600)
        return token

    async def get_current_user(self, token: str = Depends(oauth2_scheme)) -> UserInDB:
        payload = jwt_manager.verify_token(token)
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        return pwd_context.hash(password)
