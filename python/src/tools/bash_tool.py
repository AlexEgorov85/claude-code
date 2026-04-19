"""
Bash инструмент для выполнения команд в терминале
"""
import asyncio
import shlex
from typing import Dict, Any, Optional
from dataclasses import dataclass
import os

from . import BaseTool, ToolInput, ToolOutput


@dataclass
class BashConfig:
    """Конфигурация bash инструмента"""
    cwd: str = None
    timeout: int = 300  # секунд
    shell: str = "/bin/bash"
    allow_long_running: bool = True


class BashTool(BaseTool):
    """
    Инструмент для выполнения bash команд
    """
    
    name = "bash"
    description = "Выполняет команды в оболочке bash"
    requires_permission = True
    
    def __init__(self, config: Optional[BashConfig] = None):
        self.config = config or BashConfig()
        self._processes: Dict[str, asyncio.subprocess.Process] = {}
    
    async def execute(self, input_data: ToolInput) -> ToolOutput:
        """Выполнить bash команду"""
        command = input_data.arguments.get("command", "")
        cwd = input_data.arguments.get("cwd", self.config.cwd)
        timeout = input_data.arguments.get("timeout", self.config.timeout)
        background = input_data.arguments.get("background", False)
        
        if not command:
            return ToolOutput(
                success=False,
                content="",
                error_message="Команда не указана"
            )
        
        try:
            # Выполнение команды
            if background:
                # Фоновое выполнение
                return await self._execute_background(command, cwd, input_data.correlation_id)
            else:
                # Синхронное выполнение с таймаутом
                result = await asyncio.wait_for(
                    self._run_command(command, cwd),
                    timeout=timeout
                )
                return ToolOutput(
                    success=result["exit_code"] == 0,
                    content={
                        "stdout": result["stdout"],
                        "stderr": result["stderr"],
                        "exit_code": result["exit_code"]
                    },
                    metadata={
                        "command": command,
                        "cwd": cwd or os.getcwd(),
                        "execution_time": result.get("execution_time", 0)
                    }
                )
                
        except asyncio.TimeoutError:
            return ToolOutput(
                success=False,
                content="",
                error_message=f"Таймаут выполнения команды ({timeout}с)"
            )
        except Exception as e:
            return ToolOutput(
                success=False,
                content="",
                error_message=f"Ошибка выполнения: {str(e)}"
            )
    
    async def _run_command(self, command: str, cwd: Optional[str]) -> Dict[str, Any]:
        """Запустить команду и вернуть результат"""
        import time
        start_time = time.time()
        
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
            shell=True
        )
        
        stdout, stderr = await process.communicate()
        
        execution_time = int((time.time() - start_time) * 1000)
        
        return {
            "stdout": stdout.decode("utf-8", errors="replace"),
            "stderr": stderr.decode("utf-8", errors="replace"),
            "exit_code": process.returncode,
            "execution_time": execution_time
        }
    
    async def _execute_background(self, command: str, cwd: Optional[str], correlation_id: str) -> ToolOutput:
        """Запустить команду в фоновом режиме"""
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
                shell=True
            )
            
            self._processes[correlation_id] = process
            
            return ToolOutput(
                success=True,
                content={
                    "pid": process.pid,
                    "status": "running",
                    "message": "Процесс запущен в фоновом режиме"
                },
                metadata={
                    "command": command,
                    "correlation_id": correlation_id
                }
            )
        except Exception as e:
            return ToolOutput(
                success=False,
                content="",
                error_message=f"Ошибка запуска фонового процесса: {str(e)}"
            )
    
    def get_schema(self) -> Dict[str, Any]:
        """Получить JSON схему инструмента"""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Команда для выполнения"
                    },
                    "cwd": {
                        "type": "string",
                        "description": "Рабочая директория"
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Таймаут в секундах"
                    },
                    "background": {
                        "type": "boolean",
                        "description": "Запустить в фоновом режиме"
                    }
                },
                "required": ["command"]
            }
        }


__all__ = ["BashTool", "BashConfig"]
