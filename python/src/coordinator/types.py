"""
Координатор - типы и модели данных
"""

from dataclasses import dataclass, field
from typing import Optional, Any, List
from enum import Enum
from datetime import datetime
import uuid


class CoordinatorMode(Enum):
    """Режимы работы координатора"""
    SINGLE = "single"  # Один агент
    MULTI = "multi"  # Несколько агентов
    HIERARCHICAL = "hierarchical"  # Иерархическая структура
    SWARM = "swarm"  # Роевой интеллект


@dataclass
class AgentRole:
    """Роль агента в системе"""
    role_id: str
    name: str
    description: str
    capabilities: List[str] = field(default_factory=list)
    max_concurrent_tasks: int = 5
    is_active: bool = True


@dataclass
class CoordinationTask:
    """Задача координации"""
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    parent_id: Optional[str] = None
    assigned_to: Optional[str] = None  # ID агента
    status: str = "pending"
    description: str = ""
    priority: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    
    def start(self):
        self.status = "running"
        self.started_at = datetime.utcnow()
    
    def complete(self, result: Any):
        self.status = "completed"
        self.completed_at = datetime.utcnow()
        self.result = result
    
    def fail(self, error: str):
        self.status = "failed"
        self.completed_at = datetime.utcnow()
        self.error = error


@dataclass
class AgentState:
    """Состояние агента"""
    agent_id: str
    role: AgentRole
    status: str = "idle"  # idle, busy, offline
    current_task: Optional[str] = None
    tasks_completed: int = 0
    last_activity: datetime = field(default_factory=datetime.utcnow)


__all__ = [
    "CoordinatorMode",
    "AgentRole",
    "CoordinationTask",
    "AgentState"
]
