"""Основной цикл выполнения агента."""
import asyncio
from typing import Optional, AsyncGenerator, Callable, Any
from dataclasses import dataclass
from enum import Enum

from .message_types import (
    Message, UserMessage, AssistantMessage, ToolCall, 
    ToolResult, ToolUseMessage, ToolResultMessage
)
from .state import AgentState, TokenUsage


class AgentPhase(Enum):
    """Фазы агентского цикла."""
    THINK = "think"
    ACT = "act"
    OBSERVE = "observe"


@dataclass
class LoopEvent:
    """Событие в цикле агента."""
    phase: AgentPhase
    event_type: str
    data: Any = None
    timestamp: float = 0.0
    
    def __post_init__(self):
        import time
        self.timestamp = time.time()


class AgentLoop:
    """Основной цикл выполнения агента (Act-Think-Observe)."""
    
    def __init__(self, llm_client=None, tool_executor=None):
        self.llm_client = llm_client
        self.tool_executor = tool_executor
        self.state: Optional[AgentState] = None
        self._event_callbacks: list[Callable[[LoopEvent], None]] = []
        self._running = False
        self._paused = False
        self._max_iterations = 100
        self._current_iteration = 0
    
    def set_llm_client(self, client) -> None:
        """Установка LLM клиента."""
        self.llm_client = client
    
    def set_tool_executor(self, executor) -> None:
        """Установка исполнителя инструментов."""
        self.tool_executor = executor
    
    def add_event_callback(self, callback: Callable[[LoopEvent], None]) -> None:
        """Добавление обработчика событий."""
        self._event_callbacks.append(callback)
    
    def _emit_event(self, event: LoopEvent) -> None:
        """Эмиссия события."""
        for callback in self._event_callbacks:
            try:
                callback(event)
            except Exception:
                pass  # Игнорируем ошибки в колбэках
    
    async def run(
        self, 
        initial_message: str,
        state: Optional[AgentState] = None
    ) -> AsyncGenerator[LoopEvent, None]:
        """Запуск основного цикла агента."""
        self._running = True
        self._paused = False
        self._current_iteration = 0
        
        # Инициализация состояния
        if state is None:
            self.state = AgentState()
        else:
            self.state = state
        
        # Добавляем начальное сообщение
        user_msg = UserMessage(content=initial_message)
        self.state.add_message(user_msg)
        
        self._emit_event(LoopEvent(
            phase=AgentPhase.THINK,
            event_type="start",
            data={"message": initial_message}
        ))
        
        try:
            while self._running and self._current_iteration < self._max_iterations:
                if self._paused:
                    await asyncio.sleep(0.1)
                    continue
                
                self._current_iteration += 1
                
                # Фаза THINK: запрос к LLM
                think_events = await self._think_phase()
                async for event in think_events:
                    yield event
                
                # Проверка на завершение
                last_msg = self.state.get_last_message()
                if last_msg is None or not isinstance(last_msg, AssistantMessage):
                    break
                
                # Если есть вызовы инструментов - фаза ACT
                if last_msg.has_tool_calls():
                    act_events = await self._act_phase(last_msg.tool_calls)
                    async for event in act_events:
                        yield event
                    
                    # Фаза OBSERVE: обработка результатов
                    observe_events = await self._observe_phase()
                    async for event in observe_events:
                        yield event
                else:
                    # Нет вызовов инструментов - завершаем
                    self._emit_event(LoopEvent(
                        phase=AgentPhase.THINK,
                        event_type="complete",
                        data={"response": last_msg.content}
                    ))
                    break
            
            if self._current_iteration >= self._max_iterations:
                self._emit_event(LoopEvent(
                    phase=AgentPhase.THINK,
                    event_type="error",
                    data={"error": "Max iterations reached"}
                ))
                
        finally:
            self._running = False
            self._emit_event(LoopEvent(
                phase=AgentPhase.THINK,
                event_type="stop"
            ))
    
    async def _think_phase(self) -> AsyncGenerator[LoopEvent, None]:
        """Фаза THINK: получение ответа от LLM."""
        self._emit_event(LoopEvent(
            phase=AgentPhase.THINK,
            event_type="start"
        ))
        
        if not self.llm_client:
            raise RuntimeError("LLM client not set")
        
        # Получаем сообщения для LLM
        messages = self.state.get_messages_for_llm()
        
        # Запрос к LLM (с streaming)
        assistant_content = ""
        tool_calls = []
        
        try:
            async for chunk in self.llm_client.chat_completion_stream(messages):
                if "content" in chunk:
                    assistant_content += chunk["content"]
                    self._emit_event(LoopEvent(
                        phase=AgentPhase.THINK,
                        event_type="stream",
                        data={"content": chunk["content"]}
                    ))
                
                if "tool_calls" in chunk and chunk["tool_calls"]:
                    for tc in chunk["tool_calls"]:
                        tool_calls.append(ToolCall(
                            id=tc.get("id", ""),
                            name=tc.get("name", ""),
                            input=tc.get("input", {})
                        ))
            
            # Обновляем статистику токенов
            if hasattr(self.llm_client, 'last_usage'):
                usage = self.llm_client.last_usage
                self.state.update_token_usage(TokenUsage(
                    input_tokens=usage.get("input_tokens", 0),
                    output_tokens=usage.get("output_tokens", 0)
                ))
            
            # Создаем сообщение ассистента
            assistant_msg = AssistantMessage(
                content=assistant_content if assistant_content else None,
                tool_calls=tool_calls
            )
            self.state.add_message(assistant_msg)
            
            self._emit_event(LoopEvent(
                phase=AgentPhase.THINK,
                event_type="complete",
                data={
                    "content": assistant_content,
                    "tool_calls_count": len(tool_calls)
                }
            ))
            
        except Exception as e:
            self._emit_event(LoopEvent(
                phase=AgentPhase.THINK,
                event_type="error",
                data={"error": str(e)}
            ))
            raise
        
        yield LoopEvent(phase=AgentPhase.THINK, event_type="done")
    
    async def _act_phase(
        self, 
        tool_calls: list[ToolCall]
    ) -> AsyncGenerator[LoopEvent, None]:
        """Фаза ACT: выполнение инструментов."""
        self._emit_event(LoopEvent(
            phase=AgentPhase.ACT,
            event_type="start",
            data={"tool_calls_count": len(tool_calls)}
        ))
        
        if not self.tool_executor:
            raise RuntimeError("Tool executor not set")
        
        # Добавляем сообщения о использовании инструментов
        for tc in tool_calls:
            self.state.add_tool_call(tc)
            tool_use_msg = ToolUseMessage(tool_call=tc)
            self.state.add_message(tool_use_msg)
            
            self._emit_event(LoopEvent(
                phase=AgentPhase.ACT,
                event_type="tool_start",
                data={"tool_name": tc.name, "tool_id": tc.id}
            ))
        
        # Выполняем инструменты параллельно
        tasks = [
            self.tool_executor.execute(tc)
            for tc in tool_calls
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Обрабатываем результаты
        for tc, result in zip(tool_calls, results):
            if isinstance(result, Exception):
                tool_result = ToolResult(
                    tool_call_id=tc.id,
                    content=None,
                    is_error=True,
                    error_message=str(result)
                )
            else:
                tool_result = result
            
            self.state.add_tool_result(tool_result)
            
            tool_result_msg = ToolResultMessage(tool_result=tool_result)
            self.state.add_message(tool_result_msg)
            
            self._emit_event(LoopEvent(
                phase=AgentPhase.ACT,
                event_type="tool_complete",
                data={
                    "tool_name": tc.name,
                    "tool_id": tc.id,
                    "is_error": tool_result.is_error
                }
            ))
        
        self._emit_event(LoopEvent(
            phase=AgentPhase.ACT,
            event_type="complete"
        ))
        
        yield LoopEvent(phase=AgentPhase.ACT, event_type="done")
    
    async def _observe_phase(self) -> AsyncGenerator[LoopEvent, None]:
        """Фаза OBSERVE: подготовка к следующему циклу."""
        self._emit_event(LoopEvent(
            phase=AgentPhase.OBSERVE,
            event_type="start"
        ))
        
        # Здесь можно добавить логику анализа результатов
        # и принятия решения о продолжении
        
        self._emit_event(LoopEvent(
            phase=AgentPhase.OBSERVE,
            event_type="complete"
        ))
        
        yield LoopEvent(phase=AgentPhase.OBSERVE, event_type="done")
    
    def stop(self) -> None:
        """Остановка цикла."""
        self._running = False
    
    def pause(self) -> None:
        """Пауза цикла."""
        self._paused = True
    
    def resume(self) -> None:
        """Возобновление цикла."""
        self._paused = False
    
    @property
    def is_running(self) -> bool:
        """Проверка запущен ли цикл."""
        return self._running
    
    @property
    def current_iteration(self) -> int:
        """Текущая итерация."""
        return self._current_iteration
