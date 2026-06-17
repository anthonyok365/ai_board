"""
FastAPI Server for AI Board of Directors Backend.
"""

import os
import logging
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

from main import run_board_meeting, get_meeting_history, continue_meeting
from config import config, set_provider

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MeetingRequest(BaseModel):
    query: str
    thread_id: Optional[str] = None
    use_premium: bool = False
    provider: Optional[str] = None
    stream: bool = False


class MeetingResponse(BaseModel):
    status: str
    thread_id: str
    query: str
    result: dict


class ContinueRequest(BaseModel):
    thread_id: str
    query: str
    use_premium: bool = False


class HealthResponse(BaseModel):
    status: str
    provider: str
    model: str
    api_key_configured: bool


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting API - Provider: {config.provider}, Model: {config.model}")
    yield
    logger.info("Shutting down API")


app = FastAPI(title="AI Board API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"name": "AI Board API", "version": "1.0.0", "docs": "/docs"}


@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="healthy",
        provider=config.provider,
        model=config.model,
        api_key_configured=config.api_key is not None
    )


@app.post("/meeting", response_model=MeetingResponse)
async def create_meeting(request: MeetingRequest):
    try:
        if request.provider:
            set_provider(request.provider, request.use_premium)
        
        logger.info(f"Starting meeting: {request.query[:50]}...")
        
        result = run_board_meeting(
            query=request.query,
            thread_id=request.thread_id,
            use_premium=request.use_premium,
            stream=request.stream
        )
        
        return MeetingResponse(
            status="completed",
            thread_id=result.get("thread_id", request.thread_id or "unknown"),
            query=request.query,
            result=result
        )
    except Exception as e:
        logger.error(f"Meeting error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/meeting/continue", response_model=MeetingResponse)
async def continue_existing_meeting(request: ContinueRequest):
    try:
        logger.info(f"Continuing meeting {request.thread_id}: {request.query[:50]}...")
        
        result = continue_meeting(
            thread_id=request.thread_id,
            additional_query=request.query
        )
        
        return MeetingResponse(
            status="continued",
            thread_id=request.thread_id,
            query=request.query,
            result=result
        )
    except Exception as e:
        logger.error(f"Continue meeting error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/meeting/{thread_id}", response_model=MeetingResponse)
async def get_meeting(thread_id: str):
    try:
        history = get_meeting_history(thread_id)
        if not history:
            raise HTTPException(status_code=404, detail="Meeting not found")
        return MeetingResponse(
            status="found",
            thread_id=thread_id,
            query=history[0].get("query", "") if history else "",
            result={"messages": history}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("server:app", host="0.0.0.0", port=port)
