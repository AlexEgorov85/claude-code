"""
Claude Code Agent - Python Implementation
Ядро агента: полная функциональность
"""

from .core import (
    AgentMode,
    ModelConfig,
    SessionConfig,
    SessionState,
    AgentCore
)

from .tools import (
    ToolStatus,
    ToolInput,
    ToolOutput,
    ToolCall,
    BaseTool,
    ToolRegistry,
    PermissionType,
    ToolPermission
)

from .tasks import (
    TaskStatus,
    TaskType,
    TaskProgress,
    TaskResult,
    Task,
    TaskManager,
    AgentExecutor
)

from .models import (
    ModelProvider,
    ModelCapability,
    ModelInfo,
    TokenUsage,
    RateLimit,
    ModelConfig as ModelConfigInfo,
    ModelManager
)

from .prompts import (
    PromptSection,
    SystemPromptConfig,
    SystemPromptBuilder,
    PROMPT_TEMPLATES,
    get_prompt_for_mode
)

from .services import (
    APIResponse,
    APIClient,
    MCPServerStatus,
    MCPServer,
    MCPClient,
    OAuthToken,
    OAuthClient,
    TelemetryEvent,
    TelemetryData,
    TelemetryClient,
    ContextCompressor,
    Summarizer
)

from .coordinator import (
    CoordinatorMode,
    AgentRole,
    CoordinationTask,
    AgentState,
    MultiAgentCoordinator,
    BackgroundTaskManager
)

from .utils import (
    setup_logger,
    read_file,
    write_file,
    file_exists,
    get_file_hash,
    find_files,
    to_json,
    from_json,
    load_json_file,
    save_json_file,
    truncate,
    indent,
    strip_ansi,
    async_sleep,
    run_in_executor,
    now_iso,
    parse_iso,
    format_duration,
    get_env,
    get_env_bool,
    require_env,
    resolve_path,
    is_subpath,
    retry,
    timing
)


__version__ = "0.1.0"
__author__ = "Claude Code Migration Team"

__all__ = [
    # Core
    "AgentMode",
    "ModelConfig",
    "SessionConfig",
    "SessionState",
    "AgentCore",
    # Tools
    "ToolStatus",
    "ToolInput",
    "ToolOutput",
    "ToolCall",
    "BaseTool",
    "ToolRegistry",
    "PermissionType",
    "ToolPermission",
    # Tasks
    "TaskStatus",
    "TaskType",
    "TaskProgress",
    "TaskResult",
    "Task",
    "TaskManager",
    "AgentExecutor",
    # Models
    "ModelProvider",
    "ModelCapability",
    "ModelInfo",
    "TokenUsage",
    "RateLimit",
    "ModelConfigInfo",
    "ModelManager",
    # Prompts
    "PromptSection",
    "SystemPromptConfig",
    "SystemPromptBuilder",
    "PROMPT_TEMPLATES",
    "get_prompt_for_mode",
    # Services
    "APIResponse",
    "APIClient",
    "MCPServerStatus",
    "MCPServer",
    "MCPClient",
    "OAuthToken",
    "OAuthClient",
    "TelemetryEvent",
    "TelemetryData",
    "TelemetryClient",
    "ContextCompressor",
    "Summarizer",
    # Coordinator
    "CoordinatorMode",
    "AgentRole",
    "CoordinationTask",
    "AgentState",
    "MultiAgentCoordinator",
    "BackgroundTaskManager",
    # Utils
    "setup_logger",
    "read_file",
    "write_file",
    "file_exists",
    "get_file_hash",
    "find_files",
    "to_json",
    "from_json",
    "load_json_file",
    "save_json_file",
    "truncate",
    "indent",
    "strip_ansi",
    "async_sleep",
    "run_in_executor",
    "now_iso",
    "parse_iso",
    "format_duration",
    "get_env",
    "get_env_bool",
    "require_env",
    "resolve_path",
    "is_subpath",
    "retry",
    "timing",
    # Meta
    "__version__",
    "__author__"
]
