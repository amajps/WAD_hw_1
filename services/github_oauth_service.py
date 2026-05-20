"""Service layer for GitHub OAuth operations"""
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import User
from security import create_access_token, create_refresh_token
from config import settings
import redis_client


class GitHubOAuthService:
    """Handle GitHub OAuth 2.0 flow"""

    @staticmethod
    def get_github_auth_url() -> str:
        """
        Generate GitHub OAuth authorization URL.
        
        Returns:
            URL to redirect user to GitHub authorization
        """
        return (
            "https://github.com/login/oauth/authorize"
            f"?client_id={settings.GITHUB_CLIENT_ID}"
            f"&redirect_uri={settings.GITHUB_REDIRECT_URI}"
            "&scope=read:user user:email"
        )

    @staticmethod
    async def exchange_code_for_token(code: str) -> str:
        """
        Exchange GitHub authorization code for access token.
        
        Args:
            code: Authorization code from GitHub
            
        Returns:
            GitHub access token
            
        Raises:
            ValueError: If code exchange fails
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://github.com/login/oauth/access_token",
                headers={"Accept": "application/json"},
                data={
                    "client_id": settings.GITHUB_CLIENT_ID,
                    "client_secret": settings.GITHUB_CLIENT_SECRET,
                    "code": code,
                    "redirect_uri": settings.GITHUB_REDIRECT_URI,
                },
            )
            response.raise_for_status()
            token_data = response.json()

            github_token = token_data.get("access_token")
            if not github_token:
                error_msg = token_data.get("error_description", "Code exchange failed")
                raise ValueError(error_msg)

            return github_token

    @staticmethod
    async def fetch_github_user_profile(github_token: str) -> dict:
        """
        Fetch user profile from GitHub API.
        
        Args:
            github_token: GitHub access token
            
        Returns:
            Dictionary with user profile (id, login, email)
            
        Raises:
            ValueError: If API call fails
        """
        async with httpx.AsyncClient() as client:
            # Fetch user profile
            profile_response = await client.get(
                "https://api.github.com/user",
                headers={"Authorization": f"Bearer {github_token}", "Accept": "application/json"},
            )
            profile_response.raise_for_status()
            github_user = profile_response.json()

            # Fetch emails
            emails_response = await client.get(
                "https://api.github.com/user/emails",
                headers={"Authorization": f"Bearer {github_token}", "Accept": "application/json"},
            )
            emails_response.raise_for_status()
            emails_data = emails_response.json()

        # Extract primary verified email
        github_id = str(github_user.get("id"))
        username = github_user.get("login") or f"github_{github_id}"
        email = None

        for item in emails_data:
            if item.get("primary") and item.get("verified"):
                email = item.get("email")
                break

        if not email:
            email = github_user.get("email")

        return {
            "github_id": github_id,
            "username": username,
            "email": email
        }

    @staticmethod
    async def create_or_link_user(
        db: AsyncSession,
        github_id: str,
        username: str,
        email: str
    ) -> User:
        """
        Create new user or link existing user to GitHub account.
        
        Args:
            db: Database session
            github_id: GitHub user ID
            username: GitHub username
            email: GitHub email
            
        Returns:
            User object (created or updated)
        """
        # Try to find by github_id
        result = await db.execute(select(User).where(User.github_id == github_id))
        user = result.scalar_one_or_none()
        
        if user is None:
            # Try to find by email
            if email:
                result = await db.execute(select(User).where(User.email == email))
                user = result.scalar_one_or_none()
            
            if user is None:
                # Create new user
                user = User(username=username, email=email, github_id=github_id)
                db.add(user)
            else:
                # Link existing user to GitHub
                user.github_id = github_id
        else:
            # Update email if changed
            if email and user.email != email:
                user.email = email

        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def generate_oauth_tokens(user_id: int) -> tuple[str, str]:
        """
        Generate JWT and refresh tokens for OAuth login.
        
        Args:
            user_id: User ID
            
        Returns:
            Tuple of (access_token, refresh_token)
            
        Raises:
            ValueError: If Redis not initialized
        """
        if redis_client.redis_client is None:
            raise ValueError("Redis client not initialized")

        access_token = create_access_token(subject=str(user_id))
        refresh_token = create_refresh_token()
        
        # Store refresh token in Redis
        ttl_seconds = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600
        await redis_client.redis_client.set(
            refresh_token,
            str(user_id),
            ex=ttl_seconds
        )
        
        return access_token, refresh_token
