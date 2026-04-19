"""
Claude Code Agent Core - Types and Configuration
Базовые типы, конфигурация и состояние сессии
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


__all__ = [
    "AgentMode",
    "ModelConfig", 
    "SessionConfig",
    "SessionState"
]
