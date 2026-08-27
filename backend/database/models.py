import datetime
import uuid
from typing import Optional

from sqlalchemy import String, Text, ForeignKey, DateTime, Float, Date, Boolean, JSON, Integer, Column
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects.postgresql import TSVECTOR

class Base(DeclarativeBase):
    pass

def generate_uuid() -> str:
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    auth_provider_id: Mapped[Optional[str]] = mapped_column(String, unique=True, index=True, nullable=True) # E.g., Supabase user.id
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    conversations: Mapped[list["Conversation"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    health_profile: Mapped[Optional["HealthProfile"]] = relationship(back_populates="user", cascade="all, delete-orphan", uselist=False)
    conditions: Mapped[list["HealthCondition"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    allergies: Mapped[list["Allergy"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    medications: Mapped[list["Medication"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    lifestyle_entries: Mapped[list["Lifestyle"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    goals: Mapped[list["HealthGoal"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    measurements: Mapped[list["Measurement"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    documents: Mapped[list["HealthDocument"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    document_extractions: Mapped[list["DocumentExtraction"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    health_events: Mapped[list["HealthEvent"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    preferences: Mapped[Optional["UserPreferences"]] = relationship(back_populates="user", cascade="all, delete-orphan", uselist=False)


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True) # Strictly required
    title: Mapped[str] = mapped_column(String, default="New Chat")
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    user: Mapped[Optional["User"]] = relationship(back_populates="conversations")
    messages: Mapped[list["Message"]] = relationship(back_populates="conversation", cascade="all, delete-orphan", order_by="Message.timestamp")


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    conversation_id: Mapped[str] = mapped_column(ForeignKey("conversations.id", ondelete="CASCADE"))
    role: Mapped[str] = mapped_column(String)  # 'user' or 'assistant'
    content: Mapped[str] = mapped_column(Text)
    timestamp: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    conversation: Mapped["Conversation"] = relationship(back_populates="messages")


class HealthProfile(Base):
    __tablename__ = "health_profiles"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    date_of_birth: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True)
    sex: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    height: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    height_unit: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    weight: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    weight_unit: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    blood_type: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    timezone: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="health_profile")


class UserPreferences(Base):
    __tablename__ = "user_preferences"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    notif_product: Mapped[bool] = mapped_column(Boolean, default=True)
    notif_health: Mapped[bool] = mapped_column(Boolean, default=True)
    ai_data_pref: Mapped[bool] = mapped_column(Boolean, default=True)
    data_retention: Mapped[str] = mapped_column(String, default="90")
    doc_storage: Mapped[bool] = mapped_column(Boolean, default=True)
    theme: Mapped[str] = mapped_column(String, default="system")
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="preferences")


class HealthCondition(Base):
    __tablename__ = "health_conditions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, default="unknown") # active/resolved/historical/unknown
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(String, default="user") # user/document/import/system
    source_reference: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="conditions")


class Allergy(Base):
    __tablename__ = "allergies"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    substance: Mapped[str] = mapped_column(String, nullable=False)
    reaction: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    severity: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, default="active")
    source: Mapped[str] = mapped_column(String, default="user")
    source_reference: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="allergies")


class Medication(Base):
    __tablename__ = "medications"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    dose: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    dose_unit: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    frequency: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    route: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, default="active")
    start_date: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True)
    end_date: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(String, default="user")
    source_reference: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="medications")


class Lifestyle(Base):
    __tablename__ = "lifestyle_entries"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String, nullable=False) # sleep/exercise/nutrition/smoking/alcohol/caffeine/occupation/general
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(String, default="user")
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="lifestyle_entries")


class HealthGoal(Base):
    __tablename__ = "health_goals"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    category: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String, default="active") # active/completed/paused/cancelled
    target_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    target_unit: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    target_date: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="goals")


class Measurement(Base):
    __tablename__ = "measurements"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String, nullable=False) # weight/height/heart_rate/blood_pressure/temperature/blood_glucose/oxygen_saturation
    value: Mapped[float] = mapped_column(Float, nullable=False)
    secondary_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True) # e.g. diastolic
    unit: Mapped[str] = mapped_column(String, nullable=False)
    measured_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    source: Mapped[str] = mapped_column(String, default="user")
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="measurements")


class HealthDocument(Base):
    __tablename__ = "health_documents"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    filename: Mapped[str] = mapped_column(String, nullable=False)
    mime_type: Mapped[str] = mapped_column(String, nullable=False)
    file_size: Mapped[int] = mapped_column(Float, nullable=False) # In bytes
    storage_path: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    status: Mapped[str] = mapped_column(String, default="uploaded") # uploaded, processing, processed, needs_review, failed
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True) # Generated summary of the document
    uploaded_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    processed_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="documents")
    extractions: Mapped[list["DocumentExtraction"]] = relationship(back_populates="document", cascade="all, delete-orphan")


class DocumentExtraction(Base):
    __tablename__ = "document_extractions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    document_id: Mapped[str] = mapped_column(ForeignKey("health_documents.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String, nullable=False) # e.g. condition, medication, measurement, allergy
    data: Mapped[dict] = mapped_column(JSON, nullable=False) # Structured data fields
    source_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    confidence: Mapped[str] = mapped_column(String, default="high") # high, medium, low
    status: Mapped[str] = mapped_column(String, default="pending_review") # pending_review, confirmed, rejected
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="document_extractions")
    document: Mapped["HealthDocument"] = relationship(back_populates="extractions")


