"""Базовые команды агента."""
from typing import Any
from .base import BaseCommand, CommandResult


class HelpCommand(BaseCommand):
    """Команда помощи."""
    
    @property
    def name(self) -> str:
        return "help"
    
    @property
    def description(self) -> str:
        return "Показать справку по доступным командам"
    
    @property
    def usage(self) -> str:
        return "help [command_name]"
    
    @property
    def examples(self) -> list[str]:
        return [
            "help",
            "help help",
            "help status"
        ]
    
    @property
    def aliases(self) -> list[str]:
        return ["?", "h"]
    
    async def execute(self, args: list[str], context: dict[str, Any]) -> CommandResult:
        """Выполнение команды помощи."""
        from .registry import CommandRegistry
        
        registry = CommandRegistry()
        parsed = self.parse_args(args)
        
        if parsed.get("positional"):
            # Помощь по конкретной команде
            cmd_name = parsed["positional"][0]
            command = registry.get(cmd_name)
            
            if not command:
                return CommandResult(
                    success=False,
                    error_message=f"Command not found: {cmd_name}",
                    exit_code=1
                )
            
            output = f"""Command: {command.name}
Description: {command.description}
Usage: {command.usage}
Category: {command.category}
"""
            if command.examples:
                output += "\nExamples:\n"
                for example in command.examples:
                    output += f"  {example}\n"
            
            if command.aliases:
                output += f"\nAliases: {', '.join(command.aliases)}\n"
            
            return CommandResult(success=True, output=output)
        else:
            # Общий список команд
            categories = registry.get_categories()
            output = "Available commands:\n\n"
            
            for category in categories:
                commands = registry.get_commands_by_category(category)
                output += f"[{category}]\n"
                for cmd in commands:
                    output += f"  {cmd.name:20} - {cmd.description}\n"
                output += "\n"
            
            output += "\nUse 'help <command>' for more information about a specific command."
            
            return CommandResult(success=True, output=output)


class StatusCommand(BaseCommand):
    """Команда статуса."""
    
    @property
    def name(self) -> str:
        return "status"
    
    @property
    def description(self) -> str:
        return "Показать текущий статус агента"
    
    @property
    def aliases(self) -> list[str]:
        return ["st"]
    
    async def execute(self, args: list[str], context: dict[str, Any]) -> CommandResult:
        """Выполнение команды статуса."""
        state = context.get("state")
        
        if not state:
            return CommandResult(
                success=False,
                error_message="State not available",
                exit_code=1
            )
        
        output = f"""Agent Status
============
ID: {state.id}
Running: {state.is_running}
Paused: {state.is_paused}
Current Task: {state.current_task or 'None'}
Messages: {len(state.messages)}
Pending Tools: {len(state.pending_tool_calls)}
Token Usage: {state.token_usage.total_tokens}
Total Cost: ${state.cost_info.total_cost:.4f}
Created: {state.created_at}
Updated: {state.updated_at}
"""
        
        return CommandResult(success=True, output=output)


class ClearCommand(BaseCommand):
    """Команда очистки истории."""
    
    @property
    def name(self) -> str:
        return "clear"
    
    @property
    def description(self) -> str:
        return "Очистить историю сообщений"
    
    @property
    def requires_confirmation(self) -> bool:
        return True
    
    @property
    def aliases(self) -> list[str]:
        return ["cls"]
    
    async def execute(self, args: list[str], context: dict[str, Any]) -> CommandResult:
        """Выполнение команды очистки."""
        state = context.get("state")
        
        if not state:
            return CommandResult(
                success=False,
                error_message="State not available",
                exit_code=1
            )
        
        parsed = self.parse_args(args)
        keep_system = parsed.get("keep-system", False)
        
        if keep_system:
            # Сохраняем только системные сообщения
            system_messages = [
                msg for msg in state.messages 
                if msg.role.value == "system"
            ]
            removed_count = len(state.messages) - len(system_messages)
            state.messages = system_messages
        else:
            removed_count = len(state.messages)
            state.messages.clear()
        
        return CommandResult(
            success=True,
            output=f"Cleared {removed_count} messages"
        )


class ExitCommand(BaseCommand):
    """Команда выхода."""
    
    @property
    def name(self) -> str:
        return "exit"
    
    @property
    def description(self) -> str:
        return "Выйти из агента"
    
    @property
    def aliases(self) -> list[str]:
        return ["quit", "q"]
    
    async def execute(self, args: list[str], context: dict[str, Any]) -> CommandResult:
        """Выполнение команды выхода."""
        loop = context.get("loop")
        
        if loop and hasattr(loop, "stop"):
            loop.stop()
        
        return CommandResult(
            success=True,
            output="Exiting..."
        )


def register_default_commands(registry=None) -> None:
    """Регистрация команд по умолчанию."""
    from .registry import CommandRegistry
    
    reg = registry or CommandRegistry()
    reg.register(HelpCommand())
    reg.register(StatusCommand())
    reg.register(ClearCommand())
    reg.register(ExitCommand())
    
    return reg
