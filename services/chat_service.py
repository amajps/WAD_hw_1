"""Service layer for chat operations"""
from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from anyio import to_thread

from models import Chat, Message, User
from llm import generate_answer


class ChatService:
    """Handle chat and messaging business logic"""

    @staticmethod
    async def list_user_chats(user_id: int, db: AsyncSession) -> List[Chat]:
        """
        Get all chats for a user.
        
        Args:
            user_id: User ID
            db: Database session
            
        Returns:
            List of Chat objects
        """
        result = await db.execute(
            select(Chat)
            .where(Chat.user_id == user_id)
            .order_by(Chat.created_at)
        )
        return result.scalars().all()

    @staticmethod
    async def create_chat(user_id: int, title: str, db: AsyncSession) -> Chat:
        """
        Create a new chat for a user.
        
        Args:
            user_id: User ID
            title: Chat title
            db: Database session
            
        Returns:
            Created Chat object
        """
        chat = Chat(title=title, user_id=user_id)
        db.add(chat)
        await db.commit()
        await db.refresh(chat)
        return chat

    @staticmethod
    async def get_chat_messages(chat_id: int, user_id: int, db: AsyncSession) -> List[Message]:
        """
        Get all messages from a specific chat (with user verification).
        
        Args:
            chat_id: Chat ID
            user_id: User ID (for verification)
            db: Database session
            
        Returns:
            List of Message objects
            
        Raises:
            ValueError: If chat not found or user doesn't have access
        """
        result = await db.execute(
            select(Message)
            .join(Chat, Message.chat_id == Chat.id)
            .where(Chat.id == chat_id)
            .where(Chat.user_id == user_id)
            .order_by(Message.created_at)
        )
        messages = result.scalars().all()
        
        # Verify chat exists and user has access
        if not messages:
            chat_result = await db.execute(
                select(Chat).where(Chat.id == chat_id, Chat.user_id == user_id)
            )
            if not chat_result.scalar_one_or_none():
                raise ValueError(f"Chat {chat_id} not found or access denied")
        
        return messages

    @staticmethod
    async def send_message(
        chat_id: int,
        user_id: int,
        question: str,
        db: AsyncSession
    ) -> tuple[str, str]:
        """
        Send a message to the LLM and get a response.
        
        This method:
        1. Verifies chat exists and user has access
        2. Saves user message to database
        3. Calls LLM to generate response
        4. Saves assistant response to database
        5. Returns both messages
        
        Args:
            chat_id: Chat ID
            user_id: User ID
            question: User's question
            db: Database session
            
        Returns:
            Tuple of (user_message_text, assistant_response_text)
            
        Raises:
            ValueError: If chat not found or access denied
        """
        # Verify chat exists and user has access
        chat_result = await db.execute(
            select(Chat).where(Chat.id == chat_id, Chat.user_id == user_id)
        )
        chat = chat_result.scalar_one_or_none()
        if chat is None:
            raise ValueError(f"Chat {chat_id} not found or access denied")

        # Save user message
        user_message = Message(
            chat_id=chat.id,
            user_id=user_id,
            role="user",
            text=question
        )
        db.add(user_message)
        await db.commit()
        await db.refresh(user_message)

        # Generate LLM response
        prompt = f"User: {question}\nAssistant:"
        answer = await to_thread.run_sync(generate_answer, prompt)

        # Save assistant message
        assistant_message = Message(
            chat_id=chat.id,
            user_id=user_id,
            role="assistant",
            text=answer
        )
        db.add(assistant_message)
        await db.commit()
        await db.refresh(assistant_message)

        return question, answer
