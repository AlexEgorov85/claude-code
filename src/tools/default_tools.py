"""Пример простого инструмента для демонстрации."""
from typing import Any
from ..tools.base import BaseTool, ToolResult


class EchoTool(BaseTool):
    """Простой инструмент для эхо-ответа."""
    
    @property
    def name(self) -> str:
        return "echo"
    
    @property
    def description(self) -> str:
        return "Возвращает полученный текст обратно. Полезно для тестирования."
    
    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "Текст для возврата"
                }
            },
            "required": ["message"]
        }
    
    async def execute(self, message: str, **kwargs) -> ToolResult:
        """Выполнение инструмента."""
        return ToolResult(
            content=f"Echo: {message}",
            is_error=False
        )


class CalculatorTool(BaseTool):
    """Инструмент для простых вычислений."""
    
    @property
    def name(self) -> str:
        return "calculator"
    
    @property
    def description(self) -> str:
        return "Выполняет простые арифметические операции: сложение, вычитание, умножение, деление."
    
    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["add", "subtract", "multiply", "divide"],
                    "description": "Арифметическая операция"
                },
                "a": {
                    "type": "number",
                    "description": "Первый операнд"
                },
                "b": {
                    "type": "number",
                    "description": "Второй операнд"
                }
            },
            "required": ["operation", "a", "b"]
        }
    
    async def execute(
        self, 
        operation: str, 
        a: float, 
        b: float,
        **kwargs
    ) -> ToolResult:
        """Выполнение вычислений."""
        try:
            if operation == "add":
                result = a + b
            elif operation == "subtract":
                result = a - b
            elif operation == "multiply":
                result = a * b
            elif operation == "divide":
                if b == 0:
                    return ToolResult(
                        content=None,
                        is_error=True,
                        error_message="Division by zero"
                    )
                result = a / b
            else:
                return ToolResult(
                    content=None,
                    is_error=True,
                    error_message=f"Unknown operation: {operation}"
                )
            
            return ToolResult(
                content=result,
                is_error=False
            )
        except Exception as e:
            return ToolResult(
                content=None,
                is_error=True,
                error_message=str(e)
            )


def register_default_tools(registry=None) -> None:
    """Регистрация инструментов по умолчанию."""
    from ..tools.registry import ToolRegistry
    
    reg = registry or ToolRegistry()
    reg.register(EchoTool())
    reg.register(CalculatorTool())
    
    return reg
