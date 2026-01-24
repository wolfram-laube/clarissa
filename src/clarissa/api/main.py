"""
CLARISSA API - Main Application

FastAPI application providing REST endpoints for CLARISSA services.

Endpoints:
    GET  /health           - Health check
    GET  /                 - API info
    POST /api/v1/chat      - Chat with CLARISSA
    POST /api/v1/simulate  - Run simulation
    GET  /api/v1/status/{job_id} - Check job status
"""

import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from clarissa.config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# ============== Lifespan ==============
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown."""
    # Startup
    logger.info(f"Starting CLARISSA API in {settings.environment} mode")
    logger.info(f"LLM Provider: {settings.llm_provider}")
    
    if settings.use_firestore_emulator:
        logger.info(f"Using Firestore Emulator: {settings.firestore_emulator_host}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down CLARISSA API")


# ============== Application ==============
app = FastAPI(
    title="CLARISSA API",
    description="Conversational Language Agent for Reservoir Integrated Simulation System Analysis",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.is_local else ["https://clarissa.blauweiss-edv.at"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============== Models ==============
class HealthResponse(BaseModel):
    status: str
    environment: str
    timestamp: str
    version: str
    llm_provider: str


class ChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None


class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    timestamp: str


class SimulationRequest(BaseModel):
    deck_content: str | None = None
    deck_url: str | None = None
    parameters: dict[str, Any] | None = None


class SimulationResponse(BaseModel):
    job_id: str
    status: str
    message: str


class JobStatus(BaseModel):
    job_id: str
    status: str
    progress: float | None = None
    result: dict[str, Any] | None = None
    error: str | None = None


# ============== Routes ==============
@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """
    Health check endpoint.
    
    Returns current service status and configuration info.
    Used by Docker health checks and load balancers.
    """
    return HealthResponse(
        status="healthy",
        environment=settings.environment,
        timestamp=datetime.now(timezone.utc).isoformat(),
        version="0.1.0",
        llm_provider=settings.llm_provider,
    )


@app.get("/", tags=["System"])
async def root():
    """API root - returns basic info."""
    return {
        "name": "CLARISSA API",
        "version": "0.1.0",
        "description": "Conversational Language Agent for Reservoir Simulation",
        "docs": "/docs" if settings.debug else None,
        "health": "/health",
    }


@app.post("/api/v1/chat", response_model=ChatResponse, tags=["Chat"])
async def chat(request: ChatRequest):
    """
    Chat with CLARISSA.
    
    Send a natural language message and receive a response.
    Optionally provide a conversation_id to continue a previous conversation.
    """
    import uuid
    
    # TODO: Implement actual LLM integration
    conversation_id = request.conversation_id or str(uuid.uuid4())
    
    # Placeholder response
    response_text = f"[{settings.llm_provider}] I received your message: '{request.message[:50]}...'. LLM integration coming soon!"
    
    return ChatResponse(
        response=response_text,
        conversation_id=conversation_id,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@app.post("/api/v1/simulate", response_model=SimulationResponse, tags=["Simulation"])
async def simulate(request: SimulationRequest):
    """
    Submit a simulation job.
    
    Provide either deck_content (inline) or deck_url (reference).
    Returns a job_id for status tracking.
    """
    import uuid
    
    if not request.deck_content and not request.deck_url:
        raise HTTPException(
            status_code=400,
            detail="Either deck_content or deck_url must be provided"
        )
    
    job_id = str(uuid.uuid4())
    
    # TODO: Implement actual simulation job submission
    logger.info(f"Simulation job submitted: {job_id}")
    
    return SimulationResponse(
        job_id=job_id,
        status="queued",
        message="Simulation job submitted. Use /api/v1/status/{job_id} to check progress.",
    )


@app.get("/api/v1/status/{job_id}", response_model=JobStatus, tags=["Simulation"])
async def get_job_status(job_id: str):
    """
    Get simulation job status.
    
    Returns current status, progress, and results (if complete).
    """
    # TODO: Implement actual job status lookup
    return JobStatus(
        job_id=job_id,
        status="pending",
        progress=0.0,
        result=None,
        error=None,
    )


# ============== Error Handlers ==============
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors."""
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    
    if settings.debug:
        return {"error": str(exc), "type": type(exc).__name__}
    
    return {"error": "Internal server error"}
