"""Remember who is logged in, even after the browser page is refreshed.

How it works:
  * When someone logs in, we create a random token, save it on the server (sessions.db)
    and also in the person's browser as a cookie.
  * When the page is refreshed, Streamlit forgets everything, but the browser still sends
    the cookie, so we look the token up here and log the person back in automatically.
  * Log out deletes the token on the server and in the browser.
Only a hash of the token is stored on the server, never the token itself.
"""
import hashlib
import json
import secrets
import sqlite3
import time
from pathlib import Path

COOKIE_NAME = "emotalk_session"
SESSION_DAYS = 30
_DB_PATH = Path(__file__).with_name("sessions.db")


def _connect():
    conn = sqlite3.connect(_DB_PATH)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS sessions ("
        "token_hash TEXT PRIMARY KEY, user_json TEXT NOT NULL, expires_at REAL NOT NULL)"
    )
    return conn


def _hash(token):
    return hashlib.sha256(token.encode()).hexdigest()


def create_session(user):
    """Save a new login session for this user and return the secret token."""
    token = secrets.token_urlsafe(32)
    with _connect() as conn:
        conn.execute("DELETE FROM sessions WHERE expires_at < ?", (time.time(),))   # tidy up old ones
        conn.execute(
            "INSERT INTO sessions VALUES (?, ?, ?)",
            (_hash(token), json.dumps(dict(user), default=str),
             time.time() + SESSION_DAYS * 86400),
        )
    return token


def get_user(token):
    """Return the user for this token, or None if it is missing / expired / unknown."""
    if not token:
        return None
    with _connect() as conn:
        row = conn.execute(
            "SELECT user_json, expires_at FROM sessions WHERE token_hash = ?", (_hash(token),)
        ).fetchone()
    if not row or row[1] < time.time():
        return None
    return json.loads(row[0])


def delete_session(token):
    if not token:
        return
    with _connect() as conn:
        conn.execute("DELETE FROM sessions WHERE token_hash = ?", (_hash(token),))
