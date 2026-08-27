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
