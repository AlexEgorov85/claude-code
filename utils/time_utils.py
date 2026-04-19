"""
Time utilities - операции со временем
"""

from datetime import datetime


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


__all__ = ["now_iso", "parse_iso", "format_duration"]
