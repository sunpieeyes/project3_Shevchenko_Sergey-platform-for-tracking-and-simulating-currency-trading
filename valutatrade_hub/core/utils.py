from __future__ import annotations

import hashlib
import json
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def get_current_time() -> str:
    """Текущее время в ISO формате (UTC)."""
    return datetime.now(timezone.utc).isoformat()


def hash_password(password: str, salt: str | None = None) -> tuple[str, str]:
    """
    Псевдо-хеш пароля (SHA-256 + соль).
    Возвращает (hashed_password, salt).
    """
    if not isinstance(password, str) or len(password) < 4:
        raise ValueError("Пароль должен быть не короче 4 символов")

    if salt is None:
        salt = secrets.token_hex(4)

    raw = (password + salt).encode("utf-8")
    hashed = hashlib.sha256(raw).hexdigest()
    return hashed, salt


def get_next_id(items: list[dict[str, Any]], key: str = "user_id") -> int:
    """Автоинкремент id для списка словарей."""
    if not items:
        return 1
    return max(int(x.get(key, 0)) for x in items) + 1


def load_json(path: str) -> Any:
    file_path = Path(path)
    if not file_path.exists():
        return {}

    for encoding in ("utf-8", "utf-8-sig", "utf-16"):
        try:
            with file_path.open("r", encoding=encoding) as f:
                return json.load(f)
        except UnicodeDecodeError:
            continue
        except json.JSONDecodeError:
            return {}

    data = file_path.read_bytes()
    for encoding in ("utf-16", "utf-8-sig", "utf-8"):
        try:
            return json.loads(data.decode(encoding))
        except Exception:
            continue

    return {}


def save_json(path: str, data: Any) -> None:
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with file_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def verify_password(password: str, hashed_password: str, salt: str) -> bool:

    import hashlib

    check_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    return check_hash == hashed_password

