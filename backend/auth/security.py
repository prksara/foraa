import os
import logging
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from supabase import create_client, Client

from database.database import get_db
from database.models import User

logger = logging.getLogger("foraa.auth")

security = HTTPBearer()

_supabase_client: Optional[Client] = None

def get_supabase_client() -> Client:
    global _supabase_client
    if _supabase_client is None:
        url = os.getenv("SUPABASE_URL")
        # We can use the anon key or service role key to initialize the client
        # to verify a user's token via the Supabase Auth server.
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
        if not url or not key:
            raise ValueError("SUPABASE_URL and a Supabase key must be set")
        _supabase_client = create_client(url, key)
    return _supabase_client

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Validates the Supabase JWT using the Supabase Auth API and returns the User.
    If the user doesn't exist in our DB yet but has a valid token, we create them.
    """
    token = credentials.credentials
    jwt_secret = os.getenv("SUPABASE_JWT_SECRET")

    auth_provider_id = None
    email = None
    name = None
    avatar_url = None

    if jwt_secret:
        try:
            # Check the unverified header to see the algorithm used
            unverified_header = jwt.get_unverified_header(token)
            alg = unverified_header.get("alg", "HS256")
            
            # Supabase tokens typically use HS256, but let's be flexible to the header if it's symmetric
            # Note: PyJWT will reject RS256 if jwt_secret is just a string secret. 
            allowed_algs = ["HS256"] if alg == "HS256" else ["HS256", "RS256"]
            
            payload = jwt.decode(
                token, 
                jwt_secret,
                algorithms=allowed_algs,
                options={"verify_aud": False}
            )
            auth_provider_id = payload.get("sub")
            email = payload.get("email")
            user_metadata = payload.get("user_metadata", {})
            name = user_metadata.get("full_name") or user_metadata.get("name")
            avatar_url = user_metadata.get("avatar_url")
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
        except jwt.InvalidTokenError as e:
            logger.warning(f"JWT decode failed: {e}. Falling back to network validation.")
        except Exception as e:
            logger.warning(f"Unexpected error during JWT decode: {e}. Falling back to network validation.")

    # Fallback to Supabase network call if local decode didn't set auth_provider_id
    if not auth_provider_id:
        try:
            supabase_client = get_supabase_client()
            # Securely verify the JWT by delegating to Supabase Auth.
            auth_response = supabase_client.auth.get_user(token)
            
            if not auth_response or not auth_response.user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication token",
                )
                
            user_obj = auth_response.user
            auth_provider_id = user_obj.id
            email = user_obj.email
            user_metadata = user_obj.user_metadata or {}
            name = user_metadata.get("full_name") or user_metadata.get("name")
            avatar_url = user_metadata.get("avatar_url")
                
        except Exception as e:
            logger.warning(f"Auth error (get_user): {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed",
                headers={"WWW-Authenticate": "Bearer"},
            )

    if not auth_provider_id or not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token payload",
        )

    # Find the user in our database
    result = await db.execute(select(User).where(User.auth_provider_id == auth_provider_id))
    user = result.scalars().first()
    
    if not user:
        # Sync: Create the user in our DB if they don't exist yet
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
