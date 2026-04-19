#!/usr/bin/env python3
"""
CLI интерфейс для Claude Code на Python.
Точка входа в приложение.
"""
import asyncio
import sys
import typer
from rich.console import Console
from config.loader import AgentConfig
from agent.loop import AgentLoop

app = typer.Typer(help="Claude Code CLI - AI Assistant")
console = Console()

@app.command()
def interactive(
    config_file: str = typer.Option(None, "--config", "-c", help="Path to config file"),
):
    """Запуск в интерактивном режиме (REPL)."""
    try:
        config = AgentConfig.load(Path(config_file) if config_file else None)
        
        if not config.api_key:
            console.print("[red]Error:[/red] ANTHROPIC_API_KEY is not set.")
            console.print("Please export it: export ANTHROPIC_API_KEY='your-key'")
            raise SystemExit(1)

        loop = AgentLoop(config)
        asyncio.run(loop.run_interactive())
        
    except Exception as e:
        console.print(f"[red]Fatal error:[/red] {e}")
        raise SystemExit(1)

@app.command()
def run(
    prompt: str = typer.Argument(..., help="The prompt to execute"),
    config_file: str = typer.Option(None, "--config", "-c", help="Path to config file"),
):
    """Выполнить одну команду и выйти."""
    try:
        config = AgentConfig.load(Path(config_file) if config_file else None)
        
        if not config.api_key:
            console.print("[red]Error:[/red] ANTHROPIC_API_KEY is not set.")
            raise SystemExit(1)

        loop = AgentLoop(config)
        asyncio.run(loop.run(prompt))
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)

if __name__ == "__main__":
    from pathlib import Path
    app()
