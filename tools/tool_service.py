"""
Сервис управления инструментами
"""
import asyncio
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
import uuid

from .types import (
    BaseTool, ToolInput, ToolOutput, ToolCall, ToolStatus,
    ToolRegistry
)
from .permissions import PermissionManager, PermissionRequest, PermissionGrant


class ToolServiceConfig:
    """Конфигурация сервиса инструментов"""
    def __init__(
        self,
        default_timeout: int = 300,
        max_concurrent_tools: int = 10,
        enable_logging: bool = True
    ):
        self.default_timeout = default_timeout
        self.max_concurrent_tools = max_concurrent_tools
        self.enable_logging = enable_logging


class ToolService:
    """
    Сервис для управления выполнением инструментов
    
    Обрабатывает:
    - Регистрацию инструментов
    - Проверку разрешений
    - Выполнение инструментов
    - Логирование и метрики
    """
    
    def __init__(self, config: Optional[ToolServiceConfig] = None):
        self.config = config or ToolServiceConfig()
        self.registry = ToolRegistry()
        self.permission_manager = PermissionManager()
        self._active_calls: Dict[str, ToolCall] = {}
        self._semaphore = asyncio.Semaphore(self.config.max_concurrent_tools)
    
    def register_tool(self, tool: BaseTool):
        """Зарегистрировать инструмент"""
        self.registry.register(tool)
    
    def unregister_tool(self, tool_name: str):
        """Удалить инструмент"""
        self.registry.unregister(tool_name)
    
    async def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        correlation_id: Optional[str] = None,
        user_callback: Optional[Callable] = None
    ) -> ToolOutput:
        """
        Выполнить инструмент с проверкой разрешений
        
        Args:
            tool_name: Имя инструмента
            arguments: Аргументы для инструмента
            correlation_id: Уникальный ID вызова
            user_callback: Callback для запроса разрешений у пользователя
        
        Returns:
            ToolOutput с результатом выполнения
        """
        correlation_id = correlation_id or str(uuid.uuid4())
        
        # Получение инструмента
        tool = self.registry.get(tool_name)
        if not tool:
            return ToolOutput(
                success=False,
                content="",
                error_message=f"Инструмент '{tool_name}' не найден"
            )
        
        # Создание запроса на разрешение
        request = PermissionRequest(
            tool_name=tool_name,
            arguments=arguments,
            correlation_id=correlation_id
        )
        
        # Проверка разрешения
        grant = await self.permission_manager.check_permission(request, user_callback)
        if not grant.granted:
            return ToolOutput(
                success=False,
                content="",
                error_message=f"Нет разрешения: {grant.reason}"
            )
        
        # Ограничение параллелизма
        async with self._semaphore:
            # Создание вызова
            input_data = ToolInput(
                name=tool_name,
                arguments=arguments,
                correlation_id=correlation_id
            )
            
            tool_call = ToolCall(
                tool_name=tool_name,
                input_data=input_data,
                status=ToolStatus.RUNNING
            )
            
            self._active_calls[correlation_id] = tool_call
            
            try:
                # Валидация входных данных
                if not tool.validate_input(input_data):
                    return ToolOutput(
                        success=False,
                        content="",
                        error_message="Некорректные входные данные"
                    )
                
                # Выполнение инструмента
                start_time = datetime.utcnow()
                output = await tool.execute(input_data)
                end_time = datetime.utcnow()
                
                # Обновление статистики
                tool_call.status = ToolStatus.SUCCESS if output.success else ToolStatus.ERROR
                tool_call.output = output
                tool_call.completed_at = end_time
                tool_call.execution_time_ms = int((end_time - start_time).total_seconds() * 1000)
                
                return output
                
            except Exception as e:
                tool_call.status = ToolStatus.ERROR
                tool_call.output = ToolOutput(
                    success=False,
                    content="",
                    error_message=str(e)
                )
                raise
                
            finally:
                # Очистка завершенных вызовов (можно добавить TTL)
                if correlation_id in self._active_calls:
                    del self._active_calls[correlation_id]
    
    def get_active_calls(self) -> List[ToolCall]:
        """Получить активные вызовы инструментов"""
        return list(self._active_calls.values())
    
    def cancel_call(self, correlation_id: str) -> bool:
        """Отменить вызов инструмента"""
        if correlation_id in self._active_calls:
            call = self._active_calls[correlation_id]
            call.status = ToolStatus.CANCELLED
            # TODO: Реализовать отмену через asyncio.CancelledError
            return True
        return False
    
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Получить список доступных инструментов со схемами"""
        tools = []
        for tool_name in self.registry.list_tools():
            tool = self.registry.get(tool_name)
            if tool:
                tools.append(tool.get_schema())
        return tools


__all__ = [
    "ToolService",
    "ToolServiceConfig"
]
