"""FastAPI server for the AI Chat application."""

import logging
import uuid
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from .agent import ChatAgent
from .config import settings
from .database import init_db, get_db, UserSession
from .memory import PostgreSQLChatMemory
from .tool_selector import ToolSelector

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global tool selector
tool_selector: Optional[ToolSelector] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown."""
    global tool_selector

    # Startup
    logger.info("Starting AI Chat API...")
    init_db()
    logger.info("Database initialized")

    # Initialize tool selector
    try:
        tool_selector = ToolSelector.from_config_file()
        logger.info("Tool selector initialized")
    except Exception as e:
        logger.error(f"Failed to initialize tool selector: {e}")
        tool_selector = None

    yield

    # Shutdown
    logger.info("Shutting down AI Chat API...")


# FastAPI app
app = FastAPI(
    title="AI Chat API",
    description="Agentic AI chat with Vertex AI, PostgreSQL RAG, and MCP integration",
    version="0.1.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models
class ChatRequest(BaseModel):
    """Request model for chat endpoint."""

    message: str = Field(..., description="User's message")
    user_id: str = Field(..., description="User identifier")
    session_id: Optional[str] = Field(None, description="Session ID (optional, will be created if not provided)")


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""

    response: str = Field(..., description="Agent's response")
    session_id: str = Field(..., description="Session identifier")
    user_id: str = Field(..., description="User identifier")


class HistoryRequest(BaseModel):
    """Request model for history endpoint."""

    session_id: str = Field(..., description="Session identifier")
    user_id: str = Field(..., description="User identifier")
    limit: Optional[int] = Field(10, description="Maximum number of messages")


class Message(BaseModel):
    """Message model."""

    role: str
    content: str
    created_at: str
    metadata: dict = {}


class HistoryResponse(BaseModel):
    """Response model for history endpoint."""

    session_id: str
    user_id: str
    messages: List[Message]


class SessionRequest(BaseModel):
    """Request model for creating a session."""

    user_id: str = Field(..., description="User identifier")


class SessionResponse(BaseModel):
    """Response model for session operations."""

    session_id: str
    user_id: str
    created_at: str


# Dependency to get or create session
def get_or_create_session(
    user_id: str,
    session_id: Optional[str] = None,
    db: Session = Depends(get_db)
) -> str:
    """Get or create a user session."""
    if session_id:
        # Verify session exists and belongs to user
        session = db.query(UserSession).filter(
            UserSession.session_id == session_id,
            UserSession.user_id == user_id
        ).first()

        if not session:
            raise HTTPException(
                status_code=404,
                detail=f"Session {session_id} not found for user {user_id}"
            )

        return session_id
    else:
        # Create new session
        new_session_id = str(uuid.uuid4())
        session = UserSession(
            session_id=new_session_id,
            user_id=user_id,
            is_active=1
        )
        db.add(session)
        db.commit()

        return new_session_id


# API endpoints
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "AI Chat API",
        "version": "0.1.0",
        "status": "running"
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """Chat endpoint for sending messages to the agent."""
    if tool_selector is None:
        raise HTTPException(
            status_code=503,
            detail="Tool selector not initialized"
        )

    try:
        # Get or create session
        session_id = get_or_create_session(
            request.user_id,
            request.session_id,
            db
        )

        # Create agent with memory
        memory = PostgreSQLChatMemory(
            session_id=session_id,
            user_id=request.user_id,
            db_session=db
        )

        agent = ChatAgent(
            session_id=session_id,
            user_id=request.user_id,
            tool_selector=tool_selector,
            memory=memory
        )

        # Process message
        response = await agent.chat(request.message)

        return ChatResponse(
            response=response,
            session_id=session_id,
            user_id=request.user_id
        )

    except Exception as e:
        logger.error(f"Error processing chat request: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/history", response_model=HistoryResponse)
async def get_history(
    request: HistoryRequest,
    db: Session = Depends(get_db)
):
    """Get chat history for a session."""
    try:
        memory = PostgreSQLChatMemory(
            session_id=request.session_id,
            user_id=request.user_id,
            db_session=db
        )

        messages = memory.get_messages(limit=request.limit)

        return HistoryResponse(
            session_id=request.session_id,
            user_id=request.user_id,
            messages=[Message(**msg) for msg in messages]
        )

    except Exception as e:
        logger.error(f"Error getting history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/session", response_model=SessionResponse)
async def create_session(
    request: SessionRequest,
    db: Session = Depends(get_db)
):
    """Create a new session for a user."""
    try:
        session_id = str(uuid.uuid4())
        session = UserSession(
            session_id=session_id,
            user_id=request.user_id,
            is_active=1
        )
        db.add(session)
        db.commit()
        db.refresh(session)

        return SessionResponse(
            session_id=session.session_id,
            user_id=session.user_id,
            created_at=session.created_at.isoformat()
        )

    except Exception as e:
        logger.error(f"Error creating session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/session/{session_id}")
async def delete_session(
    session_id: str,
    user_id: str,
    db: Session = Depends(get_db)
):
    """Delete a session."""
    try:
        session = db.query(UserSession).filter(
            UserSession.session_id == session_id,
            UserSession.user_id == user_id
        ).first()

        if not session:
            raise HTTPException(
                status_code=404,
                detail=f"Session {session_id} not found"
            )

        session.is_active = 0
        db.commit()

        return {"message": "Session deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}
