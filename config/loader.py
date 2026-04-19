"""
Загрузчик конфигурации проекта.
Читает настройки из файлов и переменных окружения.
"""
import os
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List

@dataclass
class AgentConfig:
    api_key: str = ""
    model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 4096
    temperature: float = 0.7
    auto_approve_tools: List[str] = field(default_factory=list)
    custom_instructions: Optional[str] = None
    project_root: Path = field(default_factory=Path.cwd)

    @classmethod
    def load(cls, config_path: Optional[Path] = None) -> "AgentConfig":
        """
        Загружает конфигурацию из файла и переменных окружения.
        Приоритет: ENV > файл конфига > значения по умолчанию.
        """
        config = cls()

        # 1. Загрузка из файла (если существует)
        if config_path is None:
            config_path = Path.cwd() / ".claude-code.json"
        
        if config_path.exists():
            with open(config_path, "r") as f:
                data = json.load(f)
                config.model = data.get("model", config.model)
                config.max_tokens = data.get("max_tokens", config.max_tokens)
                config.auto_approve_tools = data.get("auto_approve_tools", [])
                config.custom_instructions = data.get("custom_instructions")

        # 2. Переопределение из ENV
        config.api_key = os.getenv("ANTHROPIC_API_KEY", config.api_key)
        config.model = os.getenv("CLAUDE_MODEL", config.model)
        
        if os.getenv("CLAUDE_MAX_TOKENS"):
            config.max_tokens = int(os.getenv("CLAUDE_MAX_TOKENS"))
        
        if os.getenv("CLAUDE_AUTO_APPROVE"):
            config.auto_approve_tools = os.getenv("CLAUDE_AUTO_APPROVE").split(",")

        return config
