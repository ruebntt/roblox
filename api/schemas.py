from pydantic import BaseModel, Field, validator, root_validator
from typing import Optional, Literal, Dict, Any
from datetime import datetime

class AuthRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Логин пользователя")
    password: str = Field(..., min_length=8, max_length=128, description="Пароль пользователя")
    captcha_token: str = Field(..., description="Токен CAPTCHA для подтверждения")
    captcha_solution: str = Field(..., description="Решение CAPTCHA")
    additional_data: Optional[Dict[str, Any]] = Field(None, description="Дополнительные данные для расширения")

    @validator('captcha_token', 'captcha_solution')
    def check_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Поле не может быть пустым')
        return v

class AuthResponse(BaseModel):
    user_id: int
    username: str
    email: Optional[str] = None
    token: str = Field(..., description="JWT токен для дальнейших запросов")
    roles: Optional[list[str]] = None
    issued_at: datetime = Field(default_factory=datetime.utcnow)
    expires_in: int = Field(..., description="Время жизни токена в секундах")

class UserProfile(BaseModel):
    user_id: int
    username: str
    email: Optional[str]
    registration_date: datetime
    last_login: Optional[datetime]
    account_status: Literal['active', 'suspended', 'deleted']
    preferences: Optional[Dict[str, Any]]

class ErrorResponse(BaseModel):
    detail: str
    code: Optional[int] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class CAPTCHAResponse(BaseModel):
    captcha_id: str
    status: Literal['pending', 'solved', 'failed']
    solution: Optional[str] = None
    solved_at: Optional[datetime] = None
    error_message: Optional[str] = None
