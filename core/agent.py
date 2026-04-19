"""
Claude Code Agent Core - Main Agent Class
Центральный компонент управления агентом
"""

from typing import Optional, Dict, Any
from .types import SessionConfig, SessionState, AgentCore


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


__all__ = ["AgentCore"]
