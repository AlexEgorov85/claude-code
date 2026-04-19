"""
Утилиты - вспомогательные функции и классы
"""

import os
import sys
import json
import hashlib
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List, Union
from datetime import datetime


# ============================================================================
# Логирование
# ============================================================================

def setup_logger(
    name: str,
    level: int = logging.INFO,
    format_string: Optional[str] = None
) -> logging.Logger:
    """Настроить логгер"""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        
        fmt = format_string or "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        formatter = logging.Formatter(fmt)
        handler.setFormatter(formatter)
        
        logger.addHandler(handler)
    
    return logger


# ============================================================================
# Работа с файлами
# ============================================================================

def read_file(path: Union[str, Path], encoding: str = "utf-8") -> str:
    """Прочитать файл"""
    with open(path, "r", encoding=encoding) as f:
        return f.read()


def write_file(path: Union[str, Path], content: str, encoding: str = "utf-8"):
    """Записать файл"""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding=encoding) as f:
        f.write(content)


def file_exists(path: Union[str, Path]) -> bool:
    """Проверить существование файла"""
    return Path(path).exists()


def get_file_hash(path: Union[str, Path]) -> str:
    """Получить хэш файла (SHA256)"""
    sha256 = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def find_files(
    directory: Union[str, Path],
    pattern: str = "*",
    recursive: bool = True
) -> List[Path]:
    """Найти файлы по паттерну"""
    path = Path(directory)
    if recursive:
        return list(path.rglob(pattern))
    return list(path.glob(pattern))


# ============================================================================
# JSON утилиты
# ============================================================================

def to_json(obj: Any, indent: int = 2, default: Optional[callable] = None) -> str:
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


# ============================================================================
# Строковые утилиты
# ============================================================================

def truncate(text: str, max_length: int, suffix: str = "...") -> str:
    """Обрезать текст до максимальной длины"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def indent(text: str, spaces: int = 4) -> str:
    """Добавить отступы к тексту"""
    prefix = " " * spaces
    return "\n".join(prefix + line for line in text.split("\n"))


def strip_ansi(text: str) -> str:
    """Удалить ANSI escape последовательности"""
    import re
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    return ansi_escape.sub("", text)


# ============================================================================
# Асинхронные утилиты
# ============================================================================

async def async_sleep(seconds: float):
    """Асинхронная задержка"""
    import asyncio
    await asyncio.sleep(seconds)


async def run_in_executor(func: callable, *args, executor=None):
    """Выполнить функцию в executor"""
    import asyncio
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, func, *args)


# ============================================================================
# Утилиты времени
# ============================================================================

def now_iso() -> str:
    """Получить текущее время в ISO формате"""
    return datetime.utcnow().isoformat()


def parse_iso(iso_string: str) -> datetime:
    """Парсить ISO строку в datetime"""
    return datetime.fromisoformat(iso_string.replace("Z", "+00:00"))


def format_duration(seconds: float) -> str:
    """Форматировать длительность в человекочитаемый вид"""
    if seconds < 60:
        return f"{seconds:.2f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.1f}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours}h {minutes}m {secs:.1f}s"


# ============================================================================
# Утилиты окружения
# ============================================================================

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


# ============================================================================
# Утилиты для работы с путями
# ============================================================================

def resolve_path(path: Union[str, Path], base: Optional[Union[str, Path]] = None) -> Path:
    """Разрешить путь относительно базового"""
    p = Path(path)
    if p.is_absolute():
        return p.resolve()
    if base:
        return (Path(base) / p).resolve()
    return p.resolve()


def is_subpath(path: Union[str, Path], parent: Union[str, Path]) -> bool:
    """Проверить является ли путь подпутем"""
    try:
        Path(path).resolve().relative_to(Path(parent).resolve())
        return True
    except ValueError:
        return False


# ============================================================================
# Декораторы
# ============================================================================

def retry(max_attempts: int = 3, delay: float = 1.0, exceptions: tuple = (Exception,)):
    """Декоратор для повторных попыток"""
    import functools
    import asyncio
    
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay * (attempt + 1))
            raise last_exception
        return wrapper
    return decorator


def timing(logger: Optional[logging.Logger] = None):
    """Декоратор для замера времени выполнения"""
    import functools
    import time
    
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            start = time.time()
            try:
                return await func(*args, **kwargs)
            finally:
                elapsed = time.time() - start
                if logger:
                    logger.debug(f"{func.__name__} took {elapsed:.3f}s")
                else:
                    print(f"{func.__name__} took {elapsed:.3f}s")
        return wrapper
    return decorator


__all__ = [
    # Logging
    "setup_logger",
    # Files
    "read_file",
    "write_file",
    "file_exists",
    "get_file_hash",
    "find_files",
    # JSON
    "to_json",
    "from_json",
    "load_json_file",
    "save_json_file",
    # Strings
    "truncate",
    "indent",
    "strip_ansi",
    # Async
    "async_sleep",
    "run_in_executor",
    # Time
    "now_iso",
    "parse_iso",
    "format_duration",
    # Env
    "get_env",
    "get_env_bool",
    "require_env",
    # Paths
    "resolve_path",
    "is_subpath",
    # Decorators
    "retry",
    "timing"
]
