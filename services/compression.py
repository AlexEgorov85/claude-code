"""
Context Compression Service - сжатие контекста для уменьшения токенов
"""

from typing import Optional, Dict, Any, List


class ContextCompressor:
    """
    Компрессор контекста для уменьшения использования токенов
    """
    
    def __init__(self, max_tokens: int = 100000):
        self.max_tokens = max_tokens
        self._compression_ratio = 0.5  # Целевой коэффициент сжатия
    
    def compress(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Сжать список сообщений
        
        Стратегии:
        1. Удаление старых сообщений
        2. Саммаризация диалогов
        3. Удаление избыточных деталей
        """
        # Простая реализация - удаление старых сообщений
        while len(messages) > 10:
            messages.pop(0)
        
        return messages
    
    def estimate_tokens(self, text: str) -> int:
        """Оценить количество токенов в тексте"""
        # Приблизительная оценка: 4 символа ≈ 1 токен
        return len(text) // 4


__all__ = ["ContextCompressor"]
