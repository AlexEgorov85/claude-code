"""
API Client Service - HTTP клиент для взаимодействия с внешними сервисами
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
import asyncio


@dataclass
class APIResponse:
    """Ответ от API"""
    status_code: int
    content: Any
    headers: Dict[str, str] = field(default_factory=dict)
    elapsed_ms: int = 0
    
    @property
    def is_success(self) -> bool:
        return 200 <= self.status_code < 300


class APIClient:
    """
    HTTP API клиент для взаимодействия с внешними сервисами
    """
    
    def __init__(self, base_url: str, api_key: Optional[str] = None):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self._session = None
        self._request_count = 0
    
    async def request(
        self,
        method: str,
        path: str,
        data: Optional[Dict] = None,
        headers: Optional[Dict] = None
    ) -> APIResponse:
        """Выполнить HTTP запрос"""
        # Здесь будет реализация через httpx/aiohttp
        # Пока заглушка
        await asyncio.sleep(0.01)
        
        self._request_count += 1
        
        return APIResponse(
            status_code=200,
            content={"status": "ok"},
            elapsed_ms=10
        )
    
    async def get(self, path: str, **kwargs) -> APIResponse:
        return await self.request("GET", path, **kwargs)
    
    async def post(self, path: str, data: Optional[Dict] = None, **kwargs) -> APIResponse:
        return await self.request("POST", path, data=data, **kwargs)
    
    async def put(self, path: str, data: Optional[Dict] = None, **kwargs) -> APIResponse:
        return await self.request("PUT", path, data=data, **kwargs)
    
    async def delete(self, path: str, **kwargs) -> APIResponse:
        return await self.request("DELETE", path, **kwargs)
    
    @property
    def request_count(self) -> int:
        return self._request_count


__all__ = ["APIResponse", "APIClient"]
