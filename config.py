import os
from pathlib import Path

# Load environment variables if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = os.getenv("DATABASE_PATH", str(BASE_DIR / "database" / "chatbot.db"))

# Local AI Engine Configuration
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "nova-general")
PORT = int(os.getenv("PORT", 5000))
DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1", "t")

DEFAULT_SYSTEM_PROMPT = """You are Nova, an intelligent, helpful, and concise local AI assistant. 
You provide clear, accurate, and nicely formatted answers using Markdown. 
When writing code, always provide code blocks with language identifiers."""
