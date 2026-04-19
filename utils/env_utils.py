"""
Environment utilities - работа с переменными окружения
"""

import os
from typing import Optional


def get_env(name: str, default: Optional[str] = None) -> Optional[str]:
    """Получить переменную окружения"""
    return os.environ.get(name, default)


def get_env_bool(name: str, default: bool = False) -> bool:
    """Получить boolean переменную окружения"""
    value = os.environ.get(name, "").lower()
    if value in ("true", "1", "yes"):
        return True
    if value in ("false", "0", "no"):
        return False
    return default


def require_env(name: str) -> str:
    """Получить обязательную переменную окружения"""
    value = os.environ.get(name)
    if not value:
        raise ValueError(f"Required environment variable {name} is not set")
    return value


__all__ = ["get_env", "get_env_bool", "require_env"]
