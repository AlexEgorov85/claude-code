"""
Decorators - декораторы для повторных попыток и замера времени
"""

import functools
import time
import asyncio
import logging
from typing import Optional, Callable, Tuple


def retry(max_attempts: int = 3, delay: float = 1.0, exceptions: Tuple = (Exception,)):
    """Декоратор для повторных попыток"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay * (attempt + 1))
            raise last_exception
        return wrapper
    return decorator


def timing(logger: Optional[logging.Logger] = None):
    """Декоратор для замера времени выполнения"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            start = time.time()
            try:
                return await func(*args, **kwargs)
            finally:
                elapsed = time.time() - start
                if logger:
                    logger.debug(f"{func.__name__} took {elapsed:.3f}s")
                else:
                    print(f"{func.__name__} took {elapsed:.3f}s")
        return wrapper
    return decorator


__all__ = ["retry", "timing"]
