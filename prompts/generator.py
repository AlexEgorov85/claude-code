"""
Генератор системных промптов для агента.
Формирует контекст, инструкции и правила поведения.
"""
from typing import Optional, List
from pathlib import Path

class SystemPromptGenerator:
    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()

    def generate(
        self,
        custom_instructions: Optional[str] = None,
        available_tools: List[str] = None
    ) -> str:
        """
        Генерирует системный промпт с инструкциями для агента.
        """
        base_prompt = f"""You are Claude Code, an expert AI programming assistant operating in a terminal environment.
Your goal is to help the user with software engineering tasks, coding, debugging, and system administration.

Current working directory: {self.project_root.absolute()}

You have access to the following tools:
- bash: Execute shell commands
- read_file: Read file contents
- write_file: Create or overwrite files
- edit_file: Make targeted edits to files
- grep: Search for patterns in files
- glob: Find files by pattern
- todo_write: Manage task lists

Rules:
1. Always think step-by-step before acting.
2. Use tools to accomplish tasks; do not just describe what to do.
3. Respect file permissions and user confirmations.
4. Keep responses concise and focused on the task.
5. If unsure, ask clarifying questions.
"""

        if available_tools:
            tools_str = ", ".join(available_tools)
            base_prompt += f"\n\nActive tools: {tools_str}"

        if custom_instructions:
            base_prompt += f"\n\nUser Instructions:\n{custom_instructions}"

        return base_prompt
