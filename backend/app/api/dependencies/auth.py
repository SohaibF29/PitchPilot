"""
Authentication dependency to validate Supabase JWT tokens.
"""

from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.config import get_settings
from app.domain.entities.user import User
from app.infrastructure.database.connection import get_db_session
from app.infrastructure.repositories.user_repository import UserRepository

settings = get_settings()
security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db_session)
) -> User:
    """
    Validate Supabase JWT from Authorization header and return the authenticated User.
    Creates a user profile on the fly if one doesn't exist yet.
    """
    token = credentials.credentials
    secret = settings.supabase_jwt_secret.get_secret_value()
    print(f"DEBUG: get_current_user invoked. secret='{secret}' (len={len(secret)})")
    
    if not secret:
        print("DEBUG: entering 'if not secret' block")
        # Fallback for development if secret not provided: allow anonymous logic
        # WARNING: This should be strict in production
        if settings.is_development:
            from app.api.routes.meetings import ANONYMOUS_USER_ID
            user_repo = UserRepository(db)
            user = await user_repo.get_by_id(ANONYMOUS_USER_ID)
            print(f"DEBUG: user from repo for anonymous: {user}")
            if not user:
                print("DEBUG: creating anonymous user in DB")
                user = User(
                    id=ANONYMOUS_USER_ID,
                    email="anonymous@pitchpilot.local",
                    full_name="Local Dev User",
                )
                user = await user_repo.save(user)
                print("DEBUG: anonymous user created successfully")
            return user
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="JWT secret not configured on server.",
        )

    try:
        # Supabase JWTs are signed with HS256 using the project JWT secret
        payload = jwt.decode(
            token,
            secret,
            algorithms=["HS256"],
            options={"verify_aud": False} # Supabase aud is typically "authenticated"
        )
        
        user_id_str = payload.get("sub")
        if not user_id_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload.",
            )
            
        user_id = UUID(user_id_str)
        email = payload.get("email", "")
        
    except JWTError as e:
        print(f"DEBUG: JWTError occurred: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)
    
    if not user:
        # Create user profile on the fly
        user = User(
            id=user_id,
            email=email,
            full_name=email.split("@")[0] if email else "New User",
        )
        user = await user_repo.save(user)
        
    return user
