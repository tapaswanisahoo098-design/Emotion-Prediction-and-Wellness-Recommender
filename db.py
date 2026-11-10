"""
db.py — SQLite storage for the Emotion Detector & Wellness Recommender.

Two tables:
  users     -> one row per person (name, email and/or phone, hashed password)
  analyses  -> every emotion analysis, linked to a user with user_id

Why SQLite: it ships with Python (no install, no server). Every function here takes
and returns plain Python types, so if you later move to PostgreSQL / Supabase / MySQL,
only this file needs to change — app.py stays the same.
"""

import hashlib
import hmac
import json
import os
import re
import secrets
import sqlite3
from contextlib import closing
from datetime import datetime, timedelta, timezone

# Where the database file lives. Override with DB_PATH in your .env if you want.
DB_PATH = os.getenv("DB_PATH", "emotion_app.db")

PBKDF2_ITERATIONS = 600_000   # how slow (and therefore hard to crack) password hashing is
MAX_FAILED_LOGINS = 5         # wrong passwords allowed in a row ...
LOCK_MINUTES = 5              # ... before the account is locked for a few minutes
MIN_PASSWORD_LENGTH = 8

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # lets us read columns by name
    return conn


def _now():
    return datetime.now(timezone.utc)


# ════════════════════════════════════════════════════════════════════════════
# Setup
# ════════════════════════════════════════════════════════════════════════════
def init_db():
    """Create the tables on first run. Safe to call every time the app starts."""
    with closing(_connect()) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                name            TEXT    NOT NULL,
                email           TEXT    UNIQUE,      -- lower-case; may be empty if phone is given
                phone           TEXT    UNIQUE,      -- digits only; may be empty if email is given
                password_hash   TEXT    NOT NULL,    -- never the real password
                created_at      TEXT    NOT NULL,
                failed_attempts INTEGER NOT NULL DEFAULT 0,
                locked_until    TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS analyses (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at      TEXT    NOT NULL,   -- UTC, ISO format
                user_name       TEXT    NOT NULL,
                user_text       TEXT    NOT NULL,   -- what the user wrote / said
                emotion         TEXT    NOT NULL,   -- top emotion label
                score           REAL    NOT NULL,   -- confidence of top emotion
                all_scores      TEXT    NOT NULL,   -- JSON: every emotion's score
                message         TEXT,               -- recommendation message
                activities      TEXT,               -- JSON list
                quote           TEXT,
                mood_keyword    TEXT,
                language        TEXT,               -- language the user used
                english_text    TEXT,               -- English version of what they said
                user_id         INTEGER             -- who this belongs to (users.id)
            )
            """
        )
        # If you ran an older version of the app, add the columns that are missing
        existing = {row["name"] for row in conn.execute("PRAGMA table_info(analyses)")}
        for column, kind in (("language", "TEXT"), ("english_text", "TEXT"), ("user_id", "INTEGER")):
            if column not in existing:
                conn.execute(f"ALTER TABLE analyses ADD COLUMN {column} {kind}")

        conn.execute("CREATE INDEX IF NOT EXISTS idx_analyses_user ON analyses (user_id, id)")
        conn.commit()


# ════════════════════════════════════════════════════════════════════════════
# Passwords  (we never store the real password — only a salted, slow hash)
# ════════════════════════════════════════════════════════════════════════════
def _hash_password(password):
    salt = secrets.token_bytes(16)   # random salt: two people with the same password get different hashes
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}"


def _verify_password(password, stored):
    try:
        _scheme, iterations, salt_hex, digest_hex = stored.split("$")
        candidate = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), int(iterations)
        )
        return hmac.compare_digest(candidate.hex(), digest_hex)   # constant-time comparison
    except Exception:
        return False


_dummy_hash = None


def _burn_time():
    """When the account doesn't exist we still do the slow hashing, so an attacker can't
    tell 'no such account' from 'wrong password' by measuring the response time."""
    global _dummy_hash
    if _dummy_hash is None:
        _dummy_hash = _hash_password("not-a-real-password")
    _verify_password("wrong", _dummy_hash)


# ════════════════════════════════════════════════════════════════════════════
# Accounts
# ════════════════════════════════════════════════════════════════════════════
def normalize_email(value):
    return (value or "").strip().lower()


def normalize_phone(value):
    """Keep digits only, and drop +91 / leading 0 so '+91 98765 43210' == '09876543210' == '9876543210'."""
    digits = re.sub(r"\D", "", value or "")
    if len(digits) == 12 and digits.startswith("91"):
        digits = digits[2:]
    elif len(digits) == 11 and digits.startswith("0"):
        digits = digits[1:]
    return digits


def _user_dict(row):
    return {"id": row["id"], "name": row["name"], "email": row["email"], "phone": row["phone"]}

 
def get_user(user_id):
    """The account with this id as a dict, or None if it doesn't exist (used to check saved logins)."""
    with closing(_connect()) as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return _user_dict(row) if row else None
 
