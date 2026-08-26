from typing import List, Optional
import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field

from database.database import get_db
from database.models import (
    User, HealthProfile, HealthCondition, Allergy, Medication,
    Lifestyle, HealthGoal, Measurement
)
from auth.security import get_current_user

router = APIRouter(prefix="/health", tags=["health"])

# --- Pydantic Schemas ---

class HealthProfileBase(BaseModel):
    date_of_birth: Optional[datetime.date] = None
    sex: Optional[str] = None
    height: Optional[float] = None
    height_unit: Optional[str] = None
    weight: Optional[float] = None
    weight_unit: Optional[str] = None
    blood_type: Optional[str] = None
    timezone: Optional[str] = None

class HealthProfileResponse(HealthProfileBase):
    id: str
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True


class HealthConditionBase(BaseModel):
    name: str
    status: str = "unknown"
    notes: Optional[str] = None
    source: str = "user"
    source_reference: Optional[str] = None

class HealthConditionResponse(HealthConditionBase):
    id: str
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True


class AllergyBase(BaseModel):
    substance: str
    reaction: Optional[str] = None
    severity: Optional[str] = None
    status: str = "active"
    source: str = "user"
    source_reference: Optional[str] = None

class AllergyResponse(AllergyBase):
    id: str
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True


class MedicationBase(BaseModel):
    name: str
    dose: Optional[str] = None
    dose_unit: Optional[str] = None
    frequency: Optional[str] = None
    route: Optional[str] = None
    status: str = "active"
    start_date: Optional[datetime.date] = None
    end_date: Optional[datetime.date] = None
    notes: Optional[str] = None
    source: str = "user"
    source_reference: Optional[str] = None

class MedicationResponse(MedicationBase):
    id: str
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True


class LifestyleBase(BaseModel):
    category: str
    summary: Optional[str] = None
    details: Optional[str] = None
    source: str = "user"

class LifestyleResponse(LifestyleBase):
    id: str
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True


class HealthGoalBase(BaseModel):
    category: Optional[str] = None
    title: str
    description: Optional[str] = None
    status: str = "active"
    target_value: Optional[float] = None
    target_unit: Optional[str] = None
    target_date: Optional[datetime.date] = None

class HealthGoalResponse(HealthGoalBase):
    id: str
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True


class MeasurementBase(BaseModel):
    type: str
    value: float
    secondary_value: Optional[float] = None
    unit: str
    source: str = "user"
    notes: Optional[str] = None

class MeasurementResponse(MeasurementBase):
    id: str
    measured_at: datetime.datetime
    created_at: datetime.datetime

    class Config:
        from_attributes = True

class HealthSummaryResponse(BaseModel):
    profile: Optional[HealthProfileResponse] = None
    active_conditions_count: int = 0
    active_medications_count: int = 0
    allergies_count: int = 0
    active_goals_count: int = 0


# --- Endpoints ---

