"""Модуль команд."""
from .base import BaseCommand, CommandDefinition, CommandResult
from .registry import CommandRegistry
from .default_commands import (
    HelpCommand, StatusCommand, ClearCommand, ExitCommand,
    register_default_commands
)

__all__ = [
    "BaseCommand",
    "CommandDefinition",
    "CommandResult",
    "CommandRegistry",
    "HelpCommand",
    "StatusCommand",
    "ClearCommand",
    "ExitCommand",
    "register_default_commands",
]
