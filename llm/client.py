"""
Асинхронный клиент для взаимодействия с Anthropic API.
Обрабатывает запросы, потоковую передачу и ошибки.
"""
import asyncio
import os
from typing import AsyncGenerator, List, Dict, Any, Optional
from dataclasses import dataclass
import httpx

@dataclass
class Message:
    role: str  # "user" или "assistant"
    content: str

@dataclass
class LLMResponse:
    text: str
    stop_reason: Optional[str] = None
    usage: Optional[Dict[str, int]] = None

class AnthropicClient:
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.anthropic.com/v1"
        self.headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }

    async def chat(
        self, 
        messages: List[Message], 
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
        stream: bool = False
    ) -> LLMResponse | AsyncGenerator[str, None]:
        """
        Отправляет запрос к API.
        Если stream=True, возвращает генератор для потоковой передачи.
        """
        payload = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": [
                {"role": msg.role, "content": msg.content} 
                for msg in messages
            ]
        }
        
        if system_prompt:
            payload["system"] = system_prompt

        if stream:
            return self._stream_request(payload)
        else:
            return await self._single_request(payload)

    async def _single_request(self, payload: dict) -> LLMResponse:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/messages",
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            
            return LLMResponse(
                text=data["content"][0]["text"],
                stop_reason=data.get("stop_reason"),
                usage=data.get("usage")
            )

    async def _stream_request(self, payload: dict) -> AsyncGenerator[str, None]:
        payload["stream"] = True
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/messages",
                headers=self.headers,
                json=payload
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str == "[DONE]":
                            break
                        try:
                            import json
                            data = json.loads(data_str)
                            if data["type"] == "content_block_delta":
                                yield data["delta"]["text"]
                        except json.JSONDecodeError:
                            continue
