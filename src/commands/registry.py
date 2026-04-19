"""Реестр команд."""
from typing import Optional, Type
from .base import BaseCommand, CommandDefinition, CommandResult


class CommandRegistry:
    """Реестр для регистрации и поиска команд."""
    
    _instance: Optional["CommandRegistry"] = None
    
    def __new__(cls) -> "CommandRegistry":
        """Синглтон паттерн."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._commands: dict[str, BaseCommand] = {}
            cls._instance._command_classes: dict[str, Type[BaseCommand]] = {}
            cls._instance._aliases: dict[str, str] = {}  # alias -> command_name
        return cls._instance
    
    @classmethod
    def reset(cls) -> None:
        """Сброс реестра (для тестов)."""
        cls._instance = None
    
    def register(self, command: BaseCommand) -> None:
        """Регистрация команды."""
        self._commands[command.name] = command
        self._command_classes[command.name] = type(command)
        
        # Регистрируем псевдонимы
        for alias in command.aliases:
            self._aliases[alias.lower()] = command.name
    
    def register_class(self, command_class: Type[BaseCommand]) -> None:
        """Регистрация класса команды."""
        instance = command_class()
        self.register(instance)
    
    def get(self, name: str) -> Optional[BaseCommand]:
        """Получение команды по имени или псевдониму."""
        # Проверяем псевдонимы
        actual_name = self._aliases.get(name.lower(), name)
        
        if actual_name in self._commands:
            return self._commands[actual_name]
        
        if actual_name in self._command_classes:
            command = self._command_classes[actual_name]()
            self._commands[actual_name] = command
            return command
        
        return None
    
    def list_commands(self, include_hidden: bool = False) -> list[CommandDefinition]:
        """Список всех зарегистрированных команд."""
        result = []
        for command in self._commands.values():
            if not command.is_hidden or include_hidden:
                result.append(command.definition)
        return sorted(result, key=lambda x: (x.category, x.name))
    
    def list_command_names(self, include_hidden: bool = False) -> list[str]:
        """Список имен команд."""
        result = []
        for command in self._commands.values():
            if not command.is_hidden or include_hidden:
                result.append(command.name)
        return sorted(result)
    
    def has_command(self, name: str) -> bool:
        """Проверка наличия команды."""
        actual_name = self._aliases.get(name.lower(), name)
        return actual_name in self._commands or actual_name in self._command_classes
    
    def remove(self, name: str) -> bool:
        """Удаление команды."""
        actual_name = self._aliases.get(name.lower(), name)
        
        if actual_name in self._commands:
            del self._commands[actual_name]
        if actual_name in self._command_classes:
            del self._command_classes[actual_name]
        
        # Удаляем псевдонимы
        aliases_to_remove = [k for k, v in self._aliases.items() if v == actual_name]
        for alias in aliases_to_remove:
            del self._aliases[alias]
        
        return True
    
    def clear(self) -> None:
        """Очистка реестра."""
        self._commands.clear()
        self._command_classes.clear()
        self._aliases.clear()
    
    @property
    def count(self) -> int:
        """Количество зарегистрированных команд."""
        return len(self._commands)
    
    @property
    def count_total(self) -> int:
        """Общее количество (включая еще не созданные)."""
        return len(self._command_classes)
    
    def get_categories(self) -> list[str]:
        """Получение списка категорий."""
        categories = set()
        for command in self._commands.values():
            categories.add(command.category)
        return sorted(categories)
    
    def get_commands_by_category(self, category: str) -> list[CommandDefinition]:
        """Получение команд по категории."""
        result = []
        for command in self._commands.values():
            if command.category == category and not command.is_hidden:
                result.append(command.definition)
        return sorted(result, key=lambda x: x.name)
