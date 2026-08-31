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
from api.settings import router as settings_router
from services.evidence_retrieval import EvidenceRetrievalService
from ai.intent import IntentAnalyzer
from services.memory_extraction import MemoryExtractor
import asyncio
import time

from safety import (
    SafetyClassifier, MedicationSafetyChecker, PostGenerationValidator, SafetyLevel, ValidationResult
)
from database.models import SafetyEvent

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

import os
_env_cors = os.getenv("CORS_ORIGINS", "")
_allowed_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
if _env_cors:
    for origin in _env_cors.split(","):
        o = origin.strip()
        if o and o not in _allowed_origins:
            _allowed_origins.append(o)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_origin_regex=r"https://.*\.vercel\.app$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------
# AI Service (initialized once at startup)
# --------------------------------------------------

_ai_service: AIService | None = None
_intent_analyzer: IntentAnalyzer | None = None

def _get_ai_service() -> AIService:
    """Return the singleton AIService, creating it on first call."""
    global _ai_service
    if _ai_service is None:
        _ai_service = AIService()
    return _ai_service

def _get_intent_analyzer() -> IntentAnalyzer:
    global _intent_analyzer
    if _intent_analyzer is None:
        _intent_analyzer = IntentAnalyzer()
    return _intent_analyzer


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
    is_archived: bool = False
    created_at: datetime
    updated_at: datetime
    messages: List[MessageSchema] = Field(default_factory=list)

    class Config:
        from_attributes = True

class ConversationUpdate(BaseModel):
    title: str

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    attachment_ids: Optional[List[str]] = None

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
app.include_router(settings_router)


# Conversation Management Routes