# --------------------------------------------------
# Phase 5A: Trusted Medical Evidence
# --------------------------------------------------

class MedicalSource(Base):
    __tablename__ = "medical_sources"
    
    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String, nullable=False)
    organization: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    source_type: Mapped[Optional[str]] = mapped_column(String, nullable=True) # e.g. guideline, academic, clinical_reference
    base_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    trust_level: Mapped[str] = mapped_column(String, default="high") # high, medium
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    
    documents: Mapped[list["KnowledgeDocument"]] = relationship(back_populates="source", cascade="all, delete-orphan")

class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"
    
    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    source_id: Mapped[str] = mapped_column(ForeignKey("medical_sources.id", ondelete="CASCADE"), index=True)
    
    title: Mapped[str] = mapped_column(String, nullable=False)
    url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    document_type: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    publication_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    content_hash: Mapped[Optional[str]] = mapped_column(String, unique=True, nullable=True)
    status: Mapped[str] = mapped_column(String, default="active")
    
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    source: Mapped["MedicalSource"] = relationship(back_populates="documents")
    chunks: Mapped[list["KnowledgeChunk"]] = relationship(back_populates="document", cascade="all, delete-orphan")

class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"
    
    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    document_id: Mapped[str] = mapped_column(ForeignKey("knowledge_documents.id", ondelete="CASCADE"), index=True)
    
    content: Mapped[str] = mapped_column(Text, nullable=False)
    section_title: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    page_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    chunk_index: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    content_hash: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    
    # HuggingFace all-MiniLM-L6-v2 uses 384 dimensions
    # Assuming Vector is imported from pgvector.sqlalchemy
    embedding: Mapped[list[float]] = mapped_column(Vector(384))
    
    # Exact keyword matching
    search_vector: Mapped[str] = mapped_column(TSVECTOR, nullable=True)
    
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    
    document: Mapped["KnowledgeDocument"] = relationship(back_populates="chunks")

class HealthEvent(Base):
    __tablename__ = "health_events"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String, nullable=False) # symptom, diagnosis, measurement, report, consultation, etc.
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    event_date: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    source_type: Mapped[str] = mapped_column(String, default="user") # conversation, report, user
    source_id: Mapped[Optional[str]] = mapped_column(String, nullable=True) # message id, report id
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    structured_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="health_events")
