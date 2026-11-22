"""Shared model and speech interface (PRD B5). FR-M-01 skeleton, built in steps.

This part adds the task registry, the prompt loader and the call log. The providers and run()
follow in later pull requests.
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
    "get_call_logger",
    "get_task",
    "register_task",
]
