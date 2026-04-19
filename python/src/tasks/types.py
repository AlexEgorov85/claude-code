"""
Система управления задачами - типы и модели данных
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum
import uuid
from datetime import datetime


class TaskStatus(Enum):
    """Статус задачи"""
    PENDING = "pending"
    RUNNING = "running"
    WAITING_INPUT = "waiting_input"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskType(Enum):
    """Тип задачи"""
    LOCAL = "local"  # Локальный агент
    REMOTE = "remote"  # Удаленный агент
    BACKGROUND = "background"  # Фоновая задача
    SUBTASK = "subtask"  # Подзадача


@dataclass
class TaskProgress:
    """Прогресс выполнения задачи"""
    percentage: float = 0.0
    current_step: str = ""
    total_steps: int = 0
    completed_steps: int = 0
    message: Optional[str] = None


@dataclass
class TaskResult:
    """Результат выполнения задачи"""
    success: bool
    output: Any = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Task:
    """
    Задача - единица работы агента
    """
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task_type: TaskType = TaskType.LOCAL
    status: TaskStatus = TaskStatus.PENDING
    description: str = ""
    prompt: Optional[str] = None
    parent_task_id: Optional[str] = None
    subtasks: List[str] = field(default_factory=list)  # IDs подзадач
    
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    progress: TaskProgress = field(default_factory=TaskProgress)
    result: Optional[TaskResult] = None
    
    context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def start(self):
        """Начать выполнение задачи"""
        self.status = TaskStatus.RUNNING
        self.started_at = datetime.utcnow()
    
    def complete(self, result: TaskResult):
        """Завершить задачу успешно"""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.result = result
        self.progress.percentage = 100.0
    
    def fail(self, error_message: str):
        """Отметить задачу как неудачную"""
        self.status = TaskStatus.FAILED
        self.completed_at = datetime.utcnow()
        self.result = TaskResult(success=False, error_message=error_message)
    
    def cancel(self):
        """Отменить задачу"""
        self.status = TaskStatus.CANCELLED
        self.completed_at = datetime.utcnow()
    
    def update_progress(self, percentage: float, step: str = "", message: str = ""):
        """Обновить прогресс"""
        self.progress.percentage = percentage
        if step:
            self.progress.current_step = step
        if message:
            self.progress.message = message
    
    @property
    def is_finished(self) -> bool:
        return self.status in [
            TaskStatus.COMPLETED, 
            TaskStatus.FAILED, 
            TaskStatus.CANCELLED
        ]
    
    @property
    def duration_seconds(self) -> Optional[float]:
        """Получить длительность выполнения в секундах"""
        if not self.started_at:
            return None
        end_time = self.completed_at or datetime.utcnow()
        return (end_time - self.started_at).total_seconds()


__all__ = [
    "TaskStatus",
    "TaskType",
    "TaskProgress",
    "TaskResult",
    "Task"
]
