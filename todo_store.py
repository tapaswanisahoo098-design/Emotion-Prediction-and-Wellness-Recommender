"""Tiny storage for each person's to-do list (kept in todos.db next to app.py)."""
import sqlite3
from pathlib import Path

_DB_PATH = Path(__file__).with_name("todos.db")


def _connect():
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute(
        "CREATE TABLE IF NOT EXISTS todos ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL, "
        "text TEXT NOT NULL, done INTEGER NOT NULL DEFAULT 0, created_at TEXT DEFAULT CURRENT_TIMESTAMP)"
    )
    return conn


def list_todos(user_id):
    with _connect() as conn:
        rows = conn.execute(
            "SELECT id, text, done FROM todos WHERE user_id = ? ORDER BY done, id", (str(user_id),)
        ).fetchall()
    return [dict(r) for r in rows]


def add_todo(user_id, text):
    text = " ".join((text or "").split())[:200]
    if not text:
        return
    with _connect() as conn:
        conn.execute("INSERT INTO todos (user_id, text) VALUES (?, ?)", (str(user_id), text))


def set_done(user_id, todo_id, done):
    with _connect() as conn:
        conn.execute("UPDATE todos SET done = ? WHERE id = ? AND user_id = ?",
                     (1 if done else 0, todo_id, str(user_id)))


def delete_todo(user_id, todo_id):
    with _connect() as conn:
        conn.execute("DELETE FROM todos WHERE id = ? AND user_id = ?", (todo_id, str(user_id)))


def clear_done(user_id):
    with _connect() as conn:
        conn.execute("DELETE FROM todos WHERE user_id = ? AND done = 1", (str(user_id),))
