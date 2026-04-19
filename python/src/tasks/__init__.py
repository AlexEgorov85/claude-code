"""
Система управления задачами (Task System)
Управление локальными и удаленными агентами, трекинг прогресса
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Callable
from enum import Enum
import uuid
from datetime import datetime
import asyncio


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


class TaskManager:
    """
    Менеджер задач - управление жизненным циклом задач
    """
    
    _instance: Optional["TaskManager"] = None
    _tasks: Dict[str, Task]
    _listeners: List[Callable[[Task], None]]
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._tasks = {}
            cls._instance._listeners = []
        return cls._instance
    
    def create_task(
        self, 
        task_type: TaskType, 
        description: str,
        prompt: Optional[str] = None,
        parent_task_id: Optional[str] = None,
        context: Optional[Dict] = None
    ) -> Task:
        """Создать новую задачу"""
        task = Task(
            task_type=task_type,
            description=description,
            prompt=prompt,
            parent_task_id=parent_task_id,
            context=context or {}
        )
        
        self._tasks[task.task_id] = task
        
        # Добавить как подзадачу родителю
        if parent_task_id and parent_task_id in self._tasks:
            self._tasks[parent_task_id].subtasks.append(task.task_id)
        
        self._notify_listeners(task)
        return task
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Получить задачу по ID"""
        return self._tasks.get(task_id)
    
    def list_tasks(self, status: Optional[TaskStatus] = None) -> List[Task]:
        """Получить список задач с фильтрацией по статусу"""
        tasks = list(self._tasks.values())
        if status:
            tasks = [t for t in tasks if t.status == status]
        return tasks
    
    def get_active_tasks(self) -> List[Task]:
        """Получить активные задачи"""
        return [t for t in self._tasks.values() if not t.is_finished]
    
    def add_listener(self, callback: Callable[[Task], None]):
        """Добавить слушатель изменений задач"""
        self._listeners.append(callback)
    
    def remove_listener(self, callback: Callable[[Task], None]):
        """Удалить слушателя"""
        if callback in self._listeners:
            self._listeners.remove(callback)
    
    def _notify_listeners(self, task: Task):
        """Уведомить слушателей об изменении задачи"""
        for listener in self._listeners:
            try:
                listener(task)
            except Exception:
                pass  # Игнорируем ошибки в слушателях
    
    def clear_completed(self, older_than_seconds: Optional[int] = None):
        """Очистить завершенные задачи"""
        now = datetime.utcnow()
        to_remove = []
        
        for task_id, task in self._tasks.items():
            if task.is_finished:
                if older_than_seconds and task.completed_at:
                    age = (now - task.completed_at).total_seconds()
                    if age < older_than_seconds:
                        continue
                to_remove.append(task_id)
        
        for task_id in to_remove:
            del self._tasks[task_id]
    
    def clear(self):
        """Очистить все задачи"""
        self._tasks.clear()


class AgentExecutor:
    """
    Исполнитель агентов - выполнение задач агентами
    """
    
    def __init__(self, task_manager: Optional[TaskManager] = None):
        self.task_manager = task_manager or TaskManager()
        self._running = False
    
    async def execute_task(self, task: Task, agent_core: Any) -> TaskResult:
        """
        Выполнить задачу с помощью агента
        
        Args:
            task: Задача для выполнения
            agent_core: Экземпляр AgentCore для выполнения
        
        Returns:
            Результат выполнения
        """
        if task.is_finished:
            return task.result or TaskResult(
                success=False, 
                error_message="Task already finished"
            )
        
        task.start()
        self._running = True
        
        try:
            # Здесь будет логика выполнения через агент
            # Пока заглушка
            await asyncio.sleep(0.1)
            
            result = TaskResult(
                success=True,
                output={"message": "Task executed"},
                metadata={"executor": "AgentExecutor"}
            )
            
            task.complete(result)
            return result
            
        except Exception as e:
            result = TaskResult(
                success=False,
                error_message=str(e)
            )
            task.fail(str(e))
            return result
            
        finally:
            self._running = False
    
    async def cancel_task(self, task: Task):
        """Отменить задачу"""
        task.cancel()
        self._running = False


__all__ = [
    "TaskStatus",
    "TaskType",
    "TaskProgress",
    "TaskResult",
    "Task",
    "TaskManager",
    "AgentExecutor"
]
