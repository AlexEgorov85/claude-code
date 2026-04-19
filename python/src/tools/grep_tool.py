"""
Инструмент grep для поиска по файлам
"""
import os
import asyncio
import re
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from . import BaseTool, ToolInput, ToolOutput


@dataclass
class GrepConfig:
    """Конфигурация grep инструмента"""
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    max_results: int = 100
    exclude_patterns: List[str] = None
    
    def __post_init__(self):
        if self.exclude_patterns is None:
            self.exclude_patterns = [
                "*.pyc", "__pycache__", "*.so", "*.dll", 
                ".git", "node_modules", "*.min.js", "*.map"
            ]


class GrepTool(BaseTool):
    """Поиск текста в файлах с поддержкой regex"""
    
    name = "grep"
    description = "Ищет текст в файлах с поддержкой регулярных выражений"
    requires_permission = True
    
    def __init__(self, config: Optional[GrepConfig] = None):
        self.config = config or GrepConfig()
    
    async def execute(self, input_data: ToolInput) -> ToolOutput:
        pattern = input_data.arguments.get("pattern", "")
        path = input_data.arguments.get("path", ".")
        case_sensitive = input_data.arguments.get("case_sensitive", False)
        regex = input_data.arguments.get("regex", False)
        include_pattern = input_data.arguments.get("include", "*")
        
        if not pattern:
            return ToolOutput(
                success=False,
                content="",
                error_message="Шаблон поиска не указан"
            )
        
        try:
            search_path = Path(path).resolve()
            
            if not search_path.exists():
                return ToolOutput(
                    success=False,
                    content="",
                    error_message=f"Путь не существует: {path}"
                )
            
            # Компиляция паттерна
            flags = 0 if case_sensitive else re.IGNORECASE
            if regex:
                try:
                    compiled_pattern = re.compile(pattern, flags)
                except re.error as e:
                    return ToolOutput(
                        success=False,
                        content="",
                        error_message=f"Некорректное регулярное выражение: {str(e)}"
                    )
            else:
                # Экранирование для обычного поиска
                compiled_pattern = re.compile(re.escape(pattern), flags)
            
            results = []
            files_searched = 0
            
            # Рекурсивный поиск
            await self._search_directory(
                search_path,
                compiled_pattern,
                include_pattern,
                results,
                files_searched
            )
            
            # Ограничение количества результатов
            if len(results) > self.config.max_results:
                results = results[:self.config.max_results]
                results.append({
                    "file": "...",
                    "line": -1,
                    "content": f"... и еще {len(results) - self.config.max_results} результатов"
                })
            
            # Форматирование вывода
            output_lines = []
            for result in results:
                if result["line"] == -1:
                    output_lines.append(result["content"])
                else:
                    output_lines.append(f"{result['file']}:{result['line']}: {result['content']}")
            
            return ToolOutput(
                success=True,
                content="\n".join(output_lines),
                metadata={
                    "pattern": pattern,
                    "path": str(search_path),
                    "files_searched": files_searched,
                    "results_found": len(results)
                }
            )
            
        except Exception as e:
            return ToolOutput(
                success=False,
                content="",
                error_message=f"Ошибка поиска: {str(e)}"
            )
    
    async def _search_directory(
        self,
        path: Path,
        pattern: re.Pattern,
        include_pattern: str,
        results: List[Dict],
        files_searched: int
    ):
        """Рекурсивный поиск по директории"""
        import fnmatch
        
        try:
            items = list(path.iterdir())
        except PermissionError:
            return
        
        for item in items:
            # Проверка исключений
            if any(fnmatch.fnmatch(item.name, exc) for exc in self.config.exclude_patterns):
                continue
            
            if item.is_file():
                # Проверка include паттерна
                if not fnmatch.fnmatch(item.name, include_pattern):
                    continue
                
                # Проверка размера
                try:
                    if item.stat().st_size > self.config.max_file_size:
                        continue
                except OSError:
                    continue
                
                files_searched += 1
                
                # Поиск в файле
                try:
                    content = await asyncio.to_thread(item.read_text, encoding="utf-8", errors="ignore")
                    lines = content.splitlines()
                    
                    for line_num, line in enumerate(lines, 1):
                        if pattern.search(line):
                            results.append({
                                "file": str(item.relative_to(path.parent)),
                                "line": line_num,
                                "content": line.rstrip()
                            })
                            
                            if len(results) >= self.config.max_results:
                                return
                                
                except (IOError, UnicodeDecodeError):
                    pass
                    
            elif item.is_dir():
                await self._search_directory(
                    item, pattern, include_pattern, results, files_searched
                )
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "Текст или regex для поиска"
                    },
                    "path": {
                        "type": "string",
                        "description": "Директория для поиска",
                        "default": "."
                    },
                    "case_sensitive": {
                        "type": "boolean",
                        "description": "Учитывать регистр",
                        "default": False
                    },
                    "regex": {
                        "type": "boolean",
                        "description": "Использовать регулярные выражения",
                        "default": False
                    },
                    "include": {
                        "type": "string",
                        "description": "Шаблон имен файлов (glob)",
                        "default": "*"
                    }
                },
                "required": ["pattern"]
            }
        }


__all__ = ["GrepTool", "GrepConfig"]
