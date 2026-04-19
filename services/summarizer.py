"""
Summarization Service - создание кратких изложений текста
"""

from typing import Optional, Dict, Any, List
from .api_client import APIClient


class Summarizer:
    """
    Саммаризатор для создания кратких изложений
    """
    
    def __init__(self, api_client: Optional[APIClient] = None):
        self.api_client = api_client
        self._cache: Dict[str, str] = {}
    
    async def summarize(
        self,
        text: str,
        max_length: int = 500,
        style: str = "concise"
    ) -> str:
        """Создать саммари текста"""
        cache_key = f"{hash(text)}:{max_length}:{style}"
        
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Здесь будет вызов LLM для саммаризации
        # Пока простая заглушка
        summary = text[:max_length] + "..." if len(text) > max_length else text
        
        self._cache[cache_key] = summary
        return summary
    
    async def summarize_conversation(
        self,
        messages: List[Dict[str, Any]],
        max_length: int = 1000
    ) -> str:
        """Саммаризировать разговор"""
        # Извлекаем текст из сообщений
        texts = []
        for msg in messages:
            if isinstance(msg.get("content"), str):
                texts.append(msg["content"])
        
        combined = "\n".join(texts)
        return await self.summarize(combined, max_length)
    
    def clear_cache(self):
        self._cache.clear()


__all__ = ["Summarizer"]
