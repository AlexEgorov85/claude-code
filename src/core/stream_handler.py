"""Исполнитель инструментов с поддержкой streaming."""
import asyncio
from typing import Optional, Any
from ..tools.base import BaseTool, ToolResult as BaseToolResult
from ..core.message_types import ToolCall, ToolResult


class StreamingToolExecutor:
    """Исполнитель инструментов с поддержкой потокового выполнения."""
    
    def __init__(self, tool_registry=None):
        from ..tools.registry import ToolRegistry
        self._registry = tool_registry or ToolRegistry()
        self._running_tasks: dict[str, asyncio.Task] = {}
    
    def set_registry(self, registry) -> None:
        """Установка реестра инструментов."""
        self._registry = registry
    
    async def execute(self, tool_call: ToolCall) -> ToolResult:
        """Выполнение одного вызова инструмента."""
        tool = self._registry.get_or_create(tool_call.name)
        
        if not tool:
            return ToolResult(
                tool_call_id=tool_call.id,
                content=None,
                is_error=True,
                error_message=f"Tool not found: {tool_call.name}"
            )
        
        # Валидация входных данных
        is_valid, error_msg = tool.validate_input(tool_call.input)
        if not is_valid:
            return ToolResult(
                tool_call_id=tool_call.id,
                content=None,
                is_error=True,
                error_message=error_msg
            )
        
        try:
            # Выполнение с таймаутом
            base_result = await tool.execute_with_timeout(**tool_call.input)
            
            return ToolResult(
                tool_call_id=tool_call.id,
                content=base_result.content,
                is_error=base_result.is_error,
                error_message=base_result.error_message
            )
        except Exception as e:
            return ToolResult(
                tool_call_id=tool_call.id,
                content=None,
                is_error=True,
                error_message=str(e)
            )
    
    async def execute_batch(
        self, 
        tool_calls: list[ToolCall],
        parallel: bool = True
    ) -> list[ToolResult]:
        """Выполнение нескольких вызовов инструментов."""
        if parallel:
            tasks = [self.execute(tc) for tc in tool_calls]
            return await asyncio.gather(*tasks)
        else:
            results = []
            for tc in tool_calls:
                result = await self.execute(tc)
                results.append(result)
            return results
    
    async def execute_with_progress(
        self,
        tool_call: ToolCall,
        progress_callback: Optional[callable] = None
    ) -> ToolResult:
        """Выполнение с колбэком прогресса."""
        tool = self._registry.get_or_create(tool_call.name)
        
        if not tool:
            return ToolResult(
                tool_call_id=tool_call.id,
                content=None,
                is_error=True,
                error_message=f"Tool not found: {tool_call.name}"
            )
        
        # Для инструментов с прогрессом
        if hasattr(tool, 'execute_with_progress'):
            async def progress_wrapper():
                async for progress_data in tool.execute_with_progress(**tool_call.input):
                    if progress_callback:
                        progress_callback(progress_data)
                    if 'result' in progress_data:
                        return progress_data['result']
                return None
            
            result = await progress_wrapper()
            if result:
                return result
        
        # Fallback к обычному выполнению
        return await self.execute(tool_call)
    
    def cancel(self, tool_call_id: str) -> bool:
        """Отмена выполнения инструмента."""
        if tool_call_id in self._running_tasks:
            task = self._running_tasks[tool_call_id]
            if not task.done():
                task.cancel()
                del self._running_tasks[tool_call_id]
                return True
        return False
    
    def cancel_all(self) -> int:
        """Отмена всех выполняющихся инструментов."""
        count = 0
        for tool_call_id in list(self._running_tasks.keys()):
            if self.cancel(tool_call_id):
                count += 1
        return count
    
    @property
    def running_count(self) -> int:
        """Количество выполняющихся инструментов."""
        return len(self._running_tasks)
