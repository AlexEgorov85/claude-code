"""Concrete LLM client implementations."""
import json
import asyncio
from typing import AsyncIterator, List, Dict, Any, Optional
from .llm_client import (
    BaseLLMClient, LLMConfig, LLMMessage, LLMResponse, 
    StreamChunk, ToolCall, FinishReason, MessageRole
)


class MockLLMClient(BaseLLMClient):
    """Mock LLM client for testing."""
    
    def __init__(self, responses: Optional[List[LLMResponse]] = None):
        self.responses = responses or []
        self.response_index = 0
        self.call_count = 0
    
    async def chat(
        self,
        messages: List[LLMMessage],
        config: Optional[LLMConfig] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = None,
    ) -> LLMResponse:
        self.call_count += 1
        if self.response_index < len(self.responses):
            response = self.responses[self.response_index]
            self.response_index += 1
            return response
        return LLMResponse(content="Mock response", finish_reason=FinishReason.STOP)
    
    async def chat_stream(
        self,
        messages: List[LLMMessage],
        config: Optional[LLMConfig] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = None,
    ) -> AsyncIterator[StreamChunk]:
        self.call_count += 1
        if self.response_index < len(self.responses):
            response = self.responses[self.response_index]
            self.response_index += 1
            
            if response.content:
                yield StreamChunk(content=response.content)
            if response.tool_calls:
                yield StreamChunk(tool_calls=response.tool_calls)
            yield StreamChunk(finish_reason=response.finish_reason, is_complete=True)
        else:
            yield StreamChunk(content="Mock streaming response")
            yield StreamChunk(finish_reason=FinishReason.STOP, is_complete=True)
    
    async def estimate_tokens(self, messages: List[LLMMessage]) -> int:
        total = 0
        for msg in messages:
            if msg.content:
                total += len(msg.content.split()) * 1.3  # Rough estimate
            if msg.tool_calls:
                for tc in msg.tool_calls:
                    total += len(json.dumps(tc.arguments).split()) * 1.3
        return int(total)


