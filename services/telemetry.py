"""
Telemetry Service - сбор и отправка телеметрии
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class TelemetryEvent(Enum):
    """Типы телеметрических событий"""
    SESSION_START = "session_start"
    SESSION_END = "session_end"
    TOOL_CALL = "tool_call"
    TASK_CREATE = "task_create"
    TASK_COMPLETE = "task_complete"
    ERROR = "error"
    MODEL_REQUEST = "model_request"


@dataclass
class TelemetryData:
    """Данные телеметрии"""
    event_type: TelemetryEvent
    timestamp: datetime = field(default_factory=datetime.utcnow)
    session_id: str = ""
    properties: Dict[str, Any] = field(default_factory=dict)


class TelemetryClient:
    """
    Клиент телеметрии для сбора аналитики
    """
    
    _instance: Optional["TelemetryClient"] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._events: List[TelemetryData] = []
            cls._instance._enabled = False
            cls._instance._endpoint = None
        return cls._instance
    
    def configure(self, endpoint: str, enabled: bool = True):
        self._endpoint = endpoint
        self._enabled = enabled
    
    def track(self, event: TelemetryEvent, properties: Optional[Dict] = None, session_id: str = ""):
        """Записать событие"""
        if not self._enabled:
            return
        
        data = TelemetryData(
            event_type=event,
            session_id=session_id,
            properties=properties or {}
        )
        self._events.append(data)
        
        # В реальной реализации здесь будет отправка на сервер
    
    def flush(self):
        """Отправить накопленные события"""
        if not self._enabled or not self._events:
            return
        
        # Отправка событий
        self._events.clear()
    
    def get_events(self) -> List[TelemetryData]:
        return self._events.copy()


__all__ = ["TelemetryEvent", "TelemetryData", "TelemetryClient"]
