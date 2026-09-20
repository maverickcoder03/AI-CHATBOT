# Nova AI — 100% Local Asynchronous AI Chatbot (FastAPI)

Nova AI is a high-performance, **100% local, self-contained** conversational AI application powered by **FastAPI**, **Uvicorn**, **Server-Sent Events (SSE) streaming**, **multi-turn context memory**, **SQLite session persistence**, and a **modern glassmorphic interface**.

> 🔒 **Zero External API Dependencies**: This application runs entirely on your local machine with zero external cloud API keys, zero internet dependencies, and no paid subscriptions.

---

## ✨ Features

- ⚡ **FastAPI & Uvicorn Asynchronous Core**: High-throughput, non-blocking ASGI web server.
- 🌊 **Real-Time Token Streaming**: Low-latency token delivery via Server-Sent Events with smooth typewriter rendering.
- 🧠 **Multi-Turn Context Memory**: Retains conversation history across turns so follow-up questions remain coherent.
- 📂 **Multi-Session Management**: Create, rename, search, switch, and delete chat threads saved locally in SQLite.
- 📖 **Interactive Swagger Documentation**: Built-in interactive API playground at `/docs` and `/redoc`.
- 🤖 **Local AI Personas**:
  - **Nova General Assistant**: All-around conversational assistant.
  - **Nova Code & Tech Specialist**: Programming, syntax guidance, and API architecture.
  - **Nova Math & Logic Engine**: Math expressions and arithmetic evaluations.
  - **Nova Creative & Brainstormer**: Startup concepts, ideas, and writing assistance.
- 🎨 **Glassmorphic UI / UX**:
  - Dark & Light mode toggle with persistent state
  - Responsive mobile-friendly layout with collapsible sidebar
  - Markdown formatting, tables, lists, and blockquotes
  - Syntax-highlighted code blocks with 1-click **"Copy Code"** buttons
  - Quick-start suggestion cards for instant exploration
- 🎤 **Voice Interaction**:
  - **Speech-to-Text (STT)**: Voice message dictation via Web Speech API
  - **Text-to-Speech (TTS)**: Voice read-out of AI responses
- 💾 **Export Chats**: Download any conversation as formatted Markdown (`.md`) or JSON.

---

## 🚀 Quick Start

### 1. Install Lightweight Web Dependencies
```bash
python -m pip install -r requirements.txt
```

### 2. Run the Application
You can start the server with either:
```bash
python app.py
```
*or using Uvicorn directly:*
```bash
uvicorn main:app --reload --port 5000
```

Open your browser and navigate to:
- **Web Chat App:** [http://127.0.0.1:5000](http://127.0.0.1:5000)
- **Interactive Swagger API Docs:** [http://127.0.0.1:5000/docs](http://127.0.0.1:5000/docs)

---

## 📁 Project Structure

```
AI-CHATBOT-main/
├── main.py                # FastAPI asynchronous server & SSE streaming routes
├── app.py                 # Application launcher with Uvicorn
├── chatbot.py             # 100% Local AI engine & streaming generator
├── database.py            # SQLite database with sessions & message history
├── config.py              # Centralized environment & settings configuration
├── requirements.txt       # Lightweight dependencies (FastAPI, Uvicorn, Jinja2, etc.)
├── .env.example           # Environment template
├── README.md              # Project documentation
├── database/              # SQLite database storage (auto-created)
│   └── chatbot.db
├── static/
│   ├── css/
│   │   └── style.css      # Dark/Light glassmorphism design system
│   └── js/
│       └── app.js         # Frontend streaming, sessions, STT/TTS & markdown logic
└── templates/
    └── index.html         # Main web application interface
```

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Serves the interactive web UI |
| `GET` | `/docs` | Interactive Swagger API documentation & testing |
| `GET` | `/api/models` | Lists local AI personas and capabilities |
| `GET` | `/api/sessions` | Lists all chat sessions |
| `POST` | `/api/sessions` | Creates a new chat session |
| `GET` | `/api/sessions/{id}` | Retrieves message history for a session |
| `DELETE` | `/api/sessions/{id}` | Deletes a chat session |
| `POST` | `/api/sessions/{id}/rename` | Renames a chat session title |
| `POST` | `/api/chat/stream` | Server-Sent Events (SSE) token streaming endpoint |
| `POST` | `/api/chat` | Non-streaming JSON fallback chat endpoint |
| `POST` | `/api/clear` | Clears all stored conversations |
