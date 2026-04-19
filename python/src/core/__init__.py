"""
Claude Code Agent Core - Python Implementation
Ядро агента: базовые типы, конфигурация и состояние сессии
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum
import uuid
from datetime import datetime


class AgentMode(Enum):
    """Режимы работы агента"""
    DEFAULT = "default"
    UNDERCOVER = "undercover"
    ULTRAPLAN = "ultraplan"
    PENGUIN = "penguin"


@dataclass
class ModelConfig:
    """Конфигурация модели"""
    model_id: str
    provider: str
    max_tokens: int
    context_window: int
    supports_vision: bool = False
    supports_tools: bool = True


@dataclass
class SessionConfig:
    """Конфигурация сессии"""
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    working_directory: str = "."
    mode: AgentMode = AgentMode.DEFAULT
    model: Optional[ModelConfig] = None
    max_iterations: int = 100
    timeout_seconds: int = 3600
    feature_flags: Dict[str, bool] = field(default_factory=dict)
    
    def __post_init__(self):
        if self.model is None:
            self.model = ModelConfig(
                model_id="claude-sonnet-4-20250514",
                provider="anthropic",
                max_tokens=8192,
                context_window=200000,
                supports_vision=True,
                supports_tools=True
            )


@dataclass
class SessionState:
    """Состояние активной сессии"""
    config: SessionConfig
    created_at: datetime = field(default_factory=datetime.utcnow)
    message_count: int = 0
    tool_call_count: int = 0
    total_token_usage: int = 0
    current_task_id: Optional[str] = None
    active_agents: Dict[str, Any] = field(default_factory=dict)
    context_items: List[Dict[str, Any]] = field(default_factory=list)
    is_running: bool = False
    
    def add_context(self, item_type: str, content: Any, metadata: Optional[Dict] = None):
        """Добавить элемент в контекст сессии"""
        self.context_items.append({
            "type": item_type,
            "content": content,
            "metadata": metadata or {},
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def increment_tool_calls(self):
        self.tool_call_count += 1
    
    def update_token_usage(self, tokens: int):
        self.total_token_usage += tokens


class AgentCore:
    """
    Ядро агента - центральный компонент управления
    """
    
    def __init__(self, config: Optional[SessionConfig] = None):
        self.config = config or SessionConfig()
        self.state = SessionState(config=self.config)
        self._initialized = False
    
    async def initialize(self):
        """Инициализация ядра агента"""
        if self._initialized:
            return
        
        # Валидация конфигурации
        if not self.config.working_directory:
            raise ValueError("Working directory must be specified")
        
        # Инициализация подсистем будет вызвана здесь
        self._initialized = True
    
    async def shutdown(self):
        """Корректное завершение работы"""
        self.state.is_running = False
        # Очистка ресурсов, закрытие соединений
    
    @property
    def session_id(self) -> str:
        return self.config.session_id
    
    @property
    def is_initialized(self) -> bool:
        return self._initialized
    
    def get_state_summary(self) -> Dict[str, Any]:
        """Получить краткую сводку состояния"""
        return {
            "session_id": self.session_id,
            "mode": self.config.mode.value,
            "model": self.config.model.model_id if self.config.model else None,
            "message_count": self.state.message_count,
            "tool_call_count": self.state.tool_call_count,
            "token_usage": self.state.total_token_usage,
            "is_running": self.state.is_running,
            "context_items_count": len(self.state.context_items)
        }


__all__ = [
    "AgentMode",
    "ModelConfig", 
    "SessionConfig",
    "SessionState",
    "AgentCore"
]
