import httpx
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_session
from models import User
from schemas import TokenResponse
from security import create_access_token, create_refresh_token
from config import settings
import redis_client

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/github/login")
async def github_login():
    """Redirect user to GitHub OAuth authorization page."""
    if not settings.GITHUB_CLIENT_ID:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="GitHub client ID is not configured")

    url = (
        "https://github.com/login/oauth/authorize"
        f"?client_id={settings.GITHUB_CLIENT_ID}"
        f"&redirect_uri={settings.GITHUB_REDIRECT_URI}"
        "&scope=read:user user:email"
    )
    return RedirectResponse(url)


@router.get("/github/callback")
async def github_callback(code: str, state: str = Query(None), db: AsyncSession = Depends(get_session)):
    """
    GitHub OAuth callback handler.
    Exchanges OAuth code for GitHub access token, fetches user profile,
    creates or updates user in DB, and redirects to frontend with tokens.
    """
    if not settings.GITHUB_CLIENT_SECRET:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="GitHub client secret is not configured")

    async with httpx.AsyncClient() as client:
        # Exchange OAuth code for GitHub access token
        token_resp = await client.post(
            "https://github.com/login/oauth/access_token",
            headers={"Accept": "application/json"},
            data={
                "client_id": settings.GITHUB_CLIENT_ID,
                "client_secret": settings.GITHUB_CLIENT_SECRET,
                "code": code,
                "redirect_uri": settings.GITHUB_REDIRECT_URI,
            },
        )
        token_resp.raise_for_status()
        token_data = token_resp.json()

        github_access_token = token_data.get("access_token")
        if not github_access_token:
            error_msg = token_data.get("error_description", "GitHub token exchange failed")
            return RedirectResponse(url=f"{settings.FRONTEND_URL}/index.html?error={error_msg}", status_code=302)

        # Fetch GitHub user profile
        user_resp = await client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {github_access_token}", "Accept": "application/json"},
        )
        user_resp.raise_for_status()
        github_user = user_resp.json()

        # Fetch GitHub user emails
        email_resp = await client.get(
            "https://api.github.com/user/emails",
            headers={"Authorization": f"Bearer {github_access_token}", "Accept": "application/json"},
        )
        email_resp.raise_for_status()
        email_data = email_resp.json()

    # Extract primary verified email or fallback to profile email
    github_id = str(github_user.get("id"))
    username = github_user.get("login") or f"github_{github_id}"
    email = None
    for item in email_data:
        if item.get("primary") and item.get("verified"):
            email = item.get("email")
            break
    if not email:
        email = github_user.get("email")

    # Find or create user in database
    result = await db.execute(select(User).where(User.github_id == github_id))
    user = result.scalar_one_or_none()
    
    if user is None:
        # Try to find by email if not by github_id
        if email is not None:
            result = await db.execute(select(User).where(User.email == email))
            user = result.scalar_one_or_none()
        
        if user is None:
            # Create new user
            user = User(username=username, email=email, github_id=github_id)
            db.add(user)
            await db.commit()
            await db.refresh(user)
    else:
        # Update existing user with any new email if changed
        if email and user.email != email:
            user.email = email
            await db.commit()

    # Create JWT and refresh token
    access_token = create_access_token(subject=str(user.id))
    refresh_token = create_refresh_token()
    
    if redis_client.redis_client is None:
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/index.html?error=Redis+not+initialized", status_code=302)

    # Store refresh token in Redis with 30-day TTL
    await redis_client.redis_client.set(refresh_token, str(user.id), ex=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600)
    
    # Redirect back to frontend with tokens in URL
    redirect_url = f"{settings.FRONTEND_URL}/index.html?access_token={access_token}&refresh_token={refresh_token}"
    return RedirectResponse(url=redirect_url, status_code=302)