@app.get("/conversations", response_model=List[ConversationSchema])
async def list_conversations(
    include_archived: bool = False,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    return await conv_manager.list_conversations(db, user_id=user.id, include_archived=include_archived)

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

@app.put("/conversations/{conv_id}", response_model=ConversationSchema)
async def update_conversation(
    conv_id: str,
    update_data: ConversationUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    conv = await conv_manager.rename_conversation(db, conv_id, user_id=user.id, title=update_data.title)
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

@app.post("/conversations/{conv_id}/archive", response_model=ConversationSchema)
async def archive_conversation(
    conv_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    conv = await conv_manager.archive_conversation(db, conv_id, user_id=user.id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found or unauthorized")
    return conv

@app.post("/conversations/{conv_id}/unarchive", response_model=ConversationSchema)
async def unarchive_conversation(
    conv_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    conv = await conv_manager.unarchive_conversation(db, conv_id, user_id=user.id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found or unauthorized")
    return conv


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
        
        # 3. Build preliminary basic context for the reasoning engine
        health_builder = HealthContextBuilder(db, user)
        base_context = await health_builder.build_context(request.message, attachment_ids=request.attachment_ids)

        # 4. Stream response and execute reasoning pipeline concurrently
        async def event_generator():
            full_reply = ""
            try:
                # Yield SSE format with conversation_id
                metadata_payload = {'conversation_id': conv_id}
                yield f"data: {json.dumps(metadata_payload)}\n\n"
                
                # Callback to emit reasoning states
                async def yield_status(msg: str):
                    await asyncio.sleep(0) # Yield control
                    # Not using yield here because it's inside a nested function,
                    # but we can mutate a queue or just let it pass to the generator.
                    # Wait, nested yield doesn't work that way. 
                    pass

                # We must yield directly from the main generator loop, so we can't use a callback easily
                # without an asyncio.Queue. Let's use a queue to bridge the engine's async emissions.
                queue = asyncio.Queue()
                
                async def yield_status_callback(msg: str):
                    await queue.put({"reasoning_status": msg})
                    
                # Instantiate Safety & Reasoning Checkers
                from reasoning.engine import ReasoningEngine
                from reasoning.schemas import ReasoningState, ResponsePolicy
                import uuid
                
                req_id = str(uuid.uuid4())
                state = ReasoningState(
                    request_id=req_id,
                    user_id=str(user.id),
                    conversation_id=str(conv_id),
                    message=request.message
                )
                engine = ReasoningEngine()
                
                # Pre-Initialize safety evaluators
                safety_classifier = SafetyClassifier()
                med_safety = MedicationSafetyChecker()
                post_validator = PostGenerationValidator()

                # Run reasoning in a task so we can stream from the queue simultaneously
                async def run_reasoning():
                    start_time = time.time()
                    try:
                        # --- PHASE 8: SAFETY PRE-CHECK ---
                        await queue.put({"reasoning_status": "Checking safety constraints..."})
                        safety_result = await asyncio.to_thread(safety_classifier.classify, state.message, base_context)
                        med_result = await asyncio.to_thread(med_safety.check, state.message, base_context)
                        
                        latency = int((time.time() - start_time) * 1000)
                        
                        # Log Safety Event
                        async for safe_db in get_db():
                            safety_event = SafetyEvent(
                                request_id=req_id,
                                user_id=str(user.id),
                                conversation_id=str(conv_id),
                                safety_level=safety_result.level.value,
                                detected_signals=safety_result.detected_signals + med_result.get("medication_alerts", []),
                                latency_ms=latency
                            )
                            safe_db.add(safety_event)
                            await safe_db.commit()
                            break

                        if safety_result.level in [SafetyLevel.URGENT, SafetyLevel.EMERGENCY] or not med_result["is_safe"]:
                            logger.warning(f"Safety constraint violated. Escalating. Level: {safety_result.level}")
                            await queue.put({"safety_escalation": {
                                "level": safety_result.level.value,
                                "reasons": safety_result.reasons,
                                "alerts": med_result.get("medication_alerts", []),
                                "recommended_action": safety_result.recommended_action
                            }})
                            state.response_policy = ResponsePolicy.SAFETY_ESCALATION
                            # Return early, skip full pipeline
                            await queue.put({"final_context": base_context, "state": state, "safety_result": safety_result})
                            return

                        # --- PHASE 7: REASONING & EVIDENCE ---
                        # Retrieval
                        evidence_pack = None
                        evidence_text = ""
                        
                        # First classify to know if we need evidence
                        state.intent = await asyncio.to_thread(engine.classifier.classify, state.message)
                        
                        if state.intent.is_health_log:
                            await queue.put({"reasoning_status": "Extracting health data..."})
                            from services.health_log_parser import HealthLogParser
                            parser = HealthLogParser()
                            extracted_log = await asyncio.to_thread(parser.parse, state.message)
                            if extracted_log:
                                await queue.put({"health_log_extracted": extracted_log})

                        if state.intent.needs_evidence:
                            await queue.put({"reasoning_status": "Searching medical knowledge base..."})
                            retrieval_service = EvidenceRetrievalService(db)
                            evidence_pack = await retrieval_service.search(request.message, limit=5)
                            
                            from services.reranking import Reranker
                            reranker = Reranker(service)
                            evidence_pack.retrieved_items = await asyncio.to_thread(
                                reranker.rerank, request.message, evidence_pack.retrieved_items
                            )
                            evidence_pack.retrieved_items = evidence_pack.retrieved_items[:3]
                            evidence_pack.retrieval_metadata["reranked"] = True
                            state.evidence_gathered = True
                            
                            if evidence_pack.retrieved_items:
                                evidence_text = "\n".join([item.content for item in evidence_pack.retrieved_items])
                                
                                # Send evidence metadata down the pipe
                                await queue.put({
                                    "evidence_metadata": [
                                        {
                                            "source_name": item.source_name,
                                            "title": item.title,
                                            "url": item.url,
                                            "publication_date": item.publication_date,
                                            "citation": item.citation_reference
                                        } for item in evidence_pack.retrieved_items
                                    ]
                                })

                        # Execute the rest of the pipeline
                        final_state = await engine.execute_reasoning_pipeline(
                            state, base_context, evidence_text, yield_status_callback
                        )
                        
                        # Build Final Context based on filtered keys
                        # We pass the final_state to filter the context appropriately
                        final_context = await health_builder.build_context(
                            request.message, 
                            attachment_ids=request.attachment_ids,
                            evidence_pack=evidence_pack,
                            intent=final_state.intent.model_dump() if final_state.intent else None
                        )
                        
                        await queue.put({"final_context": final_context, "state": final_state})
                    except Exception as e:
                        logger.error(f"Reasoning task failed: {e}")
                        await queue.put({"error": str(e)})

                reasoning_task = asyncio.create_task(run_reasoning())
                
                final_context = base_context
                final_state = None
                safety_escalation_data = None
                
                # Consume queue until reasoning is done
                while not reasoning_task.done() or not queue.empty():
                    try:
                        # Wait for item or task completion
                        msg = await asyncio.wait_for(queue.get(), timeout=0.1)
                        if "final_context" in msg:
                            final_context = msg["final_context"]
                            final_state = msg.get("state")
                            break # Reasoning done
                        elif "safety_escalation" in msg:
                            safety_escalation_data = msg["safety_escalation"]
                            yield f"data: {json.dumps({'safety_notice': safety_escalation_data})}\n\n"
                        elif "error" in msg:
                            yield f"data: {json.dumps({'error': msg['error']})}\n\n"
                            break
                        else:
                            yield f"data: {json.dumps(msg)}\n\n"
                    except asyncio.TimeoutError:
                        continue
                        
                # 3.5 Run memory extraction in background task (only if user enabled AI data preferences)
                async def background_memory_extraction(msg_content, uid, msg_id):
                    async for safe_db in get_db():
                        from database.models import UserPreferences
                        from sqlalchemy import select
                        pref_res = await safe_db.execute(select(UserPreferences).where(UserPreferences.user_id == uid))
                        prefs = pref_res.scalars().first()
                        if prefs and not prefs.ai_data_pref:
                            logger.info(f"User {uid} opted out of AI memory extraction. Skipping.")
                            break

                        extractor = MemoryExtractor(service)
                        await extractor.extract_health_events(msg_content, uid, msg_id, safe_db)
                        break
                asyncio.create_task(background_memory_extraction(request.message, user.id, conv_id))

                # Clear reasoning status in frontend before text generation
                yield f"data: {json.dumps({'reasoning_status': None})}\n\n"

                # 5. Generate Text
                context_messages = [{"role": msg.role, "content": msg.content} for msg in conv.messages]
                context_messages.insert(0, {"role": "system", "content": final_context})
                
                for chunk in service.generate_stream(context_messages):
                    if chunk:
                        full_reply += chunk
                        yield f"data: {json.dumps({'content': chunk})}\n\n"
                
                # After stream completes, validate response
                validation_result: ValidationResult = None
                if full_reply and not safety_escalation_data:
                    validation_result = await asyncio.to_thread(
                        post_validator.validate, 
                        full_reply, 
                        final_state.evidence_metadata if final_state and hasattr(final_state, 'evidence_metadata') else []
                    )
                    
                    if not validation_result.is_safe:
                        logger.warning(f"Post-generation safety validation failed: {validation_result.rewrite_reason}")
                        # In a real app we might redact or rewrite here, but since it's already streamed,
                        # we can emit a correction or just log it heavily.
                        yield f"data: {json.dumps({'validation_warning': validation_result.rewrite_reason})}\n\n"
                
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