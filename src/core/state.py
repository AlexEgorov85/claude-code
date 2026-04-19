"""Менеджер состояния агента."""
from dataclasses import dataclass, field
from typing import Optional, Any
from .message_types import Message, ToolCall, ToolResult
import uuid
import time


@dataclass
class TokenUsage:
    """Использование токенов."""
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0
    
    @property
    def total_tokens(self) -> int:
        """Общее количество токенов."""
        return self.input_tokens + self.output_tokens + self.cache_read_tokens + self.cache_write_tokens
    
    def add(self, other: "TokenUsage") -> None:
        """Добавление использования токенов."""
        self.input_tokens += other.input_tokens
        self.output_tokens += other.output_tokens
        self.cache_read_tokens += other.cache_read_tokens
        self.cache_write_tokens += other.cache_write_tokens


@dataclass
class CostInfo:
    """Информация о стоимости."""
    total_cost: float = 0.0
    input_cost: float = 0.0
    output_cost: float = 0.0
    cache_read_cost: float = 0.0
    cache_write_cost: float = 0.0
    
    def add_cost(self, cost: float, cost_type: str = "total") -> None:
        """Добавление стоимости."""
        if cost_type == "total":
            self.total_cost += cost
        elif cost_type == "input":
            self.input_cost += cost
            self.total_cost += cost
        elif cost_type == "output":
            self.output_cost += cost
            self.total_cost += cost
        elif cost_type == "cache_read":
            self.cache_read_cost += cost
            self.total_cost += cost
        elif cost_type == "cache_write":
            self.cache_write_cost += cost
            self.total_cost += cost


@dataclass
class AgentState:
    """Состояние агента."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    messages: list[Message] = field(default_factory=list)
    pending_tool_calls: list[ToolCall] = field(default_factory=list)
    pending_tool_results: list[ToolResult] = field(default_factory=list)
    token_usage: TokenUsage = field(default_factory=TokenUsage)
    cost_info: CostInfo = field(default_factory=CostInfo)
    current_task: Optional[str] = None
    is_running: bool = False
    is_paused: bool = False
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def add_message(self, message: Message) -> None:
        """Добавление сообщения."""
        self.messages.append(message)
        self.updated_at = time.time()
    
    def get_last_message(self) -> Optional[Message]:
        """Получение последнего сообщения."""
        return self.messages[-1] if self.messages else None
    
    def get_messages_for_llm(self) -> list[dict]:
        """Получение сообщений для отправки в LLM."""
        result = []
        for msg in self.messages:
            if msg.role.value == "user":
                result.append({"role": "user", "content": msg.content})
            elif msg.role.value == "assistant":
                assistant_msg = {"role": "assistant", "content": msg.content}
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    assistant_msg["tool_calls"] = [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.name,
                                "arguments": str(tc.input)
                            }
                        }
                        for tc in msg.tool_calls
                    ]
                result.append(assistant_msg)
            elif msg.role.value == "system":
                result.append({"role": "system", "content": msg.content})
            elif msg.role.value == "tool_result":
                tool_result_msg = {
                    "role": "tool",
                    "tool_call_id": msg.content.get("tool_call_id"),
                    "content": str(msg.content.get("content", ""))
                }
                if msg.content.get("is_error"):
                    tool_result_msg["content"] = f"Error: {msg.content.get('error_message', 'Unknown error')}"
                result.append(tool_result_msg)
        return result
    
    def add_tool_call(self, tool_call: ToolCall) -> None:
        """Добавление вызова инструмента."""
        self.pending_tool_calls.append(tool_call)
        self.updated_at = time.time()
    
    def add_tool_result(self, tool_result: ToolResult) -> None:
        """Добавление результата инструмента."""
        self.pending_tool_results.append(tool_result)
        # Удаляем соответствующий tool_call
        self.pending_tool_calls = [
            tc for tc in self.pending_tool_calls 
            if tc.id != tool_result.tool_call_id
        ]
        self.updated_at = time.time()
    
    def has_pending_tool_calls(self) -> bool:
        """Проверка наличия ожидающих вызовов инструментов."""
        return len(self.pending_tool_calls) > 0
    
    def clear_pending_tools(self) -> None:
        """Очистка ожидающих инструментов."""
        self.pending_tool_calls.clear()
        self.pending_tool_results.clear()
    
    def update_token_usage(self, usage: TokenUsage) -> None:
        """Обновление использования токенов."""
        self.token_usage.add(usage)
        self.updated_at = time.time()
    
    def update_cost(self, cost: float, cost_type: str = "total") -> None:
        """Обновление стоимости."""
        self.cost_info.add_cost(cost, cost_type)
        self.updated_at = time.time()
    
    def to_dict(self) -> dict:
        """Конвертация в словарь."""
        return {
            "id": self.id,
            "messages": [msg.to_dict() for msg in self.messages],
            "pending_tool_calls": [
                {"id": tc.id, "name": tc.name, "input": tc.input}
                for tc in self.pending_tool_calls
            ],
            "token_usage": {
                "input_tokens": self.token_usage.input_tokens,
                "output_tokens": self.token_usage.output_tokens,
                "total_tokens": self.token_usage.total_tokens
            },
            "cost_info": {
                "total_cost": self.cost_info.total_cost
            },
            "current_task": self.current_task,
            "is_running": self.is_running,
            "is_paused": self.is_paused,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": self.metadata
        }
