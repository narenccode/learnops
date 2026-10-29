"""Typed errors of the model interface (PRD B5.2: "a clear error, never a silent partial result").

Every error derives from ModelError so callers can catch one type. Messages never contain inputs,
prompts or model output (PRD B5.3).
"""

from __future__ import annotations


class ModelError(Exception):
    """Base class of every model-interface error."""


class UnregisteredTask(ModelError):
    """run() or get_task() was called with a task name that is not registered."""


class DuplicateTask(ModelError):
    """A task name was registered twice."""


class InvalidTaskName(ModelError):
    """A task name does not follow the naming rule."""


class SchemaMismatch(ModelError):
    """A task's schema is invalid, or run() got an output_schema that is not the registered one."""


class InvalidInput(ModelError):
    """The inputs do not match the task's input schema; nothing was sent to the model."""


class InvalidOutput(ModelError):
    """The model's output did not match the output schema on both attempts (one retry)."""


class InvalidMeta(ModelError):
    """A provider produced call metadata that does not match the B5 contract."""


class PromptError(ModelError):
    """A prompt file is missing, or its version header does not match its file name."""


class ProviderUnavailable(ModelError):
    """The provider could not be reached, or is not integrated yet."""
