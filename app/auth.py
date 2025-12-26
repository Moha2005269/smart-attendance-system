from __future__ import annotations
from typing import Optional, Any
from . import database

_CURRENT_USER: Optional[dict[str, Any]] = None


def login(student_id: str, password: str) -> Optional[dict[str, Any]]:
    global _CURRENT_USER
    user = database.verify_login(student_id, password)
    _CURRENT_USER = user
    return user


def logout() -> None:
    global _CURRENT_USER
    _CURRENT_USER = None


def current_user() -> Optional[dict[str, Any]]:
    return _CURRENT_USER
