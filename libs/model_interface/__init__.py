"""Shared model and speech interface (PRD B5). FR-M-01 skeleton; speech (FR-M-02) not yet built.

    import model_interface as model
    result = model.run(task="...", inputs={...}, output_schema=spec.output_schema)

Every AI call in LearnOps goes through run() (root CLAUDE.md rule 6). See README.md in this folder.
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

# The module is runner.py, not run.py: a module named run would be shadowed by this function, so
# "import model_interface.run" would quietly return the function instead of a module.
from .runner import Result, run

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
    "Result",
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
    "run",
]
