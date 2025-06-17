#!/usr/bin/env python3

"""Custom FastAPI web server with CORS support for Financial Advisor."""

import os
from typing import Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from financial_advisor.agent import root_agent
from google.adk.runners import InMemoryRunner
from google.genai.types import Part, UserContent

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

# Initialize the agent runner with the agent
runner = InMemoryRunner(agent=root_agent)

class ChatMessage(BaseModel):
    message: str

class ChatResponse(BaseModel):
    reply: str

@app.get("/")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "Financial Advisor API"}

@app.post("/api/agent")
async def chat_with_agent(chat_message: ChatMessage) -> ChatResponse:
    """Chat with the financial advisor agent."""
    try:
        # Create a session for this request
        session = await runner.session_service.create_session(
            app_name=runner.app_name, user_id="web_user"
        )
        
        # Create user content from the message
        content = UserContent(parts=[Part(text=chat_message.message)])
        
        # Run the agent with the user's message and collect the response
        response_text = ""
        async for event in runner.run_async(
            user_id=session.user_id,
            session_id=session.id,
            new_message=content,
        ):
            if event.content.parts and event.content.parts[0].text:
                response_text += event.content.parts[0].text
        
        return ChatResponse(reply=response_text.strip())
        
    except Exception as e:
        print(f"Error processing request: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/api/health")
async def api_health():
    """API health check."""
    return {"status": "ok", "agent": "financial_advisor"}

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    print(f"Starting Financial Advisor API server on {host}:{port}")
    print("CORS enabled for localhost:3000")
    
    uvicorn.run(
        "web_server:app",
        host=host,
        port=port,
        reload=False
    ) 