from datetime import datetime
from pydantic import BaseModel, EmailStr
from typing import List, Optional


class UserCreate(BaseModel):
    username: str
    password: str
    email: Optional[EmailStr] = None


class UserRead(BaseModel):
    id: int
    username: str
    email: Optional[EmailStr] = None
    is_active: bool

    class Config:
        orm_mode = True


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class ChatCreate(BaseModel):
    title: str


class ChatRead(BaseModel):
    id: int
    title: str
    created_at: datetime

    class Config:
        orm_mode = True


class MessageCreate(BaseModel):
    text: str


class MessageRead(BaseModel):
    id: int
    role: str
    text: str
    created_at: datetime

    class Config:
        orm_mode = True


class LLMRequest(BaseModel):
    question: str


class LLMResponse(BaseModel):
    answer: str
