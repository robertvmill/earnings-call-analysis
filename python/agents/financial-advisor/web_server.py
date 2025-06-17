#!/usr/bin/env python3

"""Custom FastAPI web server with CORS support for Financial Advisor."""

import os
import sys
import logging
from typing import Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = FastAPI(title="Financial Advisor API", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://localhost:3000",
        "*"  # In production, replace with your actual frontend URL
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for lazy initialization
runner = None

def initialize_agent():
    """Initialize the agent runner lazily."""
    global runner
    if runner is None:
        try:
            logger.info("Initializing financial advisor agent...")
            from financial_advisor.agent import root_agent
            from google.adk.runners import InMemoryRunner
            runner = InMemoryRunner(agent=root_agent)
            logger.info("Agent initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize agent: {e}")
            raise
    return runner

class ChatMessage(BaseModel):
    message: str

class ChatResponse(BaseModel):
    reply: str

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("Starting Financial Advisor API...")
    try:
        # Try to initialize the agent
        initialize_agent()
        logger.info("Startup completed successfully")
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        # Don't fail startup, let individual requests handle the error

@app.get("/")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "Financial Advisor API"}

@app.get("/api/health")
async def api_health():
    """API health check."""
    try:
        # Try to initialize agent if not already done
        initialize_agent()
        return {"status": "ok", "agent": "financial_advisor", "ready": True}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "error", "agent": "financial_advisor", "ready": False, "error": str(e)}

@app.post("/api/agent")
async def chat_with_agent(chat_message: ChatMessage) -> ChatResponse:
    """Chat with the financial advisor agent."""
    try:
        # Initialize agent if not already done
        agent_runner = initialize_agent()
        
        # Import here to avoid import issues during startup
        from google.genai.types import Part, UserContent
        
        # Create a session for this request
        session = await agent_runner.session_service.create_session(
            app_name=agent_runner.app_name, user_id="web_user"
        )
        
        # Create user content from the message
        content = UserContent(parts=[Part(text=chat_message.message)])
        
        # Run the agent with the user's message and collect the response
        response_text = ""
        async for event in agent_runner.run_async(
            user_id=session.user_id,
            session_id=session.id,
            new_message=content,
        ):
            if event.content.parts and event.content.parts[0].text:
                response_text += event.content.parts[0].text
        
        return ChatResponse(reply=response_text.strip())
        
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    
    # Cloud Run provides PORT environment variable, default to 8000 for local dev
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    logger.info(f"Starting Financial Advisor API server on {host}:{port}")
    logger.info("CORS enabled for localhost:3000")
    logger.info(f"Environment PORT: {os.getenv('PORT', 'not set')}")
    
    try:
        uvicorn.run(
            app,  # Pass the app object directly instead of string
            host=host,
            port=port,
            reload=False,
            log_level="info",
            access_log=True
        )
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1) 