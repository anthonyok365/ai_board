"""
FastAPI Server for AI Board of Directors Backend.

Deploy this on Render (or any Python hosting platform) to expose
the board meeting functionality as a REST API.

Usage:
    uvicorn server:app --host 0.0.0.0 --port $PORT
"""

import os
import logging
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import board meeting functions
from main import run_board_meeting, get_meeting_history, continue_meeting
from config import config, set_provider

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# Request/Response Models
# ============================================================================

class MeetingRequest(BaseModel):
    """Request model for starting a new board meeting."""
    query: str = Field(..., description="The business question or decision to discuss")
    thread_id: Optional[str] = Field(None, description="Custom thread ID for the meeting")
    use_premium: bool = Field(False, description="Use premium (more expensive) models")
    provider: Optional[str] = Field(None, description="LLM provider: 'xai' or 'groq'")
    stream: bool = Field(False, description="Enable streaming responses")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "Should we invest $800k in expanding our AI product line next quarter?",
                "thread_id": "meeting_001",
                "use_premium": False,
                "provider": "groq"
            }
        }


class MeetingResponse(BaseModel):
    """Response model for meeting results."""
    status: str
    thread_id: str
    query: str
    result: Dict[str, Any]
    history: Optional[list] = None


class ContinueRequest(BaseModel):
    """Request model for continuing an existing meeting."""
    thread_id: str = Field(..., description="The thread ID of the meeting to continue")
    query: str = Field(..., description="Follow-up question or direction")
    use_premium: bool = Field(False)

    class Config:
        json_schema_extra = {
            "example": {
                "thread_id": "meeting_001",
                "query": "What are the risks if we proceed?",
                "use_premium": False
            }
        }


class HistoryRequest(BaseModel):
    """Request model for getting meeting history."""
    thread_id: str = Field(..., description="The thread ID of the meeting")
    limit: int = Field(10, description="Maximum number of messages to return")


class ConfigUpdate(BaseModel):
    """Request model for updating configuration."""
    provider: Optional[str] = Field(None, description="LLM provider: 'xai' or 'groq'")
    use_premium: Optional[bool] = Field(None)


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str
    provider: str
    model: str
    api_key_configured: bool


# ============================================================================
# Lifespan Management
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    logger.info("Starting AI Board of Directors API Server")
    logger.info(f"Provider: {config.provider}, Model: {config.model}")
    
    # Check API key
    if config.api_key:
        logger.info(f"API key configured for {config.provider}")
    else:
        logger.warning("No API key configured! Set XAI_API_KEY or GROQ_API_KEY")
    
    yield
    
    logger.info("Shutting down AI Board of Directors API Server")


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="AI Board of Directors API",
    description="Multi-agent LangGraph system for AI-powered board meetings",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for your domains in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": "AI Board of Directors API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Check API health and configuration."""
    return HealthResponse(
        status="healthy",
        provider=config.provider,
        model=config.model,
        api_key_configured=config.api_key is not None
    )


@app.post("/meeting", response_model=MeetingResponse, tags=["Meetings"])
async def create_meeting(request: MeetingRequest):
    """
    Start a new board meeting.
    
    The board of directors (Strategist, Financial, Risk, CEO) will
    analyze the query and produce a structured decision.
    """
    try:
        # Update provider if specified
        if request.provider:
            set_provider(request.provider, request.use_premium)
        
        logger.info(f"Starting meeting: {request.query[:50]}...")
        
        result = run_board_meeting(
            additional_query=request.query,
            thread_id=request.thread_id,
            use_premium=request.use_premium,
            stream=request.stream
        )
        
        return MeetingResponse(
            status="completed",
            thread_id=result.get("thread_id", request.thread_id or "unknown"),
            additional_query=request.query,
            result=result
        )
        
    except Exception as e:
        logger.error(f"Meeting error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/meeting/continue", response_model=MeetingResponse, tags=["Meetings"])
async def continue_existing_meeting(request: ContinueRequest):
    """
    Continue an existing board meeting with follow-up questions.
    """
    try:
        logger.info(f"Continuing meeting {request.thread_id}: {request.query[:50]}...")
        
        result = continue_meeting(
            thread_id=request.thread_id,
            additional_query=request.query,
            use_premium=request.use_premium
        )
        
        return MeetingResponse(
            status="continued",
            thread_id=request.thread_id,
            additional_query=request.query,
            result=result
        )
        
    except Exception as e:
        logger.error(f"Continue meeting error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/meeting/{thread_id}", response_model=MeetingResponse, tags=["Meetings"])
async def get_meeting(thread_id: str):
    """Get the full history of a meeting."""
    try:
        history = get_meeting_history(thread_id)
        
        if not history:
            raise HTTPException(status_code=404, detail="Meeting not found")
        
        return MeetingResponse(
            status="found",
            thread_id=thread_id,
            query=history[0].get("query", "") if history else "",
            result={"messages": history},
            history=history
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get meeting error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/config", response_model=HealthResponse, tags=["Config"])
async def update_config(request: ConfigUpdate):
    """Update the LLM provider configuration."""
    try:
        if request.provider:
            set_provider(request.provider, request.use_premium or False)
        
        return HealthResponse(
            status="updated",
            provider=config.provider,
            model=config.model,
            api_key_configured=config.api_key is not None
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# Run Server
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=port,
        reload=False
    )
