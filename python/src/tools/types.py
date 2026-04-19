"""
Система инструментов - базовые типы и интерфейсы
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum
import uuid
from datetime import datetime


class ToolStatus(Enum):
    """Статус выполнения инструмента"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    ERROR = "error"
    CANCELLED = "cancelled"


@dataclass
class ToolInput:
    """Входные данные для инструмента"""
    name: str
    arguments: Dict[str, Any]
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class ToolOutput:
    """Результат выполнения инструмента"""
    success: bool
    content: Any
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolCall:
    """Вызов инструмента"""
    tool_name: str
    input_data: ToolInput
    status: ToolStatus = ToolStatus.PENDING
    output: Optional[ToolOutput] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    execution_time_ms: Optional[int] = None


class BaseTool(ABC):
    """
    Базовый класс для всех инструментов
    """
    
    name: str = "base_tool"
    description: str = "Base tool"
    requires_permission: bool = True
    
    @abstractmethod
    async def execute(self, input_data: ToolInput) -> ToolOutput:
        """Выполнить инструмент"""
        pass
    
    def validate_input(self, input_data: ToolInput) -> bool:
        """Валидировать входные данные"""
        return True
    
    def get_schema(self) -> Dict[str, Any]:
        """Получить JSON схему инструмента"""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {}
        }


class ToolRegistry:
    """
    Реестр доступных инструментов
    """
    
    _instance: Optional["ToolRegistry"] = None
    _tools: Dict[str, BaseTool]
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._tools = {}
        return cls._instance
    
    def register(self, tool: BaseTool):
        """Зарегистрировать инструмент"""
        self._tools[tool.name] = tool
    
    def unregister(self, tool_name: str):
        """Удалить инструмент из реестра"""
        if tool_name in self._tools:
            del self._tools[tool_name]
    
    def get(self, tool_name: str) -> Optional[BaseTool]:
        """Получить инструмент по имени"""
        return self._tools.get(tool_name)
    
    def list_tools(self) -> List[str]:
        """Получить список всех зарегистрированных инструментов"""
        return list(self._tools.keys())
    
    def clear(self):
        """Очистить реестр"""
        self._tools.clear()


# Типы разрешений для инструментов
class PermissionType(Enum):
    ALWAYS_ALLOW = "always_allow"
    ASK_USER = "ask_user"
    DENY = "deny"


@dataclass
class ToolPermission:
    """Разрешение для инструмента"""
    tool_name: str
    permission_type: PermissionType
    patterns: List[str] = field(default_factory=list)  # Паттерны для команд/путей


__all__ = [
    "ToolStatus",
    "ToolInput",
    "ToolOutput", 
    "ToolCall",
    "BaseTool",
    "ToolRegistry",
    "PermissionType",
    "ToolPermission"
]
