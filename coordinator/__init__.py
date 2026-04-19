"""
Координатор - оркестрация мульти-агентных сценариев и фоновых задач
"""

from .types import (
    CoordinatorMode,
    AgentRole,
    CoordinationTask,
    AgentState
)
from .manager import (
    MultiAgentCoordinator,
    BackgroundTaskManager
)

__all__ = [
    "CoordinatorMode",
    "AgentRole",
    "CoordinationTask",
    "AgentState",
    "MultiAgentCoordinator",
    "BackgroundTaskManager"
]
