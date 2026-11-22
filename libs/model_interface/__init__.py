"""Shared model and speech interface (PRD B5). FR-M-01 skeleton, built in steps.

This part adds the providers. run() follows in the next pull request.
"""

from .call_log import (
    CallLogger,
    CallRecord,
    InMemoryCallLogger,
    configure_call_logger,
    get_call_logger,
)
from .errors import (
    CallLoggerMissing,
    DuplicateTask,
    InvalidInput,
    InvalidMeta,
    InvalidOutput,
    InvalidTaskName,
    ModelError,
    PromptError,
    ProviderUnavailable,
    SchemaMismatch,
    UnregisteredTask,
)
from .providers import configure_provider, create_provider, get_provider
from .registry import TaskRegistry, TaskSpec, get_task, register_task

__all__ = [
    "CallLogger",
    "CallLoggerMissing",
    "CallRecord",
    "DuplicateTask",
    "InMemoryCallLogger",
    "InvalidInput",
    "InvalidMeta",
    "InvalidOutput",
    "InvalidTaskName",
    "ModelError",
    "PromptError",
    "ProviderUnavailable",
    "SchemaMismatch",
    "TaskRegistry",
    "TaskSpec",
    "UnregisteredTask",
    "configure_call_logger",
    "configure_provider",
    "create_provider",
    "get_call_logger",
    "get_provider",
    "get_task",
    "register_task",
]