def create_user(name, email, phone, password):
    """
    Register a new person. Returns (user_dict, None) on success, or (None, "error message").
    A person must give at least an email OR a phone number; each can belong to only one account.
    """
    name = " ".join((name or "").split())
    email = normalize_email(email)
    phone = normalize_phone(phone)

    if len(name) < 2:
        return None, "Please enter your name."
    if len(name) > 60:
        return None, "That name is too long (60 letters at most)."
    if not email and not phone:
        return None, "Please enter an email or a phone number (or both)."
    if email and not _EMAIL_RE.match(email):
        return None, "That email doesn't look right. Please check it."
    if phone and not (10 <= len(phone) <= 15):
        return None, "That phone number doesn't look right. Please enter a 10-digit number."
    if len(password or "") < MIN_PASSWORD_LENGTH:
        return None, f"Please choose a password with at least {MIN_PASSWORD_LENGTH} characters."
    if len(password) > 128:
        return None, "That password is too long (128 characters at most)."

    with closing(_connect()) as conn:
        if email and conn.execute("SELECT 1 FROM users WHERE email = ?", (email,)).fetchone():
            return None, "This email is already registered. Please log in instead."
        if phone and conn.execute("SELECT 1 FROM users WHERE phone = ?", (phone,)).fetchone():
            return None, "This phone number is already registered. Please log in instead."
        try:
            cur = conn.execute(
                "INSERT INTO users (name, email, phone, password_hash, created_at) VALUES (?, ?, ?, ?, ?)",
                (name, email or None, phone or None, _hash_password(password),
                 _now().isoformat(timespec="seconds")),
            )
            conn.commit()
        except sqlite3.IntegrityError:   # two people signing up at the exact same moment
            return None, "This email or phone number is already registered. Please log in instead."
        row = conn.execute("SELECT * FROM users WHERE id = ?", (cur.lastrowid,)).fetchone()
    return _user_dict(row), None


def authenticate(identifier, password):
    """
    Log in with an email OR a phone number + password.
    Returns (user_dict, None) on success, or (None, "error message").
    After MAX_FAILED_LOGINS wrong passwords the account is locked for LOCK_MINUTES minutes.
    """
    identifier = (identifier or "").strip()
    wrong = "Email/phone or password is not correct."
    if not identifier or not password:
        return None, "Please enter your email or phone number and your password."

    with closing(_connect()) as conn:
        if "@" in identifier:
            row = conn.execute("SELECT * FROM users WHERE email = ?", (normalize_email(identifier),)).fetchone()
        else:
            row = conn.execute("SELECT * FROM users WHERE phone = ?", (normalize_phone(identifier),)).fetchone()

        if row is None:
            _burn_time()
            return None, wrong

        # Locked because of too many wrong attempts?
        if row["locked_until"]:
            locked_until = datetime.fromisoformat(row["locked_until"])
            if locked_until > _now():
                minutes = int((locked_until - _now()).total_seconds() // 60) + 1
                return None, f"Too many wrong attempts. Please try again in {minutes} minute(s)."

        if _verify_password(password, row["password_hash"]):
            conn.execute("UPDATE users SET failed_attempts = 0, locked_until = NULL WHERE id = ?", (row["id"],))
            conn.commit()
            return _user_dict(row), None

        failed = row["failed_attempts"] + 1
        if failed >= MAX_FAILED_LOGINS:
            until = (_now() + timedelta(minutes=LOCK_MINUTES)).isoformat(timespec="seconds")
            conn.execute("UPDATE users SET failed_attempts = 0, locked_until = ? WHERE id = ?", (until, row["id"]))
            conn.commit()
            return None, f"Too many wrong attempts. Please try again in {LOCK_MINUTES} minutes."
        conn.execute("UPDATE users SET failed_attempts = ? WHERE id = ?", (failed, row["id"]))
        conn.commit()
        return None, wrong


# ════════════════════════════════════════════════════════════════════════════
# History  (every query is filtered by user_id, so nobody can read another person's entries)
# ════════════════════════════════════════════════════════════════════════════
def save_analysis(user_id, user_name, user_text, emotion, score, all_scores,
                  recommendation, mood_keyword=None, language=None, english_text=None):
    """Insert one analysis for this user. `recommendation` is the dict with message/activities/quote."""
    recommendation = recommendation or {}
    with closing(_connect()) as conn:
        conn.execute(
            """
            INSERT INTO analyses
                (created_at, user_name, user_text, emotion, score, all_scores,
                 message, activities, quote, mood_keyword, language, english_text, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                _now().isoformat(timespec="seconds"),
                user_name,
                user_text,
                emotion,
                float(score),
                json.dumps(all_scores),
                recommendation.get("message"),
                json.dumps(recommendation.get("activities", [])),
                recommendation.get("quote"),
                mood_keyword,
                language,
                english_text,
                user_id,
            ),
        )
        conn.commit()


def _entry_dict(row):
    item = dict(row)
    item["all_scores"] = json.loads(item["all_scores"] or "{}")
    item["activities"] = json.loads(item["activities"] or "[]")
    return item


def get_history(user_id, limit=50):
    """This user's entries, newest first, as a list of dicts."""
    with closing(_connect()) as conn:
        rows = conn.execute(
            "SELECT * FROM analyses WHERE user_id = ? ORDER BY id DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
    return [_entry_dict(r) for r in rows]


def get_entry(user_id, entry_id):
    """One entry — but only if it belongs to this user. Returns None otherwise."""
    with closing(_connect()) as conn:
        row = conn.execute(
            "SELECT * FROM analyses WHERE id = ? AND user_id = ?", (entry_id, user_id)
        ).fetchone()
    return _entry_dict(row) if row else None


def delete_entry(user_id, entry_id):
    with closing(_connect()) as conn:
        conn.execute("DELETE FROM analyses WHERE id = ? AND user_id = ?", (entry_id, user_id))
        conn.commit()


def delete_history(user_id):
    """Permanently delete every entry of this user."""
    with closing(_connect()) as conn:
        conn.execute("DELETE FROM analyses WHERE user_id = ?", (user_id,))
        conn.commit()
