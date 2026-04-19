"""Реестр инструментов."""
from typing import Optional, Type
from .base import BaseTool, ToolDefinition


class ToolRegistry:
    """Реестр для регистрации и поиска инструментов."""
    
    _instance: Optional["ToolRegistry"] = None
    
    def __new__(cls) -> "ToolRegistry":
        """Синглтон паттерн."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._tools: dict[str, BaseTool] = {}
            cls._instance._tool_classes: dict[str, Type[BaseTool]] = {}
        return cls._instance
    
    @classmethod
    def reset(cls) -> None:
        """Сброс реестра (для тестов)."""
        cls._instance = None
    
    def register(self, tool: BaseTool) -> None:
        """Регистрация инструмента."""
        self._tools[tool.name] = tool
        self._tool_classes[tool.name] = type(tool)
    
    def register_class(self, tool_class: Type[BaseTool]) -> None:
        """Регистрация класса инструмента."""
        # Создаем экземпляр для получения имени
        instance = tool_class()
        self._tool_classes[instance.name] = tool_class
    
    def get(self, name: str) -> Optional[BaseTool]:
        """Получение инструмента по имени."""
        return self._tools.get(name)
    
    def get_or_create(self, name: str) -> Optional[BaseTool]:
        """Получение или создание инструмента."""
        if name in self._tools:
            return self._tools[name]
        
        if name in self._tool_classes:
            tool = self._tool_classes[name]()
            self._tools[name] = tool
            return tool
        
        return None
    
    def list_tools(self, include_hidden: bool = False) -> list[ToolDefinition]:
        """Список всех зарегистрированных инструментов."""
        result = []
        for tool in self._tools.values():
            if not tool.is_hidden or include_hidden:
                result.append(tool.definition)
        return sorted(result, key=lambda x: x.name)
    
    def list_tool_names(self, include_hidden: bool = False) -> list[str]:
        """Список имен инструментов."""
        result = []
        for tool in self._tools.values():
            if not tool.is_hidden or include_hidden:
                result.append(tool.name)
        return sorted(result)
    
    def has_tool(self, name: str) -> bool:
        """Проверка наличия инструмента."""
        return name in self._tools or name in self._tool_classes
    
    def remove(self, name: str) -> bool:
        """Удаление инструмента."""
        if name in self._tools:
            del self._tools[name]
        if name in self._tool_classes:
            del self._tool_classes[name]
        return True
    
    def clear(self) -> None:
        """Очистка реестра."""
        self._tools.clear()
        self._tool_classes.clear()
    
    @property
    def count(self) -> int:
        """Количество зарегистрированных инструментов."""
        return len(self._tools)
    
    @property
    def count_total(self) -> int:
        """Общее количество (включая еще не созданные)."""
        return len(self._tool_classes)
