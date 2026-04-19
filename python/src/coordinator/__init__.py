"""
Координатор - оркестрация мульти-агентных сценариев и фоновых задач
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Callable
from enum import Enum
import asyncio
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


class MultiAgentCoordinator:
    """
    Координатор для управления несколькими агентами
    """
    
    def __init__(self, mode: CoordinatorMode = CoordinatorMode.SINGLE):
        self.mode = mode
        self._agents: Dict[str, AgentState] = {}
        self._roles: Dict[str, AgentRole] = {}
        self._tasks: Dict[str, CoordinationTask] = {}
        self._task_queue: asyncio.Queue = asyncio.Queue()
        self._running = False
        self._workers: List[asyncio.Task] = []
    
    def register_role(self, role: AgentRole):
        """Зарегистрировать роль агента"""
        self._roles[role.role_id] = role
    
    def register_agent(self, agent_id: str, role_id: str) -> AgentState:
        """Зарегистрировать агента"""
        if role_id not in self._roles:
            raise ValueError(f"Role {role_id} not found")
        
        role = self._roles[role_id]
        agent = AgentState(agent_id=agent_id, role=role)
        self._agents[agent_id] = agent
        return agent
    
    def unregister_agent(self, agent_id: str):
        """Удалить агента"""
        if agent_id in self._agents:
            del self._agents[agent_id]
    
    async def create_task(
        self,
        description: str,
        role_id: Optional[str] = None,
        priority: int = 0,
        parent_id: Optional[str] = None
    ) -> CoordinationTask:
        """Создать задачу координации"""
        task = CoordinationTask(
            parent_id=parent_id,
            description=description,
            priority=priority
        )
        
        # Назначаем роль если указана
        if role_id:
            agent = self._find_available_agent(role_id)
            if agent:
                task.assigned_to = agent.agent_id
        
        self._tasks[task.task_id] = task
        await self._task_queue.put(task)
        
        return task
    
    def _find_available_agent(self, role_id: str) -> Optional[AgentState]:
        """Найти доступного агента с нужной ролью"""
        for agent in self._agents.values():
            if agent.role.role_id == role_id and agent.status == "idle":
                return agent
        return None
    
    async def start(self):
        """Запустить координатор"""
        if self._running:
            return
        
        self._running = True
        
        # Запускаем воркеров для обработки задач
        num_workers = len(self._agents) or 1
        for i in range(num_workers):
            worker = asyncio.create_task(self._worker(f"worker-{i}"))
            self._workers.append(worker)
    
    async def stop(self):
        """Остановить координатор"""
        self._running = False
        
        # Отменяем воркеров
        for worker in self._workers:
            worker.cancel()
        
        self._workers.clear()
    
    async def _worker(self, worker_id: str):
        """Воркер для обработки задач"""
        while self._running:
            try:
                task = await asyncio.wait_for(
                    self._task_queue.get(),
                    timeout=1.0
                )
                
                await self._process_task(task, worker_id)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"Worker {worker_id} error: {e}")
    
    async def _process_task(self, task: CoordinationTask, worker_id: str):
        """Обработать задачу"""
        task.start()
        
        try:
            # Здесь будет логика выполнения задачи через агента
            await asyncio.sleep(0.1)  # Симуляция работы
            
            task.complete({"result": "success", "worker": worker_id})
            
        except Exception as e:
            task.fail(str(e))
    
    def get_agent(self, agent_id: str) -> Optional[AgentState]:
        return self._agents.get(agent_id)
    
    def get_task(self, task_id: str) -> Optional[CoordinationTask]:
        return self._tasks.get(task_id)
    
    def list_agents(self, status: Optional[str] = None) -> List[AgentState]:
        agents = list(self._agents.values())
        if status:
            agents = [a for a in agents if a.status == status]
        return agents
    
    def list_tasks(self, status: Optional[str] = None) -> List[CoordinationTask]:
        tasks = list(self._tasks.values())
        if status:
            tasks = [t for t in tasks if t.status == status]
        return tasks
    
    def get_stats(self) -> Dict[str, Any]:
        """Получить статистику координатора"""
        return {
            "mode": self.mode.value,
            "total_agents": len(self._agents),
            "active_agents": len([a for a in self._agents.values() if a.status == "busy"]),
            "total_tasks": len(self._tasks),
            "pending_tasks": len([t for t in self._tasks.values() if t.status == "pending"]),
            "running_tasks": len([t for t in self._tasks.values() if t.status == "running"]),
            "completed_tasks": len([t for t in self._tasks.values() if t.status == "completed"]),
            "failed_tasks": len([t for t in self._tasks.values() if t.status == "failed"]),
            "queue_size": self._task_queue.qsize()
        }


class BackgroundTaskManager:
    """
    Менеджер фоновых задач
    """
    
    def __init__(self):
        self._tasks: Dict[str, asyncio.Task] = {}
        self._results: Dict[str, Any] = {}
        self._errors: Dict[str, str] = {}
    
    async def spawn(
        self,
        task_id: str,
        coro: Callable,
        *args,
        **kwargs
    ) -> asyncio.Task:
        """Запустить фоновую задачу"""
        if task_id in self._tasks:
            raise ValueError(f"Task {task_id} already exists")
        
        task = asyncio.create_task(coro(*args, **kwargs))
        self._tasks[task_id] = task
        
        # Добавляем callback для сохранения результата
        task.add_done_callback(
            lambda t: self._on_task_done(task_id, t)
        )
        
        return task
    
    def _on_task_done(self, task_id: str, task: asyncio.Task):
        """Callback при завершении задачи"""
        try:
            self._results[task_id] = task.result()
        except Exception as e:
            self._errors[task_id] = str(e)
        finally:
            if task_id in self._tasks:
                del self._tasks[task_id]
    
    def get_result(self, task_id: str) -> Optional[Any]:
        """Получить результат задачи"""
        return self._results.get(task_id)
    
    def get_error(self, task_id: str) -> Optional[str]:
        """Получить ошибку задачи"""
        return self._errors.get(task_id)
    
    def is_running(self, task_id: str) -> bool:
        """Проверить выполняется ли задача"""
        return task_id in self._tasks
    
    async def wait(self, task_id: str, timeout: Optional[float] = None) -> Any:
        """Дождаться завершения задачи"""
        if task_id not in self._tasks:
            if task_id in self._results:
                return self._results[task_id]
            if task_id in self._errors:
                raise Exception(self._errors[task_id])
            raise KeyError(f"Task {task_id} not found")
        
        task = self._tasks[task_id]
        return await asyncio.wait_for(task, timeout=timeout)
    
    def cancel(self, task_id: str) -> bool:
        """Отменить задачу"""
        if task_id in self._tasks:
            self._tasks[task_id].cancel()
            return True
        return False
    
    def list_running(self) -> List[str]:
        """Получить список выполняющихся задач"""
        return list(self._tasks.keys())


__all__ = [
    "CoordinatorMode",
    "AgentRole",
    "CoordinationTask",
    "AgentState",
    "MultiAgentCoordinator",
    "BackgroundTaskManager"
]
