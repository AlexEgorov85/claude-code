"""
Менеджер разрешений для инструментов
"""

from typing import Dict, Optional, Set, Callable, Any
from dataclasses import dataclass

from .types import ToolPermission, PermissionType, ToolInput


@dataclass
class PermissionRequest:
    """Запрос разрешения на выполнение инструмента"""
    tool_name: str
    arguments: Dict[str, Any]
    correlation_id: str
    
    def __str__(self):
        args_preview = ", ".join(f"{k}={v}" for k, v in list(self.arguments.items())[:3])
        return f"{self.tool_name}({args_preview})"


@dataclass 
class PermissionGrant:
    """Результат предоставления разрешения"""
    granted: bool
    reason: Optional[str] = None
    one_time: bool = False  # Одноразовое разрешение


class PermissionManager:
    """
    Менеджер разрешений для инструментов
    """
    
    _instance: Optional["PermissionManager"] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._permissions: Dict[str, ToolPermission] = {}
            cls._instance._granted_once: Set[str] = set()
        return cls._instance
    
    def set_permission(self, permission: ToolPermission):
        """Установить разрешение для инструмента"""
        self._permissions[permission.tool_name] = permission
    
    def get_permission(self, tool_name: str) -> Optional[ToolPermission]:
        """Получить разрешение для инструмента"""
        return self._permissions.get(tool_name)
    
    async def check_permission(
        self, 
        request: PermissionRequest,
        user_callback: Optional[Callable] = None
    ) -> PermissionGrant:
        """
        Проверить разрешение на выполнение инструмента
        
        Args:
            request: Запрос разрешения
            user_callback: Callback для запроса у пользователя (async функция)
        
        Returns:
            PermissionGrant с результатом проверки
        """
        permission = self.get_permission(request.tool_name)
        
        # Если разрешения нет - спрашиваем пользователя
        if permission is None:
            if user_callback:
                granted = await user_callback(request)
                if granted:
                    self._granted_once.add(request.correlation_id)
                return PermissionGrant(granted=granted)
            return PermissionGrant(granted=False, reason="No permission configured")
        
        # Проверяем тип разрешения
        if permission.permission_type == PermissionType.DENY:
            return PermissionGrant(granted=False, reason="Permission denied by policy")
        
        if permission.permission_type == PermissionType.ALWAYS_ALLOW:
            return PermissionGrant(granted=True)
        
        if permission.permission_type == PermissionType.ASK_USER:
            # Проверяем паттерны
            if self._matches_patterns(request, permission.patterns):
                if user_callback:
                    granted = await user_callback(request)
                    return PermissionGrant(granted=granted)
                return PermissionGrant(granted=False, reason="User confirmation required")
            return PermissionGrant(granted=False, reason="Arguments do not match allowed patterns")
        
        return PermissionGrant(granted=False, reason="Unknown permission type")
    
    def _matches_patterns(self, request: PermissionRequest, patterns: list) -> bool:
        """Проверить соответствие аргументов паттернам"""
        if not patterns:
            return True
        
        for pattern in patterns:
            if self._match_pattern(request.arguments, pattern):
                return True
        return False
    
    def _match_pattern(self, args: Dict[str, Any], pattern: str) -> bool:
        """Простая проверка паттерна (можно расширить до regex/glob)"""
        # Пример: "command=ls*" или "path=/safe/*"
        for key, value in args.items():
            pattern_parts = pattern.split("=", 1)
            if len(pattern_parts) == 2:
                p_key, p_value = pattern_parts
                if p_key == key:
                    if p_value.endswith("*"):
                        if str(value).startswith(p_value[:-1]):
                            return True
                    elif str(value) == p_value:
                        return True
        return True
    
    def grant_once(self, correlation_id: str):
        """Предоставить одноразовое разрешение"""
        self._granted_once.add(correlation_id)
    
    def is_granted_once(self, correlation_id: str) -> bool:
        """Проверить наличие одноразового разрешения"""
        return correlation_id in self._granted_once
    
    def clear_once(self, correlation_id: str):
        """Удалить одноразовое разрешение"""
        self._granted_once.discard(correlation_id)
    
    def reset(self):
        """Сбросить все разрешения"""
        self._permissions.clear()
        self._granted_once.clear()


__all__ = ["PermissionManager", "PermissionRequest", "PermissionGrant"]
