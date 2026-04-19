"""
Системные промпты - генерация динамических промптов
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime


@dataclass
class PromptSection:
    """Секция промпта"""
    name: str
    content: str
    priority: int = 0  # Приоритет секции (меньше = важнее)
    is_required: bool = True


@dataclass
class SystemPromptConfig:
    """Конфигурация системного промпта"""
    base_prompt: str = ""
    sections: List[PromptSection] = field(default_factory=list)
    variables: Dict[str, Any] = field(default_factory=dict)
    max_length: int = 8000


class SystemPromptBuilder:
    """
    Билдер системных промптов - сборка и генерация промптов
    """
    
    def __init__(self, config: Optional[SystemPromptConfig] = None):
        self.config = config or SystemPromptConfig()
        self._sections: Dict[str, PromptSection] = {}
        
        # Добавляем стандартные секции
        self._add_default_sections()
    
    def _add_default_sections(self):
        """Добавить секции по умолчанию"""
        self.add_section(
            PromptSection(
                name="identity",
                content="""You are Claude Code, an AI programming assistant developed by Anthropic.
You are a pair programmer helping users with coding tasks.
You think step-by-step and provide clear, well-reasoned solutions.""",
                priority=1,
                is_required=True
            )
        )
        
        self.add_section(
            PromptSection(
                name="capabilities",
                content="""You have access to various tools:
- Bash execution for running commands
- File system operations (read, write, search)
- Web search capabilities
- Code analysis and LSP features
- Multi-agent coordination for complex tasks""",
                priority=2,
                is_required=True
            )
        )
        
        self.add_section(
            PromptSection(
                name="best_practices",
                content="""Best practices:
1. Always think before acting
2. Break complex tasks into smaller steps
3. Test your code when possible
4. Explain your reasoning clearly
5. Ask for clarification when needed
6. Respect user preferences and project conventions""",
                priority=3,
                is_required=False
            )
        )
        
        self.add_section(
            PromptSection(
                name="safety",
                content="""Safety guidelines:
- Do not execute destructive commands without confirmation
- Respect privacy and security
- Do not bypass authentication or security measures
- Follow ethical coding practices""",
                priority=1,
                is_required=True
            )
        )
    
    def add_section(self, section: PromptSection):
        """Добавить секцию промпта"""
        self._sections[section.name] = section
    
    def remove_section(self, name: str):
        """Удалить секцию"""
        if name in self._sections:
            del self._sections[name]
    
    def update_section(self, name: str, content: Optional[str] = None, priority: Optional[int] = None):
        """Обновить секцию"""
        if name not in self._sections:
            raise ValueError(f"Section {name} not found")
        
        section = self._sections[name]
        if content is not None:
            section.content = content
        if priority is not None:
            section.priority = priority
    
    def set_variable(self, key: str, value: Any):
        """Установить переменную для подстановки"""
        self.config.variables[key] = value
    
    def _substitute_variables(self, text: str) -> str:
        """Подставить переменные в текст"""
        result = text
        for key, value in self.config.variables.items():
            placeholder = f"{{{key}}}"
            result = result.replace(placeholder, str(value))
        return result
    
    def build(self, include_optional: bool = True) -> str:
        """
        Построить финальный системный промпт
        
        Args:
            include_optional: Включать опциональные секции
        
        Returns:
            Сформированный системный промпт
        """
        # Сортируем секции по приоритету
        sections = sorted(
            self._sections.values(),
            key=lambda s: s.priority
        )
        
        # Фильтруем по required/optional
        if not include_optional:
            sections = [s for s in sections if s.is_required]
        
        # Собираем промпт
        parts = []
        
        # Базовый промпт (если есть)
        if self.config.base_prompt:
            parts.append(self._substitute_variables(self.config.base_prompt))
        
        # Секции
        for section in sections:
            parts.append(self._substitute_variables(section.content))
        
        # Объединяем
        full_prompt = "\n\n".join(parts)
        
        # Обрезаем если слишком длинный
        if len(full_prompt) > self.config.max_length:
            full_prompt = full_prompt[:self.config.max_length - 100] + "\n\n[truncated...]"
        
        return full_prompt
    
    def get_sections_info(self) -> List[Dict[str, Any]]:
        """Получить информацию о секциях"""
        return [
            {
                "name": s.name,
                "priority": s.priority,
                "is_required": s.is_required,
                "length": len(s.content)
            }
            for s in sorted(self._sections.values(), key=lambda x: x.priority)
        ]


# Предустановленные шаблоны промптов для разных режимов
PROMPT_TEMPLATES = {
    "default": SystemPromptConfig(
        base_prompt="You are Claude Code, an AI programming assistant.",
        max_length=8000
    ),
    
    "undercover": SystemPromptConfig(
        base_prompt="You are operating in undercover mode. Be concise and direct.",
        max_length=4000
    ),
    
    "ultraplan": SystemPromptConfig(
        base_prompt="You are in ULTRAPLAN mode. Focus on detailed planning and architecture.",
        max_length=12000
    ),
    
    "penguin": SystemPromptConfig(
        base_prompt="🐧 Penguin Mode: You are a friendly penguin developer who loves clean code!",
        max_length=6000
    )
}


def get_prompt_for_mode(mode: str, variables: Optional[Dict] = None) -> str:
    """
    Получить промпт для режима
    
    Args:
        mode: Название режима
        variables: Переменные для подстановки
    
    Returns:
        Системный промпт
    """
    config = PROMPT_TEMPLATES.get(mode, PROMPT_TEMPLATES["default"])
    builder = SystemPromptBuilder(config)
    
    if variables:
        for key, value in variables.items():
            builder.set_variable(key, value)
    
    return builder.build()


__all__ = [
    "PromptSection",
    "SystemPromptConfig",
    "SystemPromptBuilder",
    "PROMPT_TEMPLATES",
    "get_prompt_for_mode"
]
