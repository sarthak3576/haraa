import hashlib
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "waste_mgmt.db"


def _init_users_table():
    with sqlite3.connect(DB_PATH, timeout=10.0) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS local_users (
                email TEXT PRIMARY KEY,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def save_local_user(email: str, password: str) -> None:
    _init_users_table()
    with sqlite3.connect(DB_PATH, timeout=10.0) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO local_users (email, password_hash) VALUES (?, ?)",
            (email.strip().lower(), _hash_password(password)),
        )


def verify_local_user(email: str, password: str) -> bool:
    _init_users_table()
    with sqlite3.connect(DB_PATH, timeout=10.0) as conn:
        cursor = conn.execute(
            "SELECT password_hash FROM local_users WHERE email = ?",
            (email.strip().lower(),),
        )
        row = cursor.fetchone()
        if not row:
            return False
        return row[0] == _hash_password(password)
