"""Базовый класс для инструментов."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional, Callable
import asyncio
import time


@dataclass
class ToolDefinition:
    """Определение инструмента."""
    name: str
    description: str
    input_schema: dict[str, Any]
    is_hidden: bool = False
    is_read_only: bool = False
    timeout: float = 60.0


@dataclass
class ToolResult:
    """Результат выполнения инструмента."""
    content: Any
    is_error: bool = False
    error_message: Optional[str] = None
    execution_time: float = 0.0


class BaseTool(ABC):
    """Базовый класс для всех инструментов."""
    
    def __init__(self):
        self._definition: Optional[ToolDefinition] = None
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Название инструмента."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Описание инструмента."""
        pass
    
    @property
    @abstractmethod
    def input_schema(self) -> dict[str, Any]:
        """JSON Schema для входных параметров."""
        pass
    
    @property
    def is_hidden(self) -> bool:
        """Скрыт ли инструмент от пользователя."""
        return False
    
    @property
    def is_read_only(self) -> bool:
        """Только чтение (не изменяет состояние)."""
        return False
    
    @property
    def timeout(self) -> float:
        """Таймаут выполнения в секундах."""
        return 60.0
    
    @property
    def definition(self) -> ToolDefinition:
        """Получение определения инструмента."""
        if not self._definition:
            self._definition = ToolDefinition(
                name=self.name,
                description=self.description,
                input_schema=self.input_schema,
                is_hidden=self.is_hidden,
                is_read_only=self.is_read_only,
                timeout=self.timeout
            )
        return self._definition
    
    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """Выполнение инструмента."""
        pass
    
    async def execute_with_timeout(self, **kwargs) -> ToolResult:
        """Выполнение с таймаутом."""
        start_time = time.time()
        try:
            result = await asyncio.wait_for(
                self.execute(**kwargs),
                timeout=self.timeout
            )
            result.execution_time = time.time() - start_time
            return result
        except asyncio.TimeoutError:
            return ToolResult(
                content=None,
                is_error=True,
                error_message=f"Tool execution timed out after {self.timeout} seconds",
                execution_time=time.time() - start_time
            )
        except Exception as e:
            return ToolResult(
                content=None,
                is_error=True,
                error_message=str(e),
                execution_time=time.time() - start_time
            )
    
    def validate_input(self, input_data: dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Валидация входных данных."""
        # Простая валидация - проверка наличия обязательных полей
        schema = self.input_schema
        required = schema.get("required", [])
        properties = schema.get("properties", {})
        
        for field_name in required:
            if field_name not in input_data:
                return False, f"Missing required field: {field_name}"
        
        # Проверка типов (базовая)
        for field_name, value in input_data.items():
            if field_name in properties:
                field_type = properties[field_name].get("type")
                if field_type == "string" and not isinstance(value, str):
                    return False, f"Field {field_name} must be a string"
                elif field_type == "integer" and not isinstance(value, int):
                    return False, f"Field {field_name} must be an integer"
                elif field_type == "number" and not isinstance(value, (int, float)):
                    return False, f"Field {field_name} must be a number"
                elif field_type == "boolean" and not isinstance(value, bool):
                    return False, f"Field {field_name} must be a boolean"
                elif field_type == "array" and not isinstance(value, list):
                    return False, f"Field {field_name} must be an array"
                elif field_type == "object" and not isinstance(value, dict):
                    return False, f"Field {field_name} must be an object"
        
        return True, None
