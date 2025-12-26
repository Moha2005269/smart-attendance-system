from __future__ import annotations

import base64
import hashlib
import hmac
import os
import sqlite3
from pathlib import Path
from typing import Any, Optional

DB_DEFAULT = "database/attendance.db"


def _connect(db_path: str = DB_DEFAULT) -> sqlite3.Connection:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path: str = DB_DEFAULT) -> None:
    with _connect(db_path) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                snapshot_path TEXT,
                confidence REAL,
                liveness_ok INTEGER DEFAULT 0,
                FOREIGN KEY(user_id) REFERENCES users(id)
            );
            """
        )


def _hash_password(password: str, salt: bytes | None = None, rounds: int = 200_000) -> str:
    if salt is None:
        salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, rounds)
    return base64.b64encode(salt + dk).decode("utf-8")


def _verify_password(password: str, stored: str, rounds: int = 200_000) -> bool:
    try:
        raw = base64.b64decode(stored.encode("utf-8"))
        salt, dk = raw[:16], raw[16:]
        new_dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, rounds)
        return hmac.compare_digest(dk, new_dk)
    except Exception:
        return False


def add_student(student_id: str, name: str, password_plain: str, db_path: str = DB_DEFAULT) -> int:
    student_id = (student_id or "").strip()
    name = (name or "").strip()
    password_plain = password_plain or ""

    if not student_id or not name or not password_plain:
        raise ValueError("student_id, name, and password are required.")

    init_db(db_path)
    pw_hash = _hash_password(password_plain)

    with _connect(db_path) as conn:
        cur = conn.execute(
            "INSERT INTO users(student_id, name, password_hash) VALUES (?, ?, ?)",
            (student_id, name, pw_hash),
        )
        return int(cur.lastrowid)


def get_user_by_student_id(student_id: str, db_path: str = DB_DEFAULT) -> Optional[dict[str, Any]]:
    init_db(db_path)
    student_id = (student_id or "").strip()
    if not student_id:
        return None

    with _connect(db_path) as conn:
        row = conn.execute(
            "SELECT id, student_id, name, created_at FROM users WHERE student_id = ?",
            (student_id,),
        ).fetchone()
        return dict(row) if row else None


def verify_login(student_id: str, password_plain: str, db_path: str = DB_DEFAULT) -> Optional[dict[str, Any]]:
    init_db(db_path)
    student_id = (student_id or "").strip()
    password_plain = password_plain or ""
    if not student_id or not password_plain:
        return None

    with _connect(db_path) as conn:
        row = conn.execute(
            "SELECT id, student_id, name, password_hash FROM users WHERE student_id = ?",
            (student_id,),
        ).fetchone()

        if not row:
            return None

        if not _verify_password(password_plain, row["password_hash"]):
            return None

        return {"id": row["id"], "student_id": row["student_id"], "name": row["name"]}


def record_attendance(
    user_id: int,
    snapshot_path: str | None = None,
    confidence: float | None = None,
    liveness_ok: bool = False,
    db_path: str = DB_DEFAULT,
) -> int:
    init_db(db_path)
    if not isinstance(user_id, int) or user_id <= 0:
        raise ValueError("user_id must be a positive int.")

    snap = (snapshot_path or "").strip() or None
    conf = float(confidence) if confidence is not None else None
    live = 1 if bool(liveness_ok) else 0

    with _connect(db_path) as conn:
        cur = conn.execute(
            "INSERT INTO attendance(user_id, snapshot_path, confidence, liveness_ok) VALUES (?, ?, ?, ?)",
            (user_id, snap, conf, live),
        )
        return int(cur.lastrowid)


def list_attendance(
    user_id: int | None = None,
    limit: int = 200,
    db_path: str = DB_DEFAULT,
) -> list[dict[str, Any]]:
    init_db(db_path)
    limit = max(1, min(int(limit), 2000))

    query = """
    SELECT
        a.id,
        a.timestamp,
        a.snapshot_path,
        a.confidence,
        a.liveness_ok,
        u.id AS user_id,
        u.student_id,
        u.name
    FROM attendance a
    JOIN users u ON u.id = a.user_id
    """

    params: list[Any] = []
    if user_id is not None:
        query += " WHERE a.user_id = ?"
        params.append(int(user_id))

    query += " ORDER BY a.timestamp DESC LIMIT ?"
    params.append(limit)

    with _connect(db_path) as conn:
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]


def latest_attendance_for_student(student_id: str, db_path: str = DB_DEFAULT) -> Optional[dict[str, Any]]:
    init_db(db_path)
    student_id = (student_id or "").strip()
    if not student_id:
        return None

    query = """
    SELECT
        a.id,
        a.timestamp,
        a.snapshot_path,
        a.confidence,
        a.liveness_ok,
        u.id AS user_id,
        u.student_id,
        u.name
    FROM attendance a
    JOIN users u ON u.id = a.user_id
    WHERE u.student_id = ?
    ORDER BY a.timestamp DESC
    LIMIT 1
    """

    with _connect(db_path) as conn:
        row = conn.execute(query, (student_id,)).fetchone()
        return dict(row) if row else None
