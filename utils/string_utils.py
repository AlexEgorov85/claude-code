"""
String utilities - строковые операции
"""

import re
from typing import Optional


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
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    return ansi_escape.sub("", text)


__all__ = ["truncate", "indent", "strip_ansi"]
