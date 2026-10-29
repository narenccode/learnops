"""Shared model and speech interface (PRD B5). FR-M-01 skeleton; speech (FR-M-02) not yet built.

    import model_interface as model
    result = model.run(task="...", inputs={...}, output_schema=spec.output_schema)

Every AI call in LearnOps goes through run() (root CLAUDE.md rule 6).
"""

from .errors import (
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

# The module is runner.py, not run.py: a module named run would be shadowed by this function, so
# "import model_interface.run" would quietly return the function instead of a module.
from .runner import Result, run

__all__ = [
    "DuplicateTask",
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
    "get_task",
    "register_task",
    "run",
]
