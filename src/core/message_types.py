"""Базовые типы сообщений для агентского цикла."""
from dataclasses import dataclass, field
from typing import Any, Optional
from enum import Enum
import time


class MessageType(Enum):
    """Типы сообщений в системе."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL_USE = "tool_use"
    TOOL_RESULT = "tool_result"
    ERROR = "error"


@dataclass
class ToolCall:
    """Представление вызова инструмента."""
    id: str
    name: str
    input: dict[str, Any]
    is_complete: bool = False


@dataclass
class ToolResult:
    """Результат выполнения инструмента."""
    tool_call_id: str
    content: Any
    is_error: bool = False
    error_message: Optional[str] = None


@dataclass
class Message:
    """Базовое сообщение в диалоге."""
    role: MessageType
    content: Any
    timestamp: float = field(default_factory=time.time)
    id: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Конвертация в словарь."""
        return {
            "role": self.role.value,
            "content": self.content,
            "timestamp": self.timestamp,
            "id": self.id
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Message":
        """Создание из словаря."""
        return cls(
            role=MessageType(data["role"]),
            content=data["content"],
            timestamp=data.get("timestamp", time.time()),
            id=data.get("id")
        )


@dataclass
class UserMessage(Message):
    """Сообщение от пользователя."""
    def __post_init__(self):
        self.role = MessageType.USER


@dataclass
class AssistantMessage(Message):
    """Сообщение от ассистента."""
    tool_calls: list[ToolCall] = field(default_factory=list)
    
    def __post_init__(self):
        self.role = MessageType.ASSISTANT
    
    def has_tool_calls(self) -> bool:
        """Проверка наличия вызовов инструментов."""
        return len(self.tool_calls) > 0


@dataclass
class SystemMessage(Message):
    """Системное сообщение."""
    def __post_init__(self):
        self.role = MessageType.SYSTEM


@dataclass
class ToolUseMessage(Message):
    """Сообщение о использовании инструмента."""
    tool_call: ToolCall = None  # type: ignore
    
    def __post_init__(self):
        self.role = MessageType.TOOL_USE
        if self.tool_call:
            self.content = {
                "id": self.tool_call.id,
                "name": self.tool_call.name,
                "input": self.tool_call.input
            }


@dataclass
class ToolResultMessage(Message):
    """Сообщение с результатом инструмента."""
    tool_result: ToolResult = None  # type: ignore
    
    def __post_init__(self):
        self.role = MessageType.TOOL_RESULT
        if self.tool_result:
            self.content = {
                "tool_call_id": self.tool_result.tool_call_id,
                "content": self.tool_result.content,
                "is_error": self.tool_result.is_error,
                "error_message": self.tool_result.error_message
            }


@dataclass
class ErrorMessage(Message):
    """Сообщение об ошибке."""
    error_code: Optional[str] = None
    
    def __post_init__(self):
        self.role = MessageType.ERROR
