#!/usr/bin/env python3

"""Simple CORS proxy for Financial Advisor ADK backend."""

import httpx
import uuid
import json
import asyncio
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
import os
import uvicorn

app = FastAPI(title="Financial Advisor CORS Proxy", version="1.0.0")

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

# Backend URL
BACKEND_URL = "https://financial-advisor-641352703162.us-central1.run.app"

class ChatMessage(BaseModel):
    message: str
    streaming: bool = False

@app.get("/")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "Financial Advisor CORS Proxy"}

@app.post("/api/agent")
async def proxy_agent_request(chat_message: ChatMessage):
    """Proxy requests to the ADK backend using the /run endpoint."""
    if chat_message.streaming:
        return StreamingResponse(
            stream_agent_response(chat_message.message),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
            }
        )
    else:
        return await get_agent_response(chat_message.message)

async def stream_agent_response(message: str):
    """Stream the agent response token by token."""
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            # Create session
            user_id = "web_user"
            session_create_response = await client.post(
                f"{BACKEND_URL}/apps/financial_advisor/users/{user_id}/sessions",
                json={}
            )
            
            if session_create_response.status_code != 200:
                yield f"data: {json.dumps({'error': 'Failed to create session'})}\n\n"
                return
                
            session_data = session_create_response.json()
            session_id = session_data["id"]
            
            # Stream from /run_sse endpoint
            run_request = {
                "appName": "financial_advisor",
                "userId": user_id,
                "sessionId": session_id,
                "newMessage": {
                    "parts": [{"text": message}],
                    "role": "user"
                },
                "streaming": True
            }
            
            async with client.stream(
                "POST",
                f"{BACKEND_URL}/run_sse",
                json=run_request,
                headers={"Accept": "text/event-stream"}
            ) as response:
                if response.status_code == 200:
                    async for chunk in response.aiter_text():
                        if chunk.strip():
                            # Parse SSE data
                            for line in chunk.split('\n'):
                                if line.startswith('data: '):
                                    try:
                                        event_data = json.loads(line[6:])
                                        if event_data.get("content") and event_data.get("content", {}).get("parts"):
                                            for part in event_data["content"]["parts"]:
                                                if part.get("text"):
                                                    yield f"data: {json.dumps({'token': part['text']})}\n\n"
                                    except json.JSONDecodeError:
                                        continue
                else:
                    yield f"data: {json.dumps({'error': f'Backend error: {response.status_code}'})}\n\n"
                    
    except Exception as e:
        yield f"data: {json.dumps({'error': f'Streaming error: {str(e)}'})}\n\n"
    
    yield f"data: {json.dumps({'done': True})}\n\n"

async def get_agent_response(message: str):
    """Get non-streaming agent response."""
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            # First, create a session
            user_id = "web_user"
            session_create_response = await client.post(
                f"{BACKEND_URL}/apps/financial_advisor/users/{user_id}/sessions",
                json={}
            )
            
            if session_create_response.status_code != 200:
                print(f"Session creation failed: {session_create_response.status_code} - {session_create_response.text}")
                raise HTTPException(status_code=500, detail="Failed to create session")
                
            session_data = session_create_response.json()
            session_id = session_data["id"]
            
            # Now use the /run endpoint with the session
            run_request = {
                "appName": "financial_advisor",
                "userId": user_id,
                "sessionId": session_id,
                "newMessage": {
                    "parts": [{"text": message}],
                    "role": "user"
                },
                "streaming": False
            }
            
            response = await client.post(
                f"{BACKEND_URL}/run",
                json=run_request
            )
            
            if response.status_code == 200:
                events = response.json()
                
                # Extract the response from the events
                reply_text = ""
                for event in events:
                    if event.get("content") and event.get("content", {}).get("parts"):
                        for part in event["content"]["parts"]:
                            if part.get("text"):
                                reply_text += part["text"]
                
                if reply_text:
                    return JSONResponse({"reply": format_text(reply_text.strip())})
                else:
                    return JSONResponse({"reply": "I received your message but couldn't generate a response. Please try again."})
            else:
                print(f"Backend error: {response.status_code} - {response.text}")
                raise HTTPException(status_code=500, detail=f"Backend error: {response.status_code}")
                
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Request timeout - the AI is processing your request")
    except Exception as e:
        print(f"Proxy error: {e}")
        raise HTTPException(status_code=500, detail=f"Proxy error: {str(e)}")

def format_text(text: str) -> str:
    """Format raw text to be more readable by handling markdown-like formatting."""
    # Convert **bold** to HTML-like tags for frontend
    text = text.replace("**", "<strong>", 1).replace("**", "</strong>", 1)
    
    # Handle bullet points and lists
    lines = text.split('\n')
    formatted_lines = []
    
    for line in lines:
        line = line.strip()
        if line.startswith('- ') or line.startswith('• '):
            # Convert to structured list items
            formatted_lines.append(f"• {line[2:]}")
        elif line.startswith('#'):
            # Handle headers
            header_level = len(line) - len(line.lstrip('#'))
            header_text = line.lstrip('# ').strip()
            formatted_lines.append(f"\n{'=' * min(header_level * 2, 8)} {header_text} {'=' * min(header_level * 2, 8)}\n")
        elif line == '':
            formatted_lines.append('')
        else:
            formatted_lines.append(line)
    
    return '\n'.join(formatted_lines)

@app.get("/api/health")
async def api_health():
    """API health check."""
    return {"status": "ok", "proxy": "financial_advisor_cors"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8001))
    host = os.getenv("HOST", "0.0.0.0")
    
    print(f"Starting CORS Proxy server on {host}:{port}")
    print("Proxying to:", BACKEND_URL)
    
    uvicorn.run(
        "cors-proxy:app",
        host=host,
        port=port,
        reload=False
    ) 