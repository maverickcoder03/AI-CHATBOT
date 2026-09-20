import os
import sqlite3
import uuid
from typing import List, Dict, Optional
from config import DATABASE_PATH

def _ensure_dir():
    db_dir = os.path.dirname(os.path.abspath(DATABASE_PATH))
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

def get_connection() -> sqlite3.Connection:
    _ensure_dir()
    con = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con

def init_db():
    _ensure_dir()
    with get_connection() as con:
        con.executescript("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id);
        """)

def create_session(session_id: Optional[str] = None, title: str = "New Conversation") -> str:
    sid = session_id or str(uuid.uuid4())
    with get_connection() as con:
        con.execute(
            "INSERT OR IGNORE INTO sessions (id, title, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)",
            (sid, title)
        )
    return sid

def get_sessions() -> List[Dict]:
    with get_connection() as con:
        cur = con.execute("""
            SELECT s.id, s.title, s.created_at, s.updated_at,
                   COUNT(m.id) as message_count
            FROM sessions s
            LEFT JOIN messages m ON s.id = m.session_id
            GROUP BY s.id
            ORDER BY s.updated_at DESC
        """)
        return [dict(row) for row in cur.fetchall()]

def get_session(session_id: str) -> Optional[Dict]:
    with get_connection() as con:
        cur = con.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
        row = cur.fetchone()
        return dict(row) if row else None

def get_session_messages(session_id: str) -> List[Dict]:
    with get_connection() as con:
        cur = con.execute(
            "SELECT id, session_id, role, content, created_at FROM messages WHERE session_id = ? ORDER BY id ASC",
            (session_id,)
        )
        return [dict(row) for row in cur.fetchall()]

def save_message(session_id: str, role: str, content: str) -> int:
    create_session(session_id=session_id)
    with get_connection() as con:
        cur = con.execute(
            "INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)",
            (session_id, role, content)
        )
        con.execute(
            "UPDATE sessions SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (session_id,)
        )
        return cur.lastrowid

def update_session_title(session_id: str, title: str) -> bool:
    with get_connection() as con:
        cur = con.execute(
            "UPDATE sessions SET title = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (title, session_id)
        )
        return cur.rowcount > 0

def delete_session(session_id: str) -> bool:
    with get_connection() as con:
        cur = con.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        return cur.rowcount > 0

def clear_all_data():
    with get_connection() as con:
        con.execute("DELETE FROM messages")
        con.execute("DELETE FROM sessions")
