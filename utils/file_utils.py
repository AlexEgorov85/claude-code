"""
File utilities - работа с файлами
"""

import hashlib
from pathlib import Path
from typing import Union, List


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


__all__ = ["read_file", "write_file", "file_exists", "get_file_hash", "find_files"]
