from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    LargeBinary,
    JSON,
    Index,
    UniqueConstraint,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(150), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(LargeBinary, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)

    captcha_attempts = relationship('CaptchaAttempt', back_populates='user', cascade='all, delete-orphan')
    sessions = relationship('UserSession', back_populates='user', cascade='all, delete-orphan')

    __table_args__ = (
        Index('ix_users_username_email', 'username', 'email'),
        UniqueConstraint('username', name='uq_users_username'),
        UniqueConstraint('email', name='uq_users_email'),
    )

class CaptchaAttempt(Base):
    __tablename__ = 'captcha_attempts'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=True)
    captcha_type = Column(String(50), nullable=False)
    success = Column(Boolean, default=False, nullable=False)
    attempt_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    response_data = Column(JSON, nullable=True)
    error_message = Column(String(255), nullable=True)
    processing_time_ms = Column(Integer, nullable=True)

    user = relationship('User', back_populates='captcha_attempts')

    __table_args__ = (
        Index('ix_captcha_attempts_user_id', 'user_id'),
        Index('ix_captcha_attempts_captcha_type', 'captcha_type'),
        Index('ix_captcha_attempts_success', 'success'),
    )

class UserSession(Base):
    __tablename__ = 'user_sessions'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    session_token = Column(String(255), unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    metadata = Column(JSON, nullable=True)

    user = relationship('User', back_populates='sessions')

    __table_args__ = (
        Index('ix_user_sessions_user_id', 'user_id'),
        Index('ix_user_sessions_session_token', 'session_token'),
        Index('ix_user_sessions_expires_at', 'expires_at'),
    )
