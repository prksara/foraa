import logging

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Load .env before anything reads environment variables.
load_dotenv()

from ai.service import AIService, AIServiceError  # noqa: E402


# --------------------------------------------------
# Logging
# --------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(name)-18s  %(levelname)-5s  %(message)s",
)
logger = logging.getLogger("foraa.main")


# --------------------------------------------------
# App
# --------------------------------------------------

app = FastAPI(
    title="Foraa AI",
    version="0.2.0",
    description="Healthcare Intelligence API",
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
# Models
# --------------------------------------------------

class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str


# --------------------------------------------------
# Routes
# --------------------------------------------------

@app.get("/")
async def root():
    return {
        "name": "Foraa AI",
        "version": "0.2.0",
        "status": "running",
    }


@app.get("/health")
async def health():
    return {
        "status": "ok",
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    try:
        service = _get_ai_service()
        reply = service.generate_response(request.message)
        return ChatResponse(reply=reply)
    except AIServiceError as exc:
        logger.warning("AIServiceError: %s", exc)
        raise HTTPException(status_code=exc.status_code, detail=str(exc))
    except Exception:
        logger.exception("Unexpected error in /chat")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred. Please try again.",
        )