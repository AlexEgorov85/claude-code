"""
Async utilities - асинхронные операции
"""

import asyncio
from typing import Callable, Any


async def async_sleep(seconds: float):
    """Асинхронная задержка"""
    await asyncio.sleep(seconds)


async def run_in_executor(func: Callable, *args, executor=None) -> Any:
    """Выполнить функцию в executor"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, func, *args)


__all__ = ["async_sleep", "run_in_executor"]
