from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from db import get_session
from models import User
from schemas import ChatCreate, ChatRead, MessageRead, LLMRequest, LLMResponse
from dependencies import get_current_user
from services.chat_service import ChatService

router = APIRouter(prefix="/chats", tags=["chats"])


@router.get("/", response_model=List[ChatRead])
async def list_chats(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_session)) -> List[ChatRead]:
    """Get all chats for current user"""
    chats = await ChatService.list_user_chats(user.id, db)
    return chats


@router.post("/", response_model=ChatRead)
async def create_chat(data: ChatCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_session)) -> ChatRead:
    """Create a new chat"""
    chat = await ChatService.create_chat(user.id, data.title, db)
    return chat


@router.get("/{chat_id}/messages", response_model=List[MessageRead])
async def get_messages(chat_id: int, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_session)) -> List[MessageRead]:
    """Get all messages from a chat"""
    try:
        messages = await ChatService.get_chat_messages(chat_id, user.id, db)
        return messages
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{chat_id}/messages", response_model=LLMResponse)
async def send_message(chat_id: int, request: LLMRequest, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_session)) -> LLMResponse:
    """Send a message and get LLM response"""
    try:
        question, answer = await ChatService.send_message(chat_id, user.id, request.question, db)
        return LLMResponse(answer=answer)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
