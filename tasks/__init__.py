"""
Система управления задачами (Task System)
Управление локальными и удаленными агентами, трекинг прогресса
"""

from .types import (
    TaskStatus,
    TaskType,
    TaskProgress,
    TaskResult,
    Task
)
from .manager import (
    TaskManager,
    AgentExecutor
)

__all__ = [
    "TaskStatus",
    "TaskType",
    "TaskProgress",
    "TaskResult",
    "Task",
    "TaskManager",
    "AgentExecutor"
]
