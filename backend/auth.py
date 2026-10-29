"""
Authentication for the Legal Intelligence System API.

Passwords are hashed with bcrypt. Sessions are a small, stdlib-only
signed token (HMAC-SHA256 over a payload, no external JWT library
needed): the frontend stores it and sends it back as
`Authorization: Bearer <token>` on every request.
"""

import base64
import hashlib
import hmac
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import bcrypt
from dotenv import load_dotenv
from fastapi import Header, HTTPException

from .database import get_connection


PROJECT_ROOT = Path(__file__).resolve().parent.parent

load_dotenv(PROJECT_ROOT / ".env")

SECRET_KEY = os.getenv("AUTH_SECRET_KEY")

if not SECRET_KEY:
    raise RuntimeError(
        "AUTH_SECRET_KEY not found.\n"
        "Make sure it is present in the .env file."
    )

TOKEN_TTL_SECONDS = 7 * 24 * 60 * 60  # 7 days


# ============================================================
# SCHEMA
# ============================================================

def init_users_table():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            name TEXT,
            created_at TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


# ============================================================
# USERS
# ============================================================

def get_user_by_email(email: str):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, email, password_hash, name FROM users WHERE email = ?",
        (email.lower().strip(),),
    )

    row = cursor.fetchone()
    conn.close()

    return dict(row) if row else None


def create_user(email: str, password: str, name: str | None = None):

    email = email.lower().strip()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO users (email, password_hash, name, created_at)
        VALUES (?, ?, ?, ?)
        """,
        (
            email,
            hash_password(password),
            (name or "").strip() or None,
            datetime.now(timezone.utc).isoformat(),
        ),
    )

    user_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return {"id": user_id, "email": email, "name": name}


# ============================================================
# PASSWORDS
# ============================================================

def hash_password(password: str) -> str:

    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt(),
    ).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:

    try:
        return bcrypt.checkpw(
            password.encode("utf-8"),
            password_hash.encode("utf-8"),
        )
    except ValueError:
        return False


# ============================================================
# TOKENS
# ============================================================

def create_token(user_id: int, email: str) -> str:

    payload = {
        "user_id": user_id,
        "email": email,
        "exp": int(time.time()) + TOKEN_TTL_SECONDS,
    }

    payload_bytes = json.dumps(payload).encode("utf-8")
    payload_b64 = base64.urlsafe_b64encode(payload_bytes).decode("utf-8").rstrip("=")

    signature = hmac.new(
        SECRET_KEY.encode("utf-8"),
        payload_b64.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    return f"{payload_b64}.{signature}"


def verify_token(token: str):
    """Returns the decoded payload dict, or None if invalid/expired."""

    try:
        payload_b64, signature = token.split(".", 1)
    except ValueError:
        return None

    expected_signature = hmac.new(
        SECRET_KEY.encode("utf-8"),
        payload_b64.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(signature, expected_signature):
        return None

    try:
        padded = payload_b64 + "=" * (-len(payload_b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded))
    except (ValueError, json.JSONDecodeError):
        return None

    if payload.get("exp", 0) < time.time():
        return None

    return payload


# ============================================================
# FASTAPI DEPENDENCY
# ============================================================

def get_current_user(authorization: str | None = Header(default=None)):

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = authorization.removeprefix("Bearer ").strip()
    payload = verify_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired session")

    return {"user_id": payload["user_id"], "email": payload["email"]}
