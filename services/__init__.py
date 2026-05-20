"""Service layer for authentication operations"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta
import secrets

from models import User
from security import hash_password, verify_password, create_access_token, create_refresh_token
import redis_client
from config import settings


class AuthService:
    """Handle authentication business logic"""

    @staticmethod
    async def register_user(
        db: AsyncSession,
        username: str,
        password: str,
        email: str
    ) -> User:
        """
        Register a new user with username, password, and email.
        
        Args:
            db: Database session
            username: Unique username
            password: Plain text password (will be hashed)
            email: User email
            
        Returns:
            Created User object
            
        Raises:
            ValueError: If username already exists
        """
        # Check if user exists
        result = await db.execute(select(User).where(User.username == username))
        if result.scalar_one_or_none():
            raise ValueError(f"Username '{username}' already exists")

        # Create new user
        user = User(
            username=username,
            email=email,
            hashed_password=hash_password(password)
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def authenticate_user(
        db: AsyncSession,
        username: str,
        password: str
    ) -> User:
        """
        Authenticate user with username and password.
        
        Args:
            db: Database session
            username: User's username
            password: Plain text password
            
        Returns:
            Authenticated User object
            
        Raises:
            ValueError: If credentials are invalid
        """
        # Find user by username
        result = await db.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()
        
        if user is None or user.hashed_password is None:
            raise ValueError("Invalid credentials")

        # Verify password
        if not verify_password(password, user.hashed_password):
            raise ValueError("Invalid credentials")

        return user

    @staticmethod
    async def create_tokens(user_id: int) -> tuple[str, str]:
        """
        Create access and refresh tokens for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Tuple of (access_token, refresh_token)
            
        Raises:
            ValueError: If Redis is not initialized
        """
        if redis_client.redis_client is None:
            raise ValueError("Redis client not initialized")

        access_token = create_access_token(subject=str(user_id))
        refresh_token = create_refresh_token()
        
        # Store refresh token in Redis with TTL
        ttl_seconds = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600
        await redis_client.redis_client.set(
            refresh_token,
            str(user_id),
            ex=ttl_seconds
        )
        
        return access_token, refresh_token

    @staticmethod
    async def refresh_access_token(refresh_token: str) -> tuple[str, str]:
        """
        Refresh access token using a refresh token.
        
        Args:
            refresh_token: Refresh token from Redis
            
        Returns:
            Tuple of (new_access_token, new_refresh_token)
            
        Raises:
            ValueError: If token is invalid or Redis error
        """
        if redis_client.redis_client is None:
            raise ValueError("Redis client not initialized")

        user_id = await redis_client.redis_client.get(refresh_token)
        if user_id is None:
            raise ValueError("Invalid refresh token")

        # Delete old refresh token
        await redis_client.redis_client.delete(refresh_token)
        
        # Create new tokens
        access_token = create_access_token(subject=user_id)
        new_refresh_token = create_refresh_token()
        
        # Store new refresh token in Redis
        ttl_seconds = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600
        await redis_client.redis_client.set(
            new_refresh_token,
            user_id,
            ex=ttl_seconds
        )
        
        return access_token, new_refresh_token

    @staticmethod
    async def logout(refresh_token: str) -> None:
        """
        Logout user by deleting refresh token from Redis.
        
        Args:
            refresh_token: Refresh token to delete
            
        Raises:
            ValueError: If Redis is not initialized
        """
        if redis_client.redis_client is None:
            raise ValueError("Redis client not initialized")

        await redis_client.redis_client.delete(refresh_token)
