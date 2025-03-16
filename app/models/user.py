# app/models/user.py
from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Integer, String
from pydantic import BaseModel, EmailStr, Field

from app.core.database import Base


class User(Base):
    """User database model."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


# Pydantic models for request/response validation
class UserCreate(BaseModel):
    """User creation schema."""
    username: str
    email: EmailStr
    password: str
    full_name: str


class UserResponse(BaseModel):
    """User response schema."""
    id: int
    username: str
    email: str
    full_name: str
    is_active: bool = True
    is_admin: bool = False
    created_at: datetime = None

    class Config:
        orm_mode = True


class Token(BaseModel):
    """Token response schema."""
    access_token: str
    token_type: str