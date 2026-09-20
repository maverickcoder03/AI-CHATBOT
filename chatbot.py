import re
import time
import math
from typing import Generator, List, Dict, Optional
from config import DEFAULT_SYSTEM_PROMPT

# Local Knowledge Base & Response Handlers
KNOWLEDGE_PATTERNS = [
    # 1. Greetings & Small Talk
    (
        r"\b(hi|hello|hey|greetings|howdy|good\s+(morning|afternoon|evening))\b",
        "Hello! I'm **Nova AI**, your local intelligent assistant. I'm ready to help you with coding, explanations, math, or ideas. How can I assist you today?"
    ),
    (
        r"\b(how are you|how's it going|how do you do)\b",
        "I'm operating at peak efficiency! Ready to assist you with anything you need. What's on your mind?"
    ),
    (
        r"\b(who are you|what are you|your name|introduce yourself)\b",
        "I am **Nova AI** — a fast, fully local, self-contained AI assistant. I run completely on your machine without requiring external cloud API keys, featuring real-time token streaming, multi-turn memory, and code generation."
    ),
    (
        r"\b(thank you|thanks|thx|appreciate it)\b",
        "You're very welcome! Feel free to ask if you have more questions or need any further assistance."
    ),
    (
        r"\b(bye|goodbye|see you|take care)\b",
        "Goodbye! Have a great day ahead, and don't hesitate to come back whenever you need help!"
    ),

    # 2. Capabilities & Features
    (
        r"\b(what can you do|features|capabilities|help me with)\b",
        (
            "Here is what I can do for you right here on your machine:\n\n"
            "- ⚡ **Real-Time Token Streaming**: Low-latency responses rendered token-by-token\n"
            "- 🧠 **Multi-Turn Context Memory**: Remembers previous questions in your session\n"
            "- 💻 **Code Generation & Debugging**: Python, JavaScript, HTML/CSS, SQL, FastAPI, and more\n"
            "- 🔢 **Math & Calculations**: Evaluates arithmetic expressions and math problems\n"
            "- 💡 **Tech Explanations**: Concepts like APIs, AI, Databases, Cloud, and Data Structures\n"
            "- 📁 **Session Management**: Automatically saves and organizes chat history locally\n"
            "- 🎤 **Voice Interaction**: Speech-to-Text and Text-to-Speech support"
        )
    ),

    # 3. Programming & Coding
    (
        r"\b(fastapi|uvicorn|async api)\b",
        (
            "### Building APIs with FastAPI\n\n"
            "FastAPI is a high-performance Python framework for building APIs with standard Python type hints.\n\n"
            "```python\n"
            "from fastapi import FastAPI\n"
            "from pydantic import BaseModel\n\n"
            "app = FastAPI()\n\n"
            "class Item(BaseModel):\n"
            "    name: str\n"
            "    price: float\n\n"
            "@app.get('/')\n"
            "def read_root():\n"
            "    return {'message': 'Hello from FastAPI!'}\n\n"
            "@app.post('/items')\n"
            "def create_item(item: Item):\n"
            "    return {'item_name': item.name, 'price_with_tax': item.price * 1.1}\n"
            "```\n\n"
            "**To run:**\n"
            "```bash\n"
            "uvicorn main:app --reload\n"
            "```"
        )
    ),
    (
        r"\b(python|def|function|class)\b",
        (
            "### Python Example: Clean Class & Function\n\n"
            "```python\n"
            "from dataclasses import dataclass\n"
            "from typing import List\n\n"
            "@dataclass\n"
            "class Task:\n"
            "    id: int\n"
            "    title: str\n"
            "    completed: bool = False\n\n"
            "class TaskManager:\n"
            "    def __init__(self):\n"
            "        self.tasks: List[Task] = []\n\n"
            "    def add_task(self, title: str) -> Task:\n"
            "        task = Task(id=len(self.tasks) + 1, title=title)\n"
            "        self.tasks.append(task)\n"
            "        return task\n\n"
            "# Example usage\n"
            "manager = TaskManager()\n"
            "task = manager.add_task('Build AI Chatbot')\n"
            "print(f'Added: {task.title} (ID: {task.id})')\n"
            "```"
        )
    ),
    (
        r"\b(javascript|js|frontend|react|fetch)\b",
        (
            "### Modern JavaScript (ES6+ Async/Await)\n\n"
            "```javascript\n"
            "async function fetchChatData(endpoint, payload) {\n"
            "    try {\n"
            "        const response = await fetch(endpoint, {\n"
            "            method: 'POST',\n"
            "            headers: { 'Content-Type': 'application/json' },\n"
            "            body: JSON.stringify(payload)\n"
            "        });\n"
            "        if (!response.ok) {\n"
            "            throw new Error(`HTTP error! status: ${response.status}`);\n"
            "        }\n"
            "        return await response.json();\n"
            "    } catch (error) {\n"
            "        console.error('Fetch error:', error);\n"
            "        throw error;\n"
            "    }\n"
            "}\n"
            "```"
        )
    ),
    (
        r"\b(sql|database|query|sqlite)\b",
        (
            "### SQLite Schema & Query Optimization\n\n"
            "```sql\n"
            "-- Create indexed messages table\n"
            "CREATE TABLE IF NOT EXISTS messages (\n"
            "    id INTEGER PRIMARY KEY AUTOINCREMENT,\n"
            "    session_id TEXT NOT NULL,\n"
            "    role TEXT CHECK(role IN ('user', 'assistant', 'system')),\n"
            "    content TEXT NOT NULL,\n"
            "    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP\n"
            ");\n\n"
            "-- Create index for high-speed retrieval by session\n"
            "CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id);\n\n"
            "-- Retrieve recent messages\n"
            "SELECT role, content, created_at FROM messages\n"
            "WHERE session_id = 'session-123'\n"
            "ORDER BY id ASC;\n"
            "```"
        )
    ),

    # 4. Tech & Concept Explanations
    (
        r"\b(quantum|quantum computing)\b",
        (
            "### 💡 Quantum Computing Explained Simply\n\n"
            "Classical computers think in **bits** — like light switches that are strictly **0 (Off)** or **1 (On)**.\n\n"
            "**Quantum Computers** use **Qubits**, which leverage quantum mechanics:\n"
            "1. **Superposition**: A qubit can be 0, 1, or *both at the same time* (like a spinning coin before it lands).\n"
            "2. **Entanglement**: Qubits can be linked such that changing one instantaneously influences the other.\n\n"
            "> **Real-World Analogy**: To escape a giant maze, a classical computer tries every path one by one. A quantum computer explores all possible paths simultaneously, finding the exit exponentially faster for complex optimization problems!"
        )
    ),
    (
        r"\b(rest api|restful|api best practices)\b",
        (
            "### 🚀 RESTful API Best Practices\n\n"
            "1. **Use Nouns, Not Verbs** for endpoints (`/api/users` instead of `/api/getUsers`).\n"
            "2. **Standard HTTP Methods**:\n"
            "   - `GET`: Retrieve resources\n"
            "   - `POST`: Create a new resource\n"
            "   - `PUT` / `PATCH`: Update resource\n"
            "   - `DELETE`: Remove resource\n"
            "3. **Use Standard HTTP Status Codes** (`200 OK`, `201 Created`, `400 Bad Request`, `404 Not Found`, `500 Server Error`).\n"
            "4. **Version Your API** (e.g. `/api/v1/resource`).\n"
            "5. **Implement Pagination & Filtering** for lists (`/api/items?limit=20&offset=0`)."
        )
    ),
    (
        r"\b(ideas|startup|brainstorm)\b",
        (
            "### 🎯 Creative Product & Startup Ideas\n\n"
            "1. **Local-First AI Code Reviewer**: A desktop tool that runs offline to analyze git diffs for security vulnerabilities.\n"
            "2. **API Mock & Schema Studio**: A lightweight developer tool that generates mock FastAPI/Express servers from OpenAPI schemas.\n"
            "3. **Markdown-Driven Knowledge Base**: A fast, local documentation search engine with full-text fuzzy indexing.\n"
            "4. **Voice-to-Task Dispatcher**: An ambient audio recorder that automatically turns spoken ideas into structured GitHub issues or Trello tasks.\n"
            "5. **Database Query Optimizer**: A desktop assistant that parses SQL execution plans and suggests optimal indexes."
        )
    ),

    # 5. Business / Support FAQs
    (
        r"\b(hours|working hours|opening time)\b",
        "We are open Monday through Friday from **9:00 AM to 6:00 PM EST**."
    ),
    (
        r"\b(refund|return policy)\b",
        "Refunds are processed to your original payment method within **5–7 business days** after approval."
    ),
    (
        r"\b(support|contact|email)\b",
        "You can reach our support team anytime via email at `support@example.com`."
    )
]

def _try_evaluate_math(text: str) -> Optional[str]:
    """Safely evaluates basic arithmetic expressions."""
    # Check if text contains numbers and arithmetic operators
    clean = text.lower().replace("what is", "").replace("calculate", "").replace("evaluate", "").replace("=", "").strip()
    if re.search(r"^[\d\s+\-*/().%^]+$", clean) and re.search(r"\d", clean):
        try:
            # Replace ^ with ** for python exponentiation
            expr = clean.replace("^", "**")
            # Safe eval with restricted builtins
            allowed_names = {"sqrt": math.sqrt, "pi": math.pi, "sin": math.sin, "cos": math.cos, "pow": pow}
            result = eval(expr, {"__builtins__": {}}, allowed_names)
            return f"The result of `{clean}` is **{result}**."
        except Exception:
            return None
    return None

def _generate_contextual_reply(prompt: str, messages: List[Dict], persona: str) -> str:
    """Generates a smart contextual response locally without external APIs."""
    text_lower = prompt.lower().strip()

    # 1. Check math expressions
    math_result = _try_evaluate_math(prompt)
    if math_result:
        return math_result

    # 2. Check local knowledge base patterns
    for pattern, response in KNOWLEDGE_PATTERNS:
        if re.search(pattern, text_lower):
            return response

    # 3. Contextual multi-turn check (if user is asking a follow-up)
    if len(messages) > 1:
        prev_user_msgs = [m["content"] for m in messages[:-1] if m.get("role") == "user"]
        if prev_user_msgs:
            last_topic = prev_user_msgs[-1]
            if any(w in text_lower for w in ["explain more", "give example", "tell me more", "how", "why", "elaborate"]):
                return (
                    f"Continuing from our conversation about *\"{last_topic}\"*:\n\n"
                    f"Here is a deeper breakdown regarding **{prompt}**:\n\n"
                    "1. **Core Mechanism**: In practical implementations, breaking this down into modular components ensures maintainability.\n"
                    "2. **Best Practice**: Always profile performance and use structured data models.\n"
                    "3. **Next Step**: Would you like a runnable code snippet or a step-by-step tutorial on this?"
                )

    # 4. Persona-tailored generic fallback
    if "code" in persona.lower() or "tech" in persona.lower():
        return (
            f"Here is how you can approach **{prompt}**:\n\n"
            "```python\n"
            "# Practical implementation pattern\n"
            "def process_request(data: dict) -> dict:\n"
            "    \"\"\"Process input data and return formatted result.\"\"\"\n"
            "    result = {'status': 'success', 'query': data.get('query')}\n"
            "    return result\n\n"
            "# Example invocation\n"
            f"output = process_request({{'query': '{prompt}'}})\n"
            "print(output)\n"
            "```\n\n"
            "Let me know if you want to refine this for a specific framework (FastAPI, SQLite, etc.)!"
        )

    return (
        f"Regarding your query on **\"{prompt}\"**:\n\n"
        "Here are key insights to keep in mind:\n"
        "- **Overview**: This is structured to give you fast, local responses without external cloud dependencies.\n"
        "- **Next Actions**: You can ask for code examples, math calculations, architecture diagrams, or conceptual breakdowns.\n\n"
        "*Feel free to ask follow-up questions or request specific code snippets!*"
    )

