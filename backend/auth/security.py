import os
import logging
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from database.database import get_db
from database.models import User

logger = logging.getLogger("foraa.auth")

security = HTTPBearer()

def get_supabase_jwt_secret() -> str:
    secret = os.getenv("SUPABASE_JWT_SECRET")
    if not secret:
        # In a real app, you MUST set this. For development without the .env, this will fail.
        raise ValueError("SUPABASE_JWT_SECRET environment variable is not set")
    return secret

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Validates the Supabase JWT and returns the corresponding User from the database.
    If the user doesn't exist in our DB yet but has a valid token, we create them.
    """
    token = credentials.credentials
    try:
        secret = get_supabase_jwt_secret()
        # Supabase uses HS256 by default for their JWTs
        payload = jwt.decode(
            token, 
            secret, 
            algorithms=["HS256"],
            options={"verify_aud": False} # Supabase aud is usually 'authenticated'
        )
        
        # 'sub' is the user's UUID in Supabase Auth
        auth_provider_id = payload.get("sub")
        email = payload.get("email")
        
        if not auth_provider_id or not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token payload",
            )
            
    except JWTError as e:
        logger.warning(f"JWT decode error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Auth error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
        )

    # Find the user in our database
    result = await db.execute(select(User).where(User.auth_provider_id == auth_provider_id))
    user = result.scalars().first()
    
    if not user:
        # Sync: Create the user in our DB if they don't exist yet but logged in via Supabase
        user_metadata = payload.get("user_metadata", {})
        name = user_metadata.get("full_name") or user_metadata.get("name")
        avatar_url = user_metadata.get("avatar_url")
        
        user = User(
            auth_provider_id=auth_provider_id,
            email=email,
            name=name,
            avatar_url=avatar_url
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        logger.info(f"Created new synced user: {user.id}")

    return user
