"""
Logging utilities - настройка логгирования
"""

import sys
import logging
from typing import Optional


def setup_logger(
    name: str,
    level: int = logging.INFO,
    format_string: Optional[str] = None
) -> logging.Logger:
    """Настроить логгер"""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        
        fmt = format_string or "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        formatter = logging.Formatter(fmt)
        handler.setFormatter(formatter)
        
        logger.addHandler(handler)
    
    return logger


__all__ = ["setup_logger"]
