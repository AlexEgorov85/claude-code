"""Базовый класс для команд."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional, Callable
import asyncio


@dataclass
class CommandDefinition:
    """Определение команды."""
    name: str
    description: str
    usage: str = ""
    examples: list[str] = field(default_factory=list)
    aliases: list[str] = field(default_factory=list)
    is_hidden: bool = False
    requires_confirmation: bool = False
    category: str = "general"


@dataclass
class CommandResult:
    """Результат выполнения команды."""
    success: bool
    output: Any = None
    error_message: Optional[str] = None
    exit_code: int = 0


class BaseCommand(ABC):
    """Базовый класс для всех команд."""
    
    def __init__(self):
        self._definition: Optional[CommandDefinition] = None
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Название команды."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Описание команды."""
        pass
    
    @property
    def usage(self) -> str:
        """Использование команды."""
        return f"{self.name} [arguments]"
    
    @property
    def examples(self) -> list[str]:
        """Примеры использования."""
        return []
    
    @property
    def aliases(self) -> list[str]:
        """Псевдонимы команды."""
        return []
    
    @property
    def is_hidden(self) -> bool:
        """Скрыта ли команда."""
        return False
    
    @property
    def requires_confirmation(self) -> bool:
        """Требует ли подтверждения."""
        return False
    
    @property
    def category(self) -> str:
        """Категория команды."""
        return "general"
    
    @property
    def definition(self) -> CommandDefinition:
        """Получение определения команды."""
        if not self._definition:
            self._definition = CommandDefinition(
                name=self.name,
                description=self.description,
                usage=self.usage,
                examples=self.examples,
                aliases=self.aliases,
                is_hidden=self.is_hidden,
                requires_confirmation=self.requires_confirmation,
                category=self.category
            )
        return self._definition
    
    @abstractmethod
    async def execute(self, args: list[str], context: dict[str, Any]) -> CommandResult:
        """Выполнение команды."""
        pass
    
    def parse_args(self, args: list[str]) -> dict[str, Any]:
        """Парсинг аргументов команды."""
        # Простая реализация - можно переопределить в наследниках
        result = {}
        i = 0
        while i < len(args):
            arg = args[i]
            if arg.startswith("--"):
                key = arg[2:]
                if i + 1 < len(args) and not args[i + 1].startswith("--"):
                    result[key] = args[i + 1]
                    i += 2
                else:
                    result[key] = True
                    i += 1
            elif arg.startswith("-") and len(arg) > 1:
                # Короткие флаги
                for char in arg[1:]:
                    result[char] = True
                i += 1
            else:
                # Позиционные аргументы
                if "positional" not in result:
                    result["positional"] = []
                result["positional"].append(arg)
                i += 1
        return result
    
    async def execute_with_timeout(
        self, 
        args: list[str], 
        context: dict[str, Any],
        timeout: float = 30.0
    ) -> CommandResult:
        """Выполнение с таймаутом."""
        try:
            result = await asyncio.wait_for(
                self.execute(args, context),
                timeout=timeout
            )
            return result
        except asyncio.TimeoutError:
            return CommandResult(
                success=False,
                error_message=f"Command timed out after {timeout} seconds",
                exit_code=124
            )
        except Exception as e:
            return CommandResult(
                success=False,
                error_message=str(e),
                exit_code=1
            )
