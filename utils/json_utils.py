"""
JSON utilities - сериализация и десериализация JSON
"""

import json
from pathlib import Path
from typing import Any, Union, Optional, Callable
from datetime import datetime


def to_json(obj: Any, indent: int = 2, default: Optional[Callable] = None) -> str:
    """Сериализовать объект в JSON"""
    def default_handler(o):
        if isinstance(o, datetime):
            return o.isoformat()
        if hasattr(o, "__dict__"):
            return o.__dict__
        return str(o)
    
    return json.dumps(obj, indent=indent, default=default or default_handler)


def from_json(text: str) -> Any:
    """Десериализовать JSON"""
    return json.loads(text)


def load_json_file(path: Union[str, Path]) -> Any:
    """Загрузить JSON из файла"""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json_file(path: Union[str, Path], data: Any, indent: int = 2):
    """Сохранить данные в JSON файл"""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, default=str)


__all__ = ["to_json", "from_json", "load_json_file", "save_json_file"]
