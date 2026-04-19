"""
Основной цикл агента (Act-Think-Observe).
Управляет взаимодействием между LLM, инструментами и пользователем.
"""
import asyncio
import json
from typing import Optional, List
from rich.console import Console
from llm.client import AnthropicClient, Message
from context.manager import ContextManager
from prompts.generator import SystemPromptGenerator
from tools.manager import ToolService
from config.loader import AgentConfig

console = Console()

class AgentLoop:
    def __init__(self, config: AgentConfig):
        self.config = config
        self.client = AnthropicClient(api_key=config.api_key, model=config.model)
        self.context = ContextManager(max_tokens=config.max_tokens)
        self.prompt_generator = SystemPromptGenerator(project_root=config.project_root)
        self.tool_service = ToolService(auto_approve=config.auto_approve_tools)
        self.running = True

    async def run(self, user_input: str):
        """Запускает один цикл обработки запроса пользователя."""
        # 1. Добавляем запрос пользователя в контекст
        self.context.add_message("user", user_input)
        
        # 2. Генерируем системный промпт
        system_prompt = self.prompt_generator.generate(
            custom_instructions=self.config.custom_instructions,
            available_tools=self.tool_service.get_available_tools()
        )

        # 3. Получаем ответ от LLM
        console.print("\n[bold blue]Thinking...[/bold blue]")
        
        response_text = ""
        async for chunk in self.client.chat(
            messages=self.context.get_messages(),
            system_prompt=system_prompt,
            stream=True
        ):
            response_text += chunk
            print(chunk, end="", flush=True)
        
        print()  # Новая строка после ответа
        
        # 4. Добавляем ответ ассистента в контекст
        self.context.add_message("assistant", response_text)

        # 5. Проверяем, есть ли вызовы инструментов в ответе
        # (В реальной реализации здесь нужен парсинг XML/JSON ответа на наличие tool_use)
        # Для демо просто эмулируем завершение
        console.print("\n[green]Cycle complete.[/green]")

    async def run_interactive(self):
        """Запускает интерактивный режим REPL."""
        console.print("[bold green]Claude Code Python (Interactive Mode)[/bold green]")
        console.print("Type 'exit' or 'quit' to stop.\n")

        while self.running:
            try:
                user_input = await asyncio.to_thread(
                    lambda: console.input("[bold yellow]You:[/bold yellow] ")
                )
                
                if user_input.lower() in ["exit", "quit"]:
                    self.running = False
                    break
                
                if not user_input.strip():
                    continue

                await self.run(user_input)

            except KeyboardInterrupt:
                console.print("\n[yellow]Interrupted by user.[/yellow]")
                break
            except Exception as e:
                console.print(f"\n[red]Error:[/red] {e}")