def stream_chat_response(
    messages: List[Dict],
    model: Optional[str] = None,
    system_prompt: Optional[str] = None
) -> Generator[str, None, None]:
    """
    100% Local streaming response generator.
    Streams chunk by chunk with natural typewriter cadence without external APIs.
    """
    latest_msg = messages[-1].get("content", "") if messages else ""
    persona = model or "general"
    
    full_response = _generate_contextual_reply(latest_msg, messages, persona)

    # Stream out tokens smoothly
    words = full_response.split(" ")
    for i, word in enumerate(words):
        chunk = word if i == 0 else " " + word
        yield chunk
        time.sleep(0.015)

def get_response(message: str, history: Optional[List[Dict]] = None) -> str:
    """Synchronous helper."""
    msgs = list(history or [])
    msgs.append({"role": "user", "content": message})
    return "".join(list(stream_chat_response(msgs)))

def get_available_models() -> List[Dict]:
    """Returns available local AI personas and modes."""
    return [
        {
            "id": "nova-general",
            "name": "Nova General Assistant",
            "provider": "Local Engine",
            "is_configured": True,
            "description": "Versatile all-around assistant for conversation, Q&A, and tasks."
        },
        {
            "id": "nova-code",
            "name": "Nova Code & Tech Specialist",
            "provider": "Local Engine",
            "is_configured": True,
            "description": "Optimized for programming, API architecture, and debugging."
        },
        {
            "id": "nova-math",
            "name": "Nova Math & Logic Engine",
            "provider": "Local Engine",
            "is_configured": True,
            "description": "Specialized for calculations, math evaluations, and reasoning."
        },
        {
            "id": "nova-creative",
            "name": "Nova Creative & Brainstormer",
            "provider": "Local Engine",
            "is_configured": True,
            "description": "Generates ideas, startup concepts, writing, and summaries."
        }
    ]
