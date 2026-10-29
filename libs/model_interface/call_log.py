"""Call logging (PRD B5.3: "every call logs meta to shared.model_calls (no raw learner content)").

A CallRecord can hold only the task name, the attempt number, the outcome and the B5 meta
record, so inputs, prompts and model output cannot reach a log through it. The Postgres logger
for shared.model_calls waits for the migration tool and shared schema (design Q36); until then
services have no database logger and tests use InMemoryCallLogger.
"""

from __future__ import annotations

import copy
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Literal, Protocol

Outcome = Literal["ok", "invalid_output"]


@dataclass(frozen=True)
class CallRecord:
    task: str
    attempt: int
    outcome: Outcome
    meta: Mapping[str, Any]  # a B5 model_result_meta record, already validated


class CallLogger(Protocol):
    def record(self, record: CallRecord) -> None: ...


@dataclass
class InMemoryCallLogger:
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
