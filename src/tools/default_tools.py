"""Default tools implementation."""
from typing import Any
import asyncio
import subprocess
from pathlib import Path
from ..tools.base import BaseTool, ToolResult


class EchoTool(BaseTool):
    """Simple echo tool for testing."""
    
    @property
    def name(self) -> str:
        return "echo"
    
    @property
    def description(self) -> str:
        return "Returns the received text back. Useful for testing."
    
    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "Text to return"
                }
            },
            "required": ["message"]
        }
    
    async def execute(self, message: str, **kwargs) -> ToolResult:
        """Execute the tool."""
        return ToolResult(
            content=f"Echo: {message}",
            is_error=False
        )


class CalculatorTool(BaseTool):
    """Tool for simple calculations."""
    
    @property
    def name(self) -> str:
        return "calculator"
    
    @property
    def description(self) -> str:
        return "Performs simple arithmetic operations: add, subtract, multiply, divide."
    
    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["add", "subtract", "multiply", "divide"],
                    "description": "Arithmetic operation"
                },
                "a": {
                    "type": "number",
                    "description": "First operand"
                },
                "b": {
                    "type": "number",
                    "description": "Second operand"
                }
            },
            "required": ["operation", "a", "b"]
        }
    
    async def execute(
        self, 
        operation: str, 
        a: float, 
        b: float,
        **kwargs
    ) -> ToolResult:
        """Perform calculations."""
        try:
            if operation == "add":
                result = a + b
            elif operation == "subtract":
                result = a - b
            elif operation == "multiply":
                result = a * b
            elif operation == "divide":
                if b == 0:
                    return ToolResult(
                        content=None,
                        is_error=True,
                        error_message="Division by zero"
                    )
                result = a / b
            else:
                return ToolResult(
                    content=None,
                    is_error=True,
                    error_message=f"Unknown operation: {operation}"
                )
            
            return ToolResult(
                content=result,
                is_error=False
            )
        except Exception as e:
            return ToolResult(
                content=None,
                is_error=True,
                error_message=str(e)
            )


class ReadFileTool(BaseTool):
    """Tool to read file contents."""
    
    @property
    def name(self) -> str:
        return "read_file"
    
    @property
    def description(self) -> str:
        return "Read the contents of a file at the specified path."
    
    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "The path to the file to read"
                },
                "offset": {
                    "type": "integer",
                    "description": "Line offset to start reading from",
                    "default": 0
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of lines to read",
                    "default": 100
                }
            },
            "required": ["path"]
        }
    
    async def execute(self, path: str, offset: int = 0, limit: int = 100, **kwargs) -> ToolResult:
        """Read file contents."""
        try:
            file_path = Path(path)
            if not file_path.exists():
                return ToolResult(
                    content=None,
                    is_error=True,
                    error_message=f"File not found: {path}"
                )
            
            if not file_path.is_file():
                return ToolResult(
                    content=None,
                    is_error=True,
                    error_message=f"Not a file: {path}"
                )
            
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            selected_lines = lines[offset:offset + limit]
            content = ''.join(selected_lines)
            
            return ToolResult(
                content=content,
                is_error=False
            )
        except Exception as e:
            return ToolResult(
                content=None,
                is_error=True,
                error_message=f"Failed to read file: {str(e)}"
            )


class WriteFileTool(BaseTool):
    """Tool to write file contents."""
    
    @property
    def name(self) -> str:
        return "write_file"
    
    @property
    def description(self) -> str:
        return "Write contents to a file at the specified path. Creates the file if it doesn't exist."
    
    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "The path to the file to write"
                },
                "content": {
                    "type": "string",
                    "description": "The content to write to the file"
                },
                "append": {
                    "type": "boolean",
                    "description": "Whether to append to the file instead of overwriting",
                    "default": False
                }
            },
            "required": ["path", "content"]
        }
    
    async def execute(self, path: str, content: str, append: bool = False, **kwargs) -> ToolResult:
        """Write content to file."""
        try:
            file_path = Path(path)
            
            # Create parent directories if they don't exist
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            mode = 'a' if append else 'w'
            with open(file_path, mode, encoding='utf-8') as f:
                f.write(content)
            
            return ToolResult(
                content=f"Successfully wrote {len(content)} characters to {path}",
                is_error=False
            )
        except Exception as e:
            return ToolResult(
                content=None,
                is_error=True,
                error_message=f"Failed to write file: {str(e)}"
            )


class BashTool(BaseTool):
    """Tool to execute bash commands."""
    
    @property
    def name(self) -> str:
        return "bash"
    
    @property
    def description(self) -> str:
        return "Execute a bash command in the shell."
    
    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The bash command to execute"
                },
                "cwd": {
                    "type": "string",
                    "description": "Working directory for the command",
                    "default": "."
                },
                "timeout": {
                    "type": "integer",
                    "description": "Timeout in seconds",
                    "default": 300
                }
            },
            "required": ["command"]
        }
    
    async def execute(self, command: str, cwd: str = ".", timeout: int = 300, **kwargs) -> ToolResult:
        """Execute bash command."""
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
                
                result = {
                    "stdout": stdout.decode('utf-8', errors='replace'),
                    "stderr": stderr.decode('utf-8', errors='replace'),
                    "exit_code": process.returncode or 0
                }
                
                return ToolResult(
                    content=result,
                    is_error=process.returncode != 0
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return ToolResult(
                    content=None,
                    is_error=True,
                    error_message=f"Command timed out after {timeout} seconds"
                )
        except Exception as e:
            return ToolResult(
                content=None,
                is_error=True,
                error_message=f"Failed to execute command: {str(e)}"
            )


class ListDirTool(BaseTool):
    """Tool to list directory contents."""
    
    @property
    def name(self) -> str:
        return "list_dir"
    
    @property
    def description(self) -> str:
        return "List contents of a directory."
    
    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "The directory path to list"
                },
                "recursive": {
                    "type": "boolean",
                    "description": "Whether to list recursively",
                    "default": False
                }
            },
            "required": ["path"]
        }
    
    async def execute(self, path: str, recursive: bool = False, **kwargs) -> ToolResult:
        """List directory contents."""
        try:
            dir_path = Path(path)
            if not dir_path.exists():
                return ToolResult(
                    content=None,
                    is_error=True,
                    error_message=f"Directory not found: {path}"
                )
            
            if not dir_path.is_dir():
                return ToolResult(
                    content=None,
                    is_error=True,
                    error_message=f"Not a directory: {path}"
                )
            
            results = []
            if recursive:
                for item in dir_path.rglob('*'):
                    results.append({
                        "name": item.name,
                        "path": str(item.relative_to(dir_path)),
                        "is_directory": item.is_dir(),
                        "size": item.stat().st_size if item.is_file() else 0
                    })
            else:
                for item in dir_path.iterdir():
                    results.append({
                        "name": item.name,
                        "path": str(item.name),
                        "is_directory": item.is_dir(),
                        "size": item.stat().st_size if item.is_file() else 0
                    })
            
            return ToolResult(
                content=sorted(results, key=lambda x: (not x["is_directory"], x["name"])),
                is_error=False
            )
        except Exception as e:
            return ToolResult(
                content=None,
                is_error=True,
                error_message=f"Failed to list directory: {str(e)}"
            )


def register_default_tools(registry=None) -> None:
    """Register default tools."""
    from ..tools.registry import ToolRegistry
    
    reg = registry or ToolRegistry()
    reg.register(EchoTool())
    reg.register(CalculatorTool())
    reg.register(ReadFileTool())
    reg.register(WriteFileTool())
    reg.register(BashTool())
    reg.register(ListDirTool())
    
    return reg

