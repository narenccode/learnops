"""Call logging (PRD B5.3: "every call logs meta to shared.model_calls (no raw learner content)").

A CallRecord can hold only the task name, the attempt number, the outcome and a B5 meta record, so
inputs, prompts and model output cannot reach a log through it. Every attempt is recorded, also a
failed one; usage that is not known is null, never 0 (decision record 0001 #1).

Required logging is never skipped. get_call_logger() returns the configured logger; in a test run
(LEARNOPS_ENV=test) with none configured it returns an in-memory one; anywhere else, including with
LEARNOPS_ENV unset, it raises CallLoggerMissing, so run() refuses before any model call.

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
from .config import ENV_VARIABLE, TEST_ENVIRONMENT
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


def configure_call_logger(logger: CallLogger) -> None:
    """Set the logger every run() uses unless a call passes its own."""
    global _configured
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
    if os.environ.get(ENV_VARIABLE, "").strip() == TEST_ENVIRONMENT:
        return _test_logger
    raise CallLoggerMissing(messages.NO_CALL_LOGGER)
