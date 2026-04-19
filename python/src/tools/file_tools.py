"""
Инструменты для работы с файловой системой
"""
import os
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import json

from . import BaseTool, ToolInput, ToolOutput


@dataclass
class FileSystemConfig:
    """Конфигурация файловых инструментов"""
    base_path: str = None  # Базовый путь (ограничение доступа)
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    allowed_extensions: List[str] = None  # None = все разрешены


class ReadFileTool(BaseTool):
    """Чтение файла"""
    
    name = "read"
    description = "Читает содержимое файла"
    requires_permission = True
    
    def __init__(self, config: Optional[FileSystemConfig] = None):
        self.config = config or FileSystemConfig()
    
    async def execute(self, input_data: ToolInput) -> ToolOutput:
        path_str = input_data.arguments.get("path", "")
        
        if not path_str:
            return ToolOutput(
                success=False,
                content="",
                error_message="Путь к файлу не указан"
            )
        
        try:
            path = Path(path_str).resolve()
            
            # Проверка базового пути
            if self.config.base_path:
                base = Path(self.config.base_path).resolve()
                if not str(path).startswith(str(base)):
                    return ToolOutput(
                        success=False,
                        content="",
                        error_message=f"Доступ за пределами базового пути {self.config.base_path}"
                    )
            
            # Проверка размера
            if path.stat().st_size > self.config.max_file_size:
                return ToolOutput(
                    success=False,
                    content="",
                    error_message=f"Файл слишком большой ({path.stat().st_size} байт)"
                )
            
            # Чтение файла
            content = await asyncio.to_thread(path.read_text, encoding="utf-8")
            
            return ToolOutput(
                success=True,
                content=content,
                metadata={
                    "path": str(path),
                    "size": path.stat().st_size,
                    "lines": len(content.splitlines())
                }
            )
            
        except FileNotFoundError:
            return ToolOutput(
                success=False,
                content="",
                error_message=f"Файл не найден: {path_str}"
            )
        except Exception as e:
            return ToolOutput(
                success=False,
                content="",
                error_message=f"Ошибка чтения: {str(e)}"
            )
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Путь к файлу"
                    }
                },
                "required": ["path"]
            }
        }


class WriteFileTool(BaseTool):
    """Запись в файл"""
    
    name = "write"
    description = "Записывает содержимое в файл (создает или перезаписывает)"
    requires_permission = True
    
    def __init__(self, config: Optional[FileSystemConfig] = None):
        self.config = config or FileSystemConfig()
    
    async def execute(self, input_data: ToolInput) -> ToolOutput:
        path_str = input_data.arguments.get("path", "")
        content = input_data.arguments.get("content", "")
        
        if not path_str:
            return ToolOutput(
                success=False,
                content="",
                error_message="Путь к файлу не указан"
            )
        
        try:
            path = Path(path_str).resolve()
            
            # Проверка базового пути
            if self.config.base_path:
                base = Path(self.config.base_path).resolve()
                if not str(path).startswith(str(base)):
                    return ToolOutput(
                        success=False,
                        content="",
                        error_message=f"Доступ за пределами базового пути {self.config.base_path}"
                    )
            
            # Создание директорий
            await asyncio.to_thread(path.parent.mkdir, parents=True, exist_ok=True)
            
            # Запись файла
            await asyncio.to_thread(path.write_text, content, encoding="utf-8")
            
            return ToolOutput(
                success=True,
                content=f"Файл записан: {path_str}",
                metadata={
                    "path": str(path),
                    "size": len(content.encode("utf-8"))
                }
            )
            
        except Exception as e:
            return ToolOutput(
                success=False,
                content="",
                error_message=f"Ошибка записи: {str(e)}"
            )
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Путь к файлу"
                    },
                    "content": {
                        "type": "string",
                        "description": "Содержимое для записи"
                    }
                },
                "required": ["path", "content"]
            }
        }


class EditFileTool(BaseTool):
    """Редактирование файла (поиск и замена)"""
    
    name = "edit"
    description = "Редактирует файл, заменяя старый текст на новый"
    requires_permission = True
    
    def __init__(self, config: Optional[FileSystemConfig] = None):
        self.config = config or FileSystemConfig()
    
    async def execute(self, input_data: ToolInput) -> ToolOutput:
        path_str = input_data.arguments.get("path", "")
        old_text = input_data.arguments.get("old_text", "")
        new_text = input_data.arguments.get("new_text", "")
        
        if not path_str:
            return ToolOutput(
                success=False,
                content="",
                error_message="Путь к файлу не указан"
            )
        
        if not old_text:
            return ToolOutput(
                success=False,
                content="",
                error_message="Текст для замены не указан"
            )
        
        try:
            path = Path(path_str).resolve()
            
            # Проверка базового пути
            if self.config.base_path:
                base = Path(self.config.base_path).resolve()
                if not str(path).startswith(str(base)):
                    return ToolOutput(
                        success=False,
                        content="",
                        error_message=f"Доступ за пределами базового пути {self.config.base_path}"
                    )
            
            # Чтение текущего содержимого
            content = await asyncio.to_thread(path.read_text, encoding="utf-8")
            
            # Поиск и замена
            if old_text not in content:
                return ToolOutput(
                    success=False,
                    content="",
                    error_message="Текст для замены не найден в файле"
                )
            
            new_content = content.replace(old_text, new_text, 1)
            
            # Запись измененного файла
            await asyncio.to_thread(path.write_text, new_content, encoding="utf-8")
            
            return ToolOutput(
                success=True,
                content="Файл успешно отредактирован",
                metadata={
                    "path": str(path),
                    "replacements": 1
                }
            )
            
        except Exception as e:
            return ToolOutput(
                success=False,
                content="",
                error_message=f"Ошибка редактирования: {str(e)}"
            )
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Путь к файлу"
                    },
                    "old_text": {
                        "type": "string",
                        "description": "Текст для замены"
                    },
                    "new_text": {
                        "type": "string",
                        "description": "Новый текст"
                    }
                },
                "required": ["path", "old_text", "new_text"]
            }
        }


__all__ = [
    "FileSystemConfig",
    "ReadFileTool",
    "WriteFileTool",
    "EditFileTool"
]
