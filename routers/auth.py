from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_session
from models import User
from schemas import UserCreate, UserRead, TokenResponse, RefreshRequest
from security import hash_password, verify_password, create_access_token, create_refresh_token, decode_access_token
import redis_client
from config import settings

router = APIRouter(prefix="/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_session)) -> User:
    try:
        payload = decode_access_token(token)
        user_id = int(payload.get("sub"))
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired access token")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
    return user


@router.post("/register", response_model=UserRead)
async def register_user(data: UserCreate, db: AsyncSession = Depends(get_session)) -> UserRead:
    existing = await db.execute(select(User).where(User.username == data.username))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")

    user = User(
        username=data.username,
        email=data.email,
        hashed_password=hash_password(data.password)
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/token", response_model=TokenResponse)
async def token(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_session)) -> TokenResponse:
    result = await db.execute(select(User).where(User.username == form_data.username))
    user = result.scalar_one_or_none()
    if user is None or user.hashed_password is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    access_token = create_access_token(subject=str(user.id))
    refresh_token = create_refresh_token()
    if redis_client.redis_client is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Redis client not initialized")

    await redis_client.redis_client.set(refresh_token, str(user.id), ex=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshRequest):
    if redis_client.redis_client is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Redis client not initialized")

    user_id = await redis_client.redis_client.get(request.refresh_token)
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    await redis_client.redis_client.delete(request.refresh_token)
    access_token = create_access_token(subject=user_id)
    new_refresh_token = create_refresh_token()
    await redis_client.redis_client.set(new_refresh_token, str(user_id), ex=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600)
    return TokenResponse(access_token=access_token, refresh_token=new_refresh_token)


@router.post("/logout")
async def logout(request: RefreshRequest):
    if redis_client.redis_client is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Redis client not initialized")

    await redis_client.redis_client.delete(request.refresh_token)
    return {"detail": "Logged out"}


@router.get("/me", response_model=UserRead)
async def me(user: User = Depends(get_current_user)) -> UserRead:
    return user
