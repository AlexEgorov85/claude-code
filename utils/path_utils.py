"""
Path utilities - операции с путями
"""

from pathlib import Path
from typing import Union


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


__all__ = ["resolve_path", "is_subpath"]
