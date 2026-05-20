import httpx
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_session
from schemas import TokenResponse
from config import settings
from services.github_oauth_service import GitHubOAuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/github/login")
async def github_login():
    """Redirect user to GitHub OAuth authorization page"""
    if not settings.GITHUB_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="GitHub client ID is not configured"
        )
    
    url = GitHubOAuthService.get_github_auth_url()
    return RedirectResponse(url)


@router.get("/github/callback")
async def github_callback(code: str, state: str = Query(None), db: AsyncSession = Depends(get_session)):
    """GitHub OAuth callback handler"""
    if not settings.GITHUB_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="GitHub client secret is not configured"
        )

    try:
        # Exchange code for token
        github_token = await GitHubOAuthService.exchange_code_for_token(code)
        
        # Fetch user profile
        user_data = await GitHubOAuthService.fetch_github_user_profile(github_token)
        
        # Create or link user
        user = await GitHubOAuthService.create_or_link_user(
            db,
            user_data["github_id"],
            user_data["username"],
            user_data["email"]
        )
        
        # Generate tokens
        access_token, refresh_token = await GitHubOAuthService.generate_oauth_tokens(user.id)
        
        # Redirect back to frontend with tokens
        redirect_url = f"{settings.FRONTEND_URL}/index.html?access_token={access_token}&refresh_token={refresh_token}"
        return RedirectResponse(url=redirect_url, status_code=302)
        
    except ValueError as e:
        error_msg = str(e)
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/index.html?error={error_msg}",
            status_code=302
        )
