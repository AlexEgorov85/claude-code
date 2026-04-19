# Claude Code Agent - Python Implementation

Python-версия ядра агента Claude Code.

## Структура проекта

```
python/
├── src/
│   ├── __init__.py          # Главный пакет, экспорты
│   ├── core/                # Ядро агента
│   │   └── __init__.py      # SessionConfig, AgentCore, AgentMode
│   ├── tools/               # Система инструментов
│   │   └── __init__.py      # BaseTool, ToolRegistry, ToolCall
│   ├── tasks/               # Управление задачами
│   │   └── __init__.py      # Task, TaskManager, AgentExecutor
│   ├── models/              # Модельный слой
│   │   └── __init__.py      # ModelManager, ModelInfo, RateLimit
│   ├── prompts/             # Системные промпты
│   │   └── __init__.py      # SystemPromptBuilder, PROMPT_TEMPLATES
│   ├── services/            # Сервисы
│   │   └── __init__.py      # APIClient, MCP, OAuth, Telemetry
│   ├── coordinator/         # Координатор
│   │   └── __init__.py      # MultiAgentCoordinator, BackgroundTaskManager
│   ├── context/             # Контекст (TODO)
│   ├── permissions/         # Разрешения (TODO)
│   └── utils/               # Утилиты
│       └── __init__.py      # Вспомогательные функции
├── tests/                   # Тесты (TODO)
├── requirements.txt         # Зависимости
└── README.md               # Этот файл
```

## Компоненты ядра

### 1. Core (`src/core/__init__.py`)
- **AgentMode** - режимы работы (default, undercover, ultraplan, penguin)
- **ModelConfig** - конфигурация модели
- **SessionConfig** - конфигурация сессии
- **SessionState** - состояние активной сессии
- **AgentCore** - центральное ядро агента

### 2. Tools (`src/tools/__init__.py`)
- **BaseTool** - базовый класс для всех инструментов
- **ToolRegistry** - реестр доступных инструментов
- **ToolCall/ToolInput/ToolOutput** - типы для вызовов инструментов
- **PermissionType/ToolPermission** - система разрешений

### 3. Tasks (`src/tasks/__init__.py`)
- **Task** - единица работы агента
- **TaskManager** - управление жизненным циклом задач
- **AgentExecutor** - выполнение задач агентами
- **TaskStatus/TaskType** - статусы и типы задач

### 4. Models (`src/models/__init__.py`)
- **ModelManager** - управление моделями
- **ModelInfo** - информация о модели
- **ModelProvider/ModelCapability** - провайдеры и возможности
- **RateLimit** - ограничения скорости
- **TokenUsage** - использование токенов

### 5. Prompts (`src/prompts/__init__.py`)
- **SystemPromptBuilder** - сборка системных промптов
- **PromptSection** - секция промпта
- **PROMPT_TEMPLATES** - шаблоны для разных режимов

### 6. Services (`src/services/__init__.py`)
- **APIClient** - HTTP клиент для API
- **MCPClient** - Model Context Protocol
- **OAuthClient** - OAuth аутентификация
- **TelemetryClient** - телеметрия
- **ContextCompressor** - компрессия контекста
- **Summarizer** - саммаризация

### 7. Coordinator (`src/coordinator/__init__.py`)
- **MultiAgentCoordinator** - оркестрация мульти-агентных сценариев
- **BackgroundTaskManager** - фоновые задачи
- **AgentRole/AgentState** - роли и состояния агентов

### 8. Utils (`src/utils/__init__.py`)
- Файловые операции
- JSON утилиты
- Строковые утилиты
- Асинхронные хелперы
- Декораторы (retry, timing)

## Быстрый старт

```python
import asyncio
from src import AgentCore, SessionConfig, AgentMode

async def main():
    # Создание конфигурации
    config = SessionConfig(
        working_directory="/path/to/project",
        mode=AgentMode.DEFAULT
    )
    
    # Инициализация ядра
    agent = AgentCore(config)
    await agent.initialize()
    
    # Получение состояния
    print(agent.get_state_summary())
    
    # Завершение
    await agent.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
```

## Зависимости

Основные зависимости (устанавливаются через `pip install -r requirements.txt`):

```
pydantic>=2.0
httpx>=0.25
textual>=0.50
```

## Следующие шаги

1. ✅ Базовая инфраструктура (core, tools, tasks)
2. ✅ Модельный слой (models)
3. ✅ Системные промпты (prompts)
4. ✅ Сервисы (services)
5. ✅ Координатор (coordinator)
6. ✅ Утилиты (utils)
7. ⏳ CLI интерфейс
8. ⏳ Инструменты (bash, filesystem, etc.)
9. ⏳ MCP интеграция
10. ⏳ UI (textual)

## Статус миграции

| Компонент | Статус | Файлы |
|-----------|--------|-------|
| Core | ✅ Готово | 1 |
| Tools | ✅ Готово | 1 |
| Tasks | ✅ Готово | 1 |
| Models | ✅ Готово | 1 |
| Prompts | ✅ Готово | 1 |
| Services | ✅ Готово | 1 |
| Coordinator | ✅ Готово | 1 |
| Utils | ✅ Готово | 1 |
| CLI | ⏳ Ожидает | - |
| Real Tools | ⏳ Ожидает | - |

Всего создано: **8 файлов** ядра агента
