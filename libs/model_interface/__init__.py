"""Shared model and speech interface (PRD B5). FR-M-01 skeleton, built in steps.

This part provides the error family, the messages, the provider settings and the transcript
checks. The registry, providers and run() follow in later pull requests.
"""

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

__all__ = [
    "CallLoggerMissing",
    "DuplicateTask",
    "InvalidInput",
    "InvalidMeta",
    "InvalidOutput",
    "InvalidTaskName",
    "ModelError",
    "PromptError",
    "ProviderUnavailable",
    "SchemaMismatch",
    "UnregisteredTask",
]