# Health Profile
@router.get("/profile", response_model=Optional[HealthProfileResponse])
async def get_health_profile(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    stmt = select(HealthProfile).where(HealthProfile.user_id == user.id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

@router.put("/profile", response_model=HealthProfileResponse)
async def update_health_profile(profile_data: HealthProfileBase, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    stmt = select(HealthProfile).where(HealthProfile.user_id == user.id)
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()
    
    if profile:
        for key, value in profile_data.model_dump().items():
            setattr(profile, key, value)
    else:
        profile = HealthProfile(user_id=user.id, **profile_data.model_dump())
        db.add(profile)
    
    await db.commit()
    await db.refresh(profile)
    return profile

# Generic CRUD Helper
async def create_item(db: AsyncSession, user_id: str, model_cls, data: BaseModel):
    item = model_cls(user_id=user_id, **data.model_dump())
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item

async def list_items(db: AsyncSession, user_id: str, model_cls):
    stmt = select(model_cls).where(model_cls.user_id == user_id)
    result = await db.execute(stmt)
    return result.scalars().all()

async def update_item(db: AsyncSession, user_id: str, item_id: str, model_cls, data: BaseModel):
    stmt = select(model_cls).where(model_cls.id == item_id, model_cls.user_id == user_id)
    result = await db.execute(stmt)
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    for key, value in data.model_dump().items():
        setattr(item, key, value)
    await db.commit()
    await db.refresh(item)
    return item

async def delete_item(db: AsyncSession, user_id: str, item_id: str, model_cls):
    stmt = select(model_cls).where(model_cls.id == item_id, model_cls.user_id == user_id)
    result = await db.execute(stmt)
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    await db.delete(item)
    await db.commit()
    return {"status": "deleted"}

# Conditions
@router.get("/conditions", response_model=List[HealthConditionResponse])
async def get_conditions(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    return await list_items(db, user.id, HealthCondition)

@router.post("/conditions", response_model=HealthConditionResponse)
async def create_condition(data: HealthConditionBase, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    return await create_item(db, user.id, HealthCondition, data)

@router.put("/conditions/{item_id}", response_model=HealthConditionResponse)
async def update_condition(item_id: str, data: HealthConditionBase, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    return await update_item(db, user.id, item_id, HealthCondition, data)

@router.delete("/conditions/{item_id}")
async def delete_condition(item_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    return await delete_item(db, user.id, item_id, HealthCondition)

# Allergies
@router.get("/allergies", response_model=List[AllergyResponse])
async def get_allergies(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    return await list_items(db, user.id, Allergy)

@router.post("/allergies", response_model=AllergyResponse)
async def create_allergy(data: AllergyBase, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    return await create_item(db, user.id, Allergy, data)

@router.put("/allergies/{item_id}", response_model=AllergyResponse)
async def update_allergy(item_id: str, data: AllergyBase, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    return await update_item(db, user.id, item_id, Allergy, data)

@router.delete("/allergies/{item_id}")
async def delete_allergy(item_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    return await delete_item(db, user.id, item_id, Allergy)

# Medications
@router.get("/medications", response_model=List[MedicationResponse])
async def get_medications(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    return await list_items(db, user.id, Medication)

@router.post("/medications", response_model=MedicationResponse)
async def create_medication(data: MedicationBase, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    return await create_item(db, user.id, Medication, data)

@router.put("/medications/{item_id}", response_model=MedicationResponse)
async def update_medication(item_id: str, data: MedicationBase, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    return await update_item(db, user.id, item_id, Medication, data)

@router.delete("/medications/{item_id}")
async def delete_medication(item_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    return await delete_item(db, user.id, item_id, Medication)

# Lifestyle
@router.get("/lifestyle", response_model=List[LifestyleResponse])
async def get_lifestyle(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    return await list_items(db, user.id, Lifestyle)

@router.post("/lifestyle", response_model=LifestyleResponse)
async def create_lifestyle(data: LifestyleBase, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    return await create_item(db, user.id, Lifestyle, data)

@router.put("/lifestyle/{item_id}", response_model=LifestyleResponse)
async def update_lifestyle(item_id: str, data: LifestyleBase, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    return await update_item(db, user.id, item_id, Lifestyle, data)

@router.delete("/lifestyle/{item_id}")
async def delete_lifestyle(item_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    return await delete_item(db, user.id, item_id, Lifestyle)

# Goals
@router.get("/goals", response_model=List[HealthGoalResponse])
async def get_goals(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    return await list_items(db, user.id, HealthGoal)

@router.post("/goals", response_model=HealthGoalResponse)
async def create_goal(data: HealthGoalBase, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    return await create_item(db, user.id, HealthGoal, data)

@router.put("/goals/{item_id}", response_model=HealthGoalResponse)
async def update_goal(item_id: str, data: HealthGoalBase, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    return await update_item(db, user.id, item_id, HealthGoal, data)

@router.delete("/goals/{item_id}")
async def delete_goal(item_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    return await delete_item(db, user.id, item_id, HealthGoal)

# Measurements (No PUT since measurements are usually immutable point-in-time data)
@router.get("/measurements", response_model=List[MeasurementResponse])
async def get_measurements(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    stmt = select(Measurement).where(Measurement.user_id == user.id).order_by(Measurement.measured_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/measurements", response_model=MeasurementResponse)
async def create_measurement(data: MeasurementBase, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    return await create_item(db, user.id, Measurement, data)

@router.delete("/measurements/{item_id}")
async def delete_measurement(item_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    return await delete_item(db, user.id, item_id, Measurement)

# Summary
@router.get("/summary", response_model=HealthSummaryResponse)
async def get_summary(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    profile = await get_health_profile(db, user)
    
    # Simple count queries
    # Note: In a real large app we'd use select(func.count()). For now, fetching list size is fine.
    conditions = await list_items(db, user.id, HealthCondition)
    medications = await list_items(db, user.id, Medication)
    allergies = await list_items(db, user.id, Allergy)
    goals = await list_items(db, user.id, HealthGoal)
    
    return HealthSummaryResponse(
        profile=profile,
        active_conditions_count=len([c for c in conditions if c.status == 'active']),
        active_medications_count=len([m for m in medications if m.status == 'active']),
        allergies_count=len(allergies),
        active_goals_count=len([g for g in goals if g.status == 'active'])
    )