class AnthropicLLMClient(BaseLLMClient):
    """Anthropic API client implementation."""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key
        self.base_url = base_url or "https://api.anthropic.com"
        self._client = None
    
    def _get_client(self):
        """Lazy load the anthropic client."""
        if self._client is None:
            try:
                import anthropic
                self._client = anthropic.AsyncAnthropic(api_key=self.api_key)
            except ImportError:
                raise ImportError("Please install anthropic: pip install anthropic")
        return self._client
    
    async def chat(
        self,
        messages: List[LLMMessage],
        config: Optional[LLMConfig] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = None,
    ) -> LLMResponse:
        client = self._get_client()
        config = config or LLMConfig()
        
        # Convert messages to Anthropic format
        system_prompt = config.system_prompt
        anthropic_messages = self._convert_messages(messages)
        
        kwargs = {
            "model": config.model,
            "max_tokens": config.max_tokens,
            "messages": anthropic_messages,
        }
        
        if system_prompt:
            kwargs["system"] = system_prompt
        
        if tools:
            kwargs["tools"] = tools
        
        if tool_choice:
            kwargs["tool_choice"] = {"type": tool_choice}
        
        if config.temperature is not None:
            kwargs["temperature"] = config.temperature
        
        if config.top_p is not None:
            kwargs["top_p"] = config.top_p
        
        response = await client.messages.create(**kwargs)
        
        # Parse response
        content = None
        tool_calls = []
        
        for block in response.content:
            if block.type == "text":
                content = block.text
            elif block.type == "tool_use":
                tool_calls.append(ToolCall(
                    id=block.id,
                    name=block.name,
                    arguments=block.input if isinstance(block.input, dict) else json.loads(block.input)
                ))
        
        finish_reason = FinishReason.STOP
        if response.stop_reason == "max_tokens":
            finish_reason = FinishReason.LENGTH
        elif response.stop_reason == "tool_use":
            finish_reason = FinishReason.TOOL_CALLS
        elif response.stop_reason == "end_turn":
            finish_reason = FinishReason.STOP
        
        usage = {
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
        }
        
        return LLMResponse(
            content=content,
            tool_calls=tool_calls if tool_calls else None,
            finish_reason=finish_reason,
            usage=usage,
            model=response.model
        )
    
    async def chat_stream(
        self,
        messages: List[LLMMessage],
        config: Optional[LLMConfig] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = None,
    ) -> AsyncIterator[StreamChunk]:
        client = self._get_client()
        config = config or LLMConfig()
        
        system_prompt = config.system_prompt
        anthropic_messages = self._convert_messages(messages)
        
        kwargs = {
            "model": config.model,
            "max_tokens": config.max_tokens,
            "messages": anthropic_messages,
        }
        
        if system_prompt:
            kwargs["system"] = system_prompt
        
        if tools:
            kwargs["tools"] = tools
        
        if tool_choice:
            kwargs["tool_choice"] = {"type": tool_choice}
        
        if config.temperature is not None:
            kwargs["temperature"] = config.temperature
        
        if config.top_p is not None:
            kwargs["top_p"] = config.top_p
        
        current_tool_call: Optional[Dict[str, Any]] = None
        current_tool_id: Optional[str] = None
        current_tool_name: Optional[str] = None
        current_tool_args: str = ""
        
        async with client.messages.stream(**kwargs) as stream:
            async for event in stream:
                if event.type == "content_block_start":
                    if event.content_block.type == "tool_use":
                        current_tool_id = event.content_block.id
                        current_tool_name = event.content_block.name
                        current_tool_args = ""
                
                elif event.type == "content_block_delta":
                    if event.delta.type == "text_delta":
                        yield StreamChunk(content=event.delta.text)
                    elif event.delta.type == "input_json_delta":
                        current_tool_args += event.delta.partial_json
                
                elif event.type == "content_block_stop":
                    if current_tool_id and current_tool_name:
                        try:
                            args = json.loads(current_tool_args) if current_tool_args else {}
                        except json.JSONDecodeError:
                            args = {}
                        yield StreamChunk(tool_calls=[ToolCall(
                            id=current_tool_id,
                            name=current_tool_name,
                            arguments=args
                        )])
                        current_tool_id = None
                        current_tool_name = None
                        current_tool_args = ""
                
                elif event.type == "message_delta":
                    finish_reason = FinishReason.STOP
                    if event.delta.stop_reason == "max_tokens":
                        finish_reason = FinishReason.LENGTH
                    elif event.delta.stop_reason == "tool_use":
                        finish_reason = FinishReason.TOOL_CALLS
                    
                    usage = None
                    if hasattr(event, 'usage') and event.usage:
                        usage = {
                            "output_tokens": getattr(event.usage, 'output_tokens', 0)
                        }
                    
                    yield StreamChunk(
                        finish_reason=finish_reason,
                        usage=usage,
                        is_complete=True
                    )
    
    def _convert_messages(self, messages: List[LLMMessage]) -> List[Dict[str, Any]]:
        """Convert internal messages to Anthropic format."""
        result = []
        for msg in messages:
            if msg.role == MessageRole.SYSTEM:
                continue  # System prompt is handled separately
            
            content = []
            if msg.content:
                content.append({"type": "text", "text": msg.content})
            
            if msg.tool_calls:
                for tc in msg.tool_calls:
                    content.append({
                        "type": "tool_use",
                        "id": tc.id,
                        "name": tc.name,
                        "input": tc.arguments
                    })
            
            if msg.tool_call_id:
                # This is a tool result message
                result.append({
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": msg.tool_call_id,
                            "content": msg.content or ""
                        }
                    ]
                })
            else:
                role = "assistant" if msg.role == MessageRole.ASSISTANT else "user"
                if content:
                    result.append({"role": role, "content": content})
                elif msg.role == MessageRole.ASSISTANT and msg.tool_calls:
                    result.append({"role": "assistant", "content": content})
        
        return result
    
    async def estimate_tokens(self, messages: List[LLMMessage]) -> int:
        """Estimate tokens using Anthropic's tokenizer if available."""
        try:
            import tiktoken
            encoding = tiktoken.get_encoding("cl100k_base")
            total = 0
            for msg in messages:
                if msg.content:
                    total += len(encoding.encode(msg.content))
                if msg.tool_calls:
                    for tc in msg.tool_calls:
                        total += len(encoding.encode(json.dumps(tc.arguments)))
            return total
        except ImportError:
            # Fallback to rough estimate
            total = 0
            for msg in messages:
                if msg.content:
                    total += len(msg.content.split()) * 1.3
            return int(total)
