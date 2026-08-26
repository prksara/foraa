import logging
import json
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

# Load .env before anything reads environment variables.
load_dotenv()

from ai.service import AIService, AIServiceError
from api.conversation_manager import manager as conv_manager
from database.database import init_db, get_db
from sqlalchemy.ext.asyncio import AsyncSession
from auth.security import get_current_user
from database.models import User
from ai.health_context import HealthContextBuilder
from api.health import router as health_router
from api.reports import router as reports_router

# --------------------------------------------------
# Logging
# --------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(name)-18s  %(levelname)-5s  %(message)s",
)
logger = logging.getLogger("foraa.main")


# --------------------------------------------------
# Lifespan
# --------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up...")
    # Still calling init_db to create tables if they don't exist (like sqlite)
    # But Alembic handles Postgres migrations. This is safe to run.
    await init_db()
    yield
    # Shutdown
    logger.info("Shutting down...")


# --------------------------------------------------
# App
# --------------------------------------------------

app = FastAPI(
    title="Foraa AI",
    version="0.3.0",
    description="Healthcare Intelligence API",
    lifespan=lifespan
)


# --------------------------------------------------
# CORS
# --------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------
# AI Service (initialized once at startup)
# --------------------------------------------------

_ai_service: AIService | None = None


def _get_ai_service() -> AIService:
    """Return the singleton AIService, creating it on first call."""
    global _ai_service
    if _ai_service is None:
        _ai_service = AIService()
    return _ai_service


# --------------------------------------------------
# Pydantic Schemas
# --------------------------------------------------

class MessageSchema(BaseModel):
    id: str
    role: str
    content: str
    timestamp: datetime

    class Config:
        from_attributes = True

class ConversationSchema(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    messages: List[MessageSchema] = Field(default_factory=list)

    class Config:
        from_attributes = True

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    active_report_id: Optional[str] = None

class ChatResponse(BaseModel):
    reply: str


# --------------------------------------------------
# Routes
# --------------------------------------------------

@app.get("/")
async def root():
    return {
        "name": "Foraa AI",
        "version": "0.3.0",
        "status": "running",
    }


@app.get("/health")
async def health():
    return {
        "status": "ok",
    }

app.include_router(health_router)
app.include_router(reports_router)


# Conversation Management Routes

@app.get("/conversations", response_model=List[ConversationSchema])
async def list_conversations(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    return await conv_manager.list_conversations(db, user_id=user.id)

@app.post("/conversations", response_model=ConversationSchema)
async def create_conversation(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    return await conv_manager.create_conversation(db, user_id=user.id)

@app.get("/conversations/{conv_id}", response_model=ConversationSchema)
async def get_conversation(
    conv_id: str, 
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    conv = await conv_manager.get_conversation(db, conv_id, user_id=user.id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found or unauthorized")
    return conv

@app.delete("/conversations/{conv_id}")
async def delete_conversation(
    conv_id: str, 
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    if not await conv_manager.delete_conversation(db, conv_id, user_id=user.id):
        raise HTTPException(status_code=404, detail="Conversation not found or unauthorized")
    return {"status": "deleted"}


# Chat Routes

@app.post("/chat/stream")
async def chat_stream(
    request: ChatRequest, 
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Streaming chat endpoint strictly bounded by user authentication context."""
    try:
        service = _get_ai_service()
        
        # 1. Manage Conversation
        conv_id = request.conversation_id
        if not conv_id:
            conv = await conv_manager.create_conversation(db, user_id=user.id)
            conv_id = conv.id
        else:
            conv = await conv_manager.get_conversation(db, conv_id, user_id=user.id)
            if not conv:
                raise HTTPException(status_code=404, detail="Conversation not found or unauthorized")
                
        # 2. Add User Message
        await conv_manager.add_message(db, conv_id, user_id=user.id, role="user", content=request.message)
        
        # Reload conversation to get fresh messages list for context
        conv = await conv_manager.get_conversation(db, conv_id, user_id=user.id)
        
        # 3. Build Context
        context_messages = [{"role": msg.role, "content": msg.content} for msg in conv.messages]
        
        health_builder = HealthContextBuilder(db, user)
        health_context_str = await health_builder.build_context(request.message, active_report_id=request.active_report_id)
        context_messages.insert(0, {"role": "system", "content": health_context_str})
        
        # 4. Stream response and capture full reply
        async def event_generator():
            full_reply = ""
            try:
                # Yield SSE format with conversation_id
                yield f"data: {json.dumps({'conversation_id': conv_id})}\n\n"
                
                for chunk in service.generate_stream(context_messages):
                    if chunk:
                        full_reply += chunk
                        yield f"data: {json.dumps({'content': chunk})}\n\n"
                
                # After stream completes, save assistant message safely
                if full_reply:
                    async for safe_db in get_db():
                        await conv_manager.add_message(safe_db, conv_id, user_id=user.id, role="assistant", content=full_reply)
                        break
                    
                yield "data: [DONE]\n\n"
                
            except Exception as e:
                logger.exception("Error during streaming")
                yield f"data: {json.dumps({'error': str(e)})}\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")

    except AIServiceError as exc:
        logger.warning("AIServiceError: %s", exc)
        raise HTTPException(status_code=exc.status_code, detail=str(exc))
    except Exception as e:
        logger.exception("Unexpected error in /chat/stream")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred. Please try again.",
        )