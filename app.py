"""
Entry point for running the Nova AI Chatbot application.
Powered by FastAPI and Uvicorn.
"""
import uvicorn
from config import PORT, DEBUG
from main import app

if __name__ == "__main__":
    print(f"🚀 Starting Nova AI on http://127.0.0.1:{PORT}")
    print(f"📖 Interactive Swagger API docs: http://127.0.0.1:{PORT}/docs")
    uvicorn.run("main:app", host="127.0.0.1", port=PORT, reload=DEBUG)
