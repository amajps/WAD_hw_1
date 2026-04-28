from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from anyio import to_thread

from db import get_session
from models import Chat, Message, User
from schemas import ChatCreate, ChatRead, MessageRead, LLMRequest, LLMResponse
from routers.auth import get_current_user
from llm import generate_answer

router = APIRouter(prefix="/chats", tags=["chats"])


@router.get("/", response_model=List[ChatRead])
async def list_chats(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_session)) -> List[ChatRead]:
    result = await db.execute(select(Chat).where(Chat.user_id == user.id).order_by(Chat.created_at))
    chats = result.scalars().all()
    return chats


@router.post("/", response_model=ChatRead)
async def create_chat(data: ChatCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_session)) -> ChatRead:
    chat = Chat(title=data.title, user_id=user.id)
    db.add(chat)
    await db.commit()
    await db.refresh(chat)
    return chat


@router.get("/{chat_id}/messages", response_model=List[MessageRead])
async def get_messages(chat_id: int, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_session)) -> List[MessageRead]:
    result = await db.execute(
        select(Message)
        .join(Chat, Message.chat_id == Chat.id)
        .where(Chat.id == chat_id)
        .where(Chat.user_id == user.id)
        .order_by(Message.created_at)
    )
    messages = result.scalars().all()
    return messages


@router.post("/{chat_id}/messages", response_model=LLMResponse)
async def send_message(chat_id: int, request: LLMRequest, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_session)) -> LLMResponse:
    result = await db.execute(select(Chat).where(Chat.id == chat_id, Chat.user_id == user.id))
    chat = result.scalar_one_or_none()
    if chat is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")

    user_message = Message(chat_id=chat.id, user_id=user.id, role="user", text=request.question)
    db.add(user_message)
    await db.commit()
    await db.refresh(user_message)

    answer = await to_thread.run_sync(generate_answer, f"User: {request.question}\nAssistant:")

    assistant_message = Message(chat_id=chat.id, user_id=user.id, role="assistant", text=answer)
    db.add(assistant_message)
    await db.commit()
    await db.refresh(assistant_message)

    return LLMResponse(answer=answer)
