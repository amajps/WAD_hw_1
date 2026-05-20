from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_session
from models import User
from schemas import UserCreate, UserRead, TokenResponse, RefreshRequest
from dependencies import get_current_user
from services import AuthService
from config import settings

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead)
async def register_user(data: UserCreate, db: AsyncSession = Depends(get_session)) -> UserRead:
    """Register a new user"""
    try:
        user = await AuthService.register_user(db, data.username, data.password, data.email)
        return user
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/token", response_model=TokenResponse)
async def token(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_session)) -> TokenResponse:
    """Login with username and password"""
    try:
        user = await AuthService.authenticate_user(db, form_data.username, form_data.password)
        access_token, refresh_token = await AuthService.create_tokens(user.id)
        return TokenResponse(access_token=access_token, refresh_token=refresh_token)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshRequest):
    """Refresh access token using refresh token"""
    try:
        access_token, new_refresh_token = await AuthService.refresh_access_token(request.refresh_token)
        return TokenResponse(access_token=access_token, refresh_token=new_refresh_token)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/logout")
async def logout(request: RefreshRequest):
    """Logout and delete refresh token"""
    try:
        await AuthService.logout(request.refresh_token)
        return {"detail": "Logged out"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/me", response_model=UserRead)
async def me(user: User = Depends(get_current_user)) -> UserRead:
    return user
