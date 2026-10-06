from __future__ import annotations

import os
import sqlite3
from pathlib import Path


_DB_PATH = Path(__file__).parent.parent.parent / "data" / "latissa.db"


def _get_conn() -> sqlite3.Connection:
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(_DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with _get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                user_message TEXT NOT NULL,
                bot_response TEXT NOT NULL,
                intent TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS inquiries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                name TEXT,
                email TEXT,
                phone TEXT,
                message TEXT NOT NULL,
                status TEXT DEFAULT 'new',
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        conn.commit()


def log_conversation(session_id: str, user_message: str, bot_response: str, intent: str = "info_query"):
    try:
        with _get_conn() as conn:
            conn.execute(
                "INSERT INTO conversations (session_id, user_message, bot_response, intent) VALUES (?, ?, ?, ?)",
                (session_id, user_message, bot_response, intent),
            )
            conn.commit()
    except Exception as e:
        print(f"[db] log_conversation error: {e}")


def save_inquiry(session_id: str, name: str, email: str, phone: str, message: str) -> int | None:
    try:
        with _get_conn() as conn:
            cur = conn.execute(
                "INSERT INTO inquiries (session_id, name, email, phone, message) VALUES (?, ?, ?, ?, ?)",
                (session_id, name, email, phone, message),
            )
            conn.commit()
            return cur.lastrowid
    except Exception as e:
        print(f"[db] save_inquiry error: {e}")
        return None


def get_conversations(limit: int = 100) -> list[dict]:
    try:
        with _get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM conversations ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
            return [dict(r) for r in rows]
    except Exception:
        return []


def get_inquiries(limit: int = 100) -> list[dict]:
    try:
        with _get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM inquiries ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
            return [dict(r) for r in rows]
    except Exception:
        return []
