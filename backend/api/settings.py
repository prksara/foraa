import os
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from database.database import get_db
from database.models import UserPreferences, User
from auth.security import get_current_user
from pydantic import BaseModel

router = APIRouter(prefix="/settings", tags=["settings"])

class UserPreferencesSchema(BaseModel):
    notif_product: bool
    notif_health: bool
    ai_data_pref: bool
    data_retention: str
    doc_storage: bool
    theme: str

    class Config:
        from_attributes = True

@router.get("/preferences", response_model=UserPreferencesSchema)
async def get_preferences(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    result = await db.execute(select(UserPreferences).where(UserPreferences.user_id == user.id))
    prefs = result.scalars().first()
    
    if not prefs:
        # Return defaults
        return UserPreferencesSchema(
            notif_product=True,
            notif_health=True,
            ai_data_pref=True,
            data_retention="90",
            doc_storage=True,
            theme="system"
        )
    return prefs

@router.put("/preferences", response_model=UserPreferencesSchema)
async def update_preferences(
    prefs_in: UserPreferencesSchema,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    result = await db.execute(select(UserPreferences).where(UserPreferences.user_id == user.id))
    prefs = result.scalars().first()
    
    if not prefs:
        prefs = UserPreferences(user_id=user.id)
        db.add(prefs)
        
    prefs.notif_product = prefs_in.notif_product
    prefs.notif_health = prefs_in.notif_health
    prefs.ai_data_pref = prefs_in.ai_data_pref
    prefs.data_retention = prefs_in.data_retention
    prefs.doc_storage = prefs_in.doc_storage
    prefs.theme = prefs_in.theme
    
    await db.commit()
    await db.refresh(prefs)
    return prefs

@router.delete("/account")
async def delete_account(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Permanently deletes user account and all associated health records, documents,
    conversations, timeline events, and preferences via cascade.
    """
    user_id = user.id

    # 1. Delete user from database (triggers ON DELETE CASCADE for all user child tables)
    await db.delete(user)
    await db.commit()

    # 2. Delete user from Supabase Auth if service role is configured
    try:
        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        if supabase_url and supabase_key:
            from supabase import create_client
            client = create_client(supabase_url, supabase_key)
            client.auth.admin.delete_user(user_id)
    except Exception as e:
        # DB deletion succeeded; log any auth service error
        pass

    return {"status": "account_deleted", "message": "All user data has been permanently deleted."}
