"""
Модельный слой - управление моделями, выбор, проверка доступности и лимитов
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum
from datetime import datetime, timedelta
import asyncio


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


class ModelManager:
    """
    Менеджер моделей - управление доступными моделями и их выбором
    """
    
    _instance: Optional["ModelManager"] = None
    _models: Dict[str, ModelInfo]
    _rate_limits: Dict[str, RateLimit]
    _usage_stats: Dict[str, TokenUsage]
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._models = {}
            cls._instance._rate_limits = {}
            cls._instance._usage_stats = {}
            cls._instance._initialize_default_models()
        return cls._instance
    
    def _initialize_default_models(self):
        """Инициализировать модели по умолчанию"""
        default_models = [
            ModelInfo(
                model_id="claude-sonnet-4-20250514",
                provider=ModelProvider.ANTHROPIC,
                display_name="Claude Sonnet 4",
                context_window=200000,
                max_output_tokens=8192,
                capabilities=[
                    ModelCapability.TEXT,
                    ModelCapability.VISION,
                    ModelCapability.TOOLS,
                    ModelCapability.FUNCTION_CALLING,
                    ModelCapability.JSON_MODE
                ],
                cost_per_input_token=0.000003,
                cost_per_output_token=0.000015
            ),
            ModelInfo(
                model_id="claude-opus-4-20250514",
                provider=ModelProvider.ANTHROPIC,
                display_name="Claude Opus 4",
                context_window=200000,
                max_output_tokens=8192,
                capabilities=[
                    ModelCapability.TEXT,
                    ModelCapability.VISION,
                    ModelCapability.TOOLS,
                    ModelCapability.FUNCTION_CALLING,
                    ModelCapability.JSON_MODE
                ],
                cost_per_input_token=0.000015,
                cost_per_output_token=0.000075
            ),
            ModelInfo(
                model_id="gpt-4o",
                provider=ModelProvider.OPENAI,
                display_name="GPT-4o",
                context_window=128000,
                max_output_tokens=4096,
                capabilities=[
                    ModelCapability.TEXT,
                    ModelCapability.VISION,
                    ModelCapability.TOOLS,
                    ModelCapability.FUNCTION_CALLING,
                    ModelCapability.JSON_MODE
                ]
            )
        ]
        
        for model in default_models:
            self.register_model(model)
            self._rate_limits[model.model_id] = RateLimit()
            self._usage_stats[model.model_id] = TokenUsage()
    
    def register_model(self, model: ModelInfo):
        """Зарегистрировать модель"""
        self._models[model.model_id] = model
    
    def get_model(self, model_id: str) -> Optional[ModelInfo]:
        """Получить информацию о модели"""
        return self._models.get(model_id)
    
    def list_models(
        self, 
        provider: Optional[ModelProvider] = None,
        capability: Optional[ModelCapability] = None
    ) -> List[ModelInfo]:
        """Получить список моделей с фильтрацией"""
        models = list(self._models.values())
        
        if provider:
            models = [m for m in models if m.provider == provider]
        
        if capability:
            models = [m for m in models if m.has_capability(capability)]
        
        return models
    
    def select_best_model(
        self,
        required_capabilities: Optional[List[ModelCapability]] = None,
        min_context_window: int = 0,
        preferred_provider: Optional[ModelProvider] = None
    ) -> Optional[ModelInfo]:
        """Выбрать лучшую модель по критериям"""
        candidates = self.list_models()
        
        # Фильтрация по возможностям
        if required_capabilities:
            candidates = [
                m for m in candidates
                if all(m.has_capability(c) for c in required_capabilities)
            ]
        
        # Фильтрация по контекстному окну
        candidates = [m for m in candidates if m.context_window >= min_context_window]
        
        # Предпочтение провайдеру
        if preferred_provider:
            preferred = [m for m in candidates if m.provider == preferred_provider]
            if preferred:
                candidates = preferred
        
        if not candidates:
            return None
        
        # Возвращаем первую подходящую (можно улучшить логику выбора)
        return candidates[0]
    
    def check_availability(self, model_id: str, tokens: int = 1) -> tuple[bool, str]:
        """Проверить доступность модели"""
        if model_id not in self._models:
            return False, f"Model {model_id} not found"
        
        rate_limit = self._rate_limits.get(model_id)
        if rate_limit:
            return rate_limit.check_limit(tokens)
        
        return True, ""
    
    def record_usage(self, model_id: str, usage: TokenUsage):
        """Записать использование модели"""
        if model_id in self._usage_stats:
            self._usage_stats[model_id] = self._usage_stats[model_id].add(usage)
        
        rate_limit = self._rate_limits.get(model_id)
        if rate_limit:
            rate_limit.record_request(usage.total_tokens)
    
    def get_usage_stats(self, model_id: str) -> Optional[TokenUsage]:
        """Получить статистику использования"""
        return self._usage_stats.get(model_id)
    
    def estimate_cost(self, model_id: str, input_tokens: int, output_tokens: int) -> float:
        """Оценить стоимость запроса"""
        model = self.get_model(model_id)
        if not model:
            return 0.0
        
        return (
            input_tokens * model.cost_per_input_token +
            output_tokens * model.cost_per_output_token
        )


__all__ = [
    "ModelProvider",
    "ModelCapability",
    "ModelInfo",
    "TokenUsage",
    "RateLimit",
    "ModelConfig",
    "ModelManager"
]
