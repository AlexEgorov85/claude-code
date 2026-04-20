"""LLM Client & API Integration module."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import AsyncIterator, Optional, List, Dict, Any, Union
from enum import Enum
import json


class MessageRole(str, Enum):
    """Role of a message in the conversation."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class FinishReason(str, Enum):
    """Reason why the model finished generating."""
    STOP = "stop"
    LENGTH = "length"
    TOOL_CALLS = "tool_calls"
    CONTENT_FILTER = "content_filter"
    ERROR = "error"


@dataclass
class ToolCall:
    """Represents a tool call from the model."""
    id: str
    name: str
    arguments: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": "function",
            "function": {
                "name": self.name,
                "arguments": json.dumps(self.arguments)
            }
        }


@dataclass
class LLMMessage:
    """A message in the conversation."""
    role: MessageRole
    content: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None
    tool_call_id: Optional[str] = None
    name: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {"role": self.role.value}
        
        if self.content is not None:
            result["content"] = self.content
        
        if self.tool_calls:
            result["tool_calls"] = [tc.to_dict() for tc in self.tool_calls]
        
        if self.tool_call_id:
            result["tool_call_id"] = self.tool_call_id
        
        if self.name:
            result["name"] = self.name
        
        return result


@dataclass
class LLMResponse:
    """Response from the LLM."""
    content: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None
    finish_reason: Optional[FinishReason] = None
    usage: Optional[Dict[str, int]] = None
    model: Optional[str] = None
    
    @property
    def has_tool_calls(self) -> bool:
        return bool(self.tool_calls)
    
    @property
    def is_finished(self) -> bool:
        return self.finish_reason in (FinishReason.STOP, FinishReason.TOOL_CALLS, FinishReason.LENGTH)


@dataclass
class StreamChunk:
    """A chunk of streaming response."""
    content: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None
    finish_reason: Optional[FinishReason] = None
    usage: Optional[Dict[str, int]] = None
    is_complete: bool = False


@dataclass
class LLMConfig:
    """Configuration for LLM client."""
    model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 8192
    temperature: float = 0.7
    top_p: float = 1.0
    stop_sequences: Optional[List[str]] = None
    system_prompt: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    timeout: int = 300


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients."""
    
    @abstractmethod
    async def chat(
        self,
        messages: List[LLMMessage],
        config: Optional[LLMConfig] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = None,
    ) -> LLMResponse:
        """Send a chat request and get a response."""
        pass
    
    @abstractmethod
    async def chat_stream(
        self,
        messages: List[LLMMessage],
        config: Optional[LLMConfig] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = None,
    ) -> AsyncIterator[StreamChunk]:
        """Send a chat request and stream the response."""
        pass
    
    @abstractmethod
    async def estimate_tokens(self, messages: List[LLMMessage]) -> int:
        """Estimate the number of tokens in the messages."""
        pass


@dataclass
class TokenUsage:
    """Track token usage."""
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0
    total_tokens: int = 0
    
    @property
    def cost(self) -> float:
        """Calculate cost based on token usage (placeholder rates)."""
        # These are example rates, should be configurable
        input_rate = 0.000003  # $3 per 1M input tokens
        output_rate = 0.000015  # $15 per 1M output tokens
        return (self.input_tokens * input_rate) + (self.output_tokens * output_rate)
    
    def add(self, usage: Dict[str, int]) -> None:
        """Add usage from API response."""
        if "input_tokens" in usage or "prompt_tokens" in usage:
            self.input_tokens += usage.get("input_tokens", usage.get("prompt_tokens", 0))
        if "output_tokens" in usage or "completion_tokens" in usage:
            self.output_tokens += usage.get("output_tokens", usage.get("completion_tokens", 0))
        if "cache_read_tokens" in usage:
            self.cache_read_tokens += usage["cache_read_tokens"]
        if "cache_write_tokens" in usage:
            self.cache_write_tokens += usage["cache_write_tokens"]
        self.total_tokens = self.input_tokens + self.output_tokens


class CostTracker:
    """Track costs across multiple requests."""
    
    def __init__(self):
        self.sessions: Dict[str, TokenUsage] = {}
        self.total_usage = TokenUsage()
    
    def record_usage(self, session_id: str, usage: Dict[str, int]) -> TokenUsage:
        """Record usage for a session."""
        if session_id not in self.sessions:
            self.sessions[session_id] = TokenUsage()
        
        session_usage = self.sessions[session_id]
        session_usage.add(usage)
        self.total_usage.add(usage)
        
        return session_usage
    
    def get_session_cost(self, session_id: str) -> float:
        """Get cost for a specific session."""
        if session_id in self.sessions:
            return self.sessions[session_id].cost
        return 0.0
    
    def get_total_cost(self) -> float:
        """Get total cost across all sessions."""
        return self.total_usage.cost
    
    def reset_session(self, session_id: str) -> None:
        """Reset usage for a session."""
        if session_id in self.sessions:
            del self.sessions[session_id]
    
    def reset_all(self) -> None:
        """Reset all usage tracking."""
        self.sessions.clear()
        self.total_usage = TokenUsage()
