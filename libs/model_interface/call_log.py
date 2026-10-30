"""Call logging (PRD B5.3: "every call logs meta to shared.model_calls (no raw learner content)").

A CallRecord can hold only the task name, the attempt number, the outcome and a B5 meta record, so
inputs, prompts and model output cannot reach a log through it. Every attempt is recorded, also a
failed one; usage that is not known is null, never 0 (decision record 0001 #1).

Required logging is never skipped. get_call_logger() returns the configured logger; in a test run
(LEARNOPS_ENV=test) with none configured it returns an in-memory one; anywhere else, including with
LEARNOPS_ENV unset, it raises CallLoggerMissing, so run() refuses before any model call.

Logger injection is for tests. Outside a test run, a logger passed to run() must be the configured
one, so a call cannot bypass the shared log, and InMemoryCallLogger cannot be configured at all,
because its records would not reach shared.model_calls.

The PostgreSQL logger for shared.model_calls waits for the migration tool and shared schema
(design Q36). Until it exists, no lab or production service can make a logged model call.
"""

from __future__ import annotations

import copy
import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Literal, Protocol

from . import messages
from .config import ENV_VARIABLE, TEST_ENVIRONMENT, ConfigError
from .errors import CallLoggerMissing

Outcome = Literal["ok", "invalid_output", "provider_error", "invalid_meta"]


@dataclass(frozen=True)
class CallRecord:
    task: str
    attempt: int
    outcome: Outcome
    # B5 model_result_meta fields. For provider_error and invalid_meta the usage fields are null.
    meta: Mapping[str, Any]


class CallLogger(Protocol):
    def record(self, record: CallRecord) -> None: ...


@dataclass
class InMemoryCallLogger:
    """For tests. It is not shared.model_calls and keeps every record in memory."""

    records: list[CallRecord] = field(default_factory=list)

    def record(self, record: CallRecord) -> None:
        self.records.append(
            CallRecord(
                record.task,
                record.attempt,
                record.outcome,
                copy.deepcopy(dict(record.meta)),
            )
        )


_configured: CallLogger | None = None
_test_logger = InMemoryCallLogger()


def is_test_run() -> bool:
    """True only with LEARNOPS_ENV=test. Unset counts as "not test", as in config.py."""
    return os.environ.get(ENV_VARIABLE, "").strip() == TEST_ENVIRONMENT


def configure_call_logger(logger: CallLogger) -> None:
    """Set the logger every run() uses. InMemoryCallLogger is refused outside a test run."""
    global _configured
    if isinstance(logger, InMemoryCallLogger) and not is_test_run():
        raise ConfigError(messages.IN_MEMORY_LOGGER_TEST_ONLY)
    _configured = logger


def reset_call_logger() -> None:
    """Forget the configured logger and the in-memory test records. For tests."""
    global _configured
    _configured = None
    _test_logger.records.clear()


def get_call_logger() -> CallLogger:
    """The configured logger, or the in-memory one in a test run; otherwise CallLoggerMissing."""
    if _configured is not None:
        return _configured
    if is_test_run():
        return _test_logger
    raise CallLoggerMissing(messages.NO_CALL_LOGGER)


def resolve_call_logger(logger: CallLogger | None) -> CallLogger:
    """The logger for one call. Passing one is for tests; a service gets the configured one only."""
    if logger is None:
        return get_call_logger()
    if is_test_run():
        return logger
    if logger is not get_call_logger():
        raise ConfigError(messages.CALL_LOGGER_NOT_CONFIGURED)
    return logger
