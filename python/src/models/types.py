"""
Модельный слой - типы и модели данных
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum
from datetime import datetime, timedelta


class ModelProvider(Enum):
    """Провайдеры моделей"""
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GOOGLE = "google"
    AZURE = "azure"
    LOCAL = "local"


class ModelCapability(Enum):
    """Возможности модели"""
    TEXT = "text"
    VISION = "vision"
    TOOLS = "tools"
    FUNCTION_CALLING = "function_calling"
    JSON_MODE = "json_mode"


@dataclass
class ModelInfo:
    """Информация о модели"""
    model_id: str
    provider: ModelProvider
    display_name: str
    context_window: int
    max_output_tokens: int
    capabilities: List[ModelCapability]
    supports_streaming: bool = True
    cost_per_input_token: float = 0.0
    cost_per_output_token: float = 0.0
    
    def has_capability(self, capability: ModelCapability) -> bool:
        return capability in self.capabilities


@dataclass
class TokenUsage:
    """Использование токенов"""
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0
    
    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens
    
    def add(self, other: "TokenUsage") -> "TokenUsage":
        return TokenUsage(
            input_tokens=self.input_tokens + other.input_tokens,
            output_tokens=self.output_tokens + other.output_tokens,
            cache_read_tokens=self.cache_read_tokens + other.cache_read_tokens,
            cache_write_tokens=self.cache_write_tokens + other.cache_write_tokens
        )


@dataclass
class RateLimit:
    """Ограничения скорости"""
    requests_per_minute: int = 60
    tokens_per_minute: int = 100000
    requests_per_day: int = 10000
    
    current_requests_minute: int = 0
    current_tokens_minute: int = 0
    current_requests_day: int = 0
    
    last_reset_minute: datetime = field(default_factory=datetime.utcnow)
    last_reset_day: datetime = field(default_factory=datetime.utcnow)
    
    def check_limit(self, tokens: int = 1) -> tuple[bool, str]:
        """Проверить ограничения"""
        now = datetime.utcnow()
        
        # Сброс счетчиков每分钟
        if (now - self.last_reset_minute).total_seconds() >= 60:
            self.current_requests_minute = 0
            self.current_tokens_minute = 0
            self.last_reset_minute = now
        
        # Сброс счетчиков ежедневно
        if (now - self.last_reset_day).total_seconds() >= 86400:
            self.current_requests_day = 0
            self.last_reset_day = now
        
        # Проверка лимитов
        if self.current_requests_minute >= self.requests_per_minute:
            return False, "Rate limit exceeded: requests per minute"
        
        if self.current_tokens_minute + tokens > self.tokens_per_minute:
            return False, "Rate limit exceeded: tokens per minute"
        
        if self.current_requests_day >= self.requests_per_day:
            return False, "Rate limit exceeded: requests per day"
        
        return True, ""
    
    def record_request(self, tokens: int = 1):
        """Записать запрос"""
        self.current_requests_minute += 1
        self.current_tokens_minute += tokens
        self.current_requests_day += 1


@dataclass
class ModelConfig:
    """Конфигурация для использования модели"""
    model_id: str
    provider: ModelProvider
    temperature: float = 0.7
    max_tokens: int = 4096
    top_p: float = 0.9
    stop_sequences: List[str] = field(default_factory=list)
    system_prompt: Optional[str] = None


__all__ = [
    "ModelProvider",
    "ModelCapability",
    "ModelInfo",
    "TokenUsage",
    "RateLimit",
    "ModelConfig"
]
