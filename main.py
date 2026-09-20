import json
import asyncio
from typing import Optional, List, Dict
from pathlib import Path

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import PORT, DEBUG, DEFAULT_MODEL, DEFAULT_SYSTEM_PROMPT
from database import (
    init_db,
    create_session,
    get_sessions,
    get_session,
    get_session_messages,
    save_message,
    delete_session,
    update_session_title,
    clear_all_data
)
from chatbot import (
    stream_chat_response,
    get_response,
    get_available_models
)

# Initialize database schema
init_db()

# Initialize FastAPI Application
app = FastAPI(
    title="Nova AI Chatbot API",
    description="High-performance asynchronous streaming AI chatbot powered by FastAPI.",
    version="2.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent

# Mount Static Files & Templates
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# --- Pydantic Request Models ---
class CreateSessionRequest(BaseModel):
    title: Optional[str] = "New Conversation"

class RenameSessionRequest(BaseModel):
    title: str

class ChatStreamRequest(BaseModel):
    session_id: Optional[str] = None
    message: str
    model: Optional[str] = DEFAULT_MODEL
    system_prompt: Optional[str] = DEFAULT_SYSTEM_PROMPT

class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str
    model: Optional[str] = DEFAULT_MODEL

# --- Routes ---

@app.get("/", response_class=HTMLResponse, summary="Main Web UI")
async def home(request: Request):
    """Serve the main interactive web interface."""
    return templates.TemplateResponse(request=request, name="index.html")

@app.get("/api/models", summary="List Available AI Models")
async def get_models():
    """Retrieve available AI models and active configurations."""
    return {
        "models": get_available_models(),
        "default_model": DEFAULT_MODEL
    }

@app.get("/api/sessions", summary="List Chat Sessions")
async def list_sessions():
    """Retrieve all conversation sessions."""
    sessions = get_sessions()
    return {"sessions": sessions}

@app.post("/api/sessions", summary="Create New Session")
async def new_session(payload: Optional[CreateSessionRequest] = None):
    """Create a new chat conversation session."""
    title = payload.title if payload and payload.title else "New Conversation"
    session_id = create_session(title=title)
    return {"session_id": session_id, "title": title}

@app.get("/api/sessions/{session_id}", summary="Get Session History")
async def get_session_history(session_id: str):
    """Retrieve message history for a specific conversation session."""
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    messages = get_session_messages(session_id)
    return {"session": session, "messages": messages}

@app.delete("/api/sessions/{session_id}", summary="Delete Session")
async def remove_session(session_id: str):
    """Delete a conversation session and all its messages."""
    deleted = delete_session(session_id)
    return {"success": deleted}

@app.post("/api/sessions/{session_id}/rename", summary="Rename Session")
async def rename_session(session_id: str, payload: RenameSessionRequest):
    """Rename a conversation title."""
    clean_title = payload.title.strip()
    if not clean_title:
        raise HTTPException(status_code=400, detail="Title cannot be empty")
    updated = update_session_title(session_id, clean_title)
    return {"success": updated, "title": clean_title}

@app.post("/api/chat/stream", summary="Live SSE Token Streaming")
async def chat_stream(payload: ChatStreamRequest):
    """
    Server-Sent Events (SSE) streaming endpoint for real-time token delivery.
    """
    message = payload.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    session_id = payload.session_id
    if not session_id:
        session_id = create_session(title=message[:30] + ("..." if len(message) > 30 else ""))
    else:
        existing_msgs = get_session_messages(session_id)
        if len(existing_msgs) == 0:
            update_session_title(session_id, message[:30] + ("..." if len(message) > 30 else ""))

    # Save user message to database
    save_message(session_id, "user", message)

    # Fetch recent history for multi-turn context
    history = get_session_messages(session_id)
    formatted_context = [{"role": m["role"], "content": m["content"]} for m in history]

    async def event_generator():
        full_reply = []
        try:
            # Generate tokens synchronously/asynchronously from chatbot engine
            for token in stream_chat_response(
                messages=formatted_context,
                model=payload.model,
                system_prompt=payload.system_prompt
            ):
                full_reply.append(token)
                event_data = json.dumps({"chunk": token, "session_id": session_id})
                yield f"data: {event_data}\n\n"
                await asyncio.sleep(0.005)

            complete_text = "".join(full_reply)
            save_message(session_id, "assistant", complete_text)

            done_data = json.dumps({
                "done": True,
                "session_id": session_id,
                "full_response": complete_text
            })
            yield f"data: {done_data}\n\n"
        except Exception as e:
            err_data = json.dumps({"error": str(e), "session_id": session_id})
            yield f"data: {err_data}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@app.post("/api/chat", summary="Non-Streaming Chat Fallback")
async def chat(payload: ChatRequest):
    """Non-streaming fallback chat endpoint."""
    message = payload.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    session_id = payload.session_id or create_session(title=message[:30])
    save_message(session_id, "user", message)
    
    history = get_session_messages(session_id)
    formatted_history = [{"role": m["role"], "content": m["content"]} for m in history]

    reply = get_response(message, formatted_history[:-1])
    save_message(session_id, "assistant", reply)

    return {
        "reply": reply,
        "session_id": session_id
    }

@app.post("/api/clear", summary="Clear All Chat History")
async def clear_history():
    """Clear all chat history and sessions."""
    clear_all_data()
    return {"success": True, "message": "All conversations cleared."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=PORT, reload=DEBUG)
