"""Checks against the B5 contract, shared by model.run() and speech.transcribe() (PRD B5).

One place for the schema and the error wording, so the model and speech interfaces cannot drift
apart.
"""

from __future__ import annotations

import json
import time
from functools import cache
from pathlib import Path
from typing import Any, Final

from jsonschema import Draft202012Validator
from jsonschema.exceptions import best_match

B5_SCHEMA_PATH: Final = (
    Path(__file__).resolve().parents[2] / "contracts" / "model-interface.v1.schema.json"
)


@cache
def b5_validator() -> Draft202012Validator:
    """The whole B5 schema: a meta record or a transcript (it picks the shape itself)."""
    schema = json.loads(B5_SCHEMA_PATH.read_text(encoding="utf-8"))
    return Draft202012Validator(schema)


def first_problem(validator: Draft202012Validator, instance: Any) -> str | None:
    """The first problem, named by its place in the SCHEMA only.

    The schema is code we wrote; the instance is learner input or model output. The place in the
    instance (absolute_path) can hold keys the model or learner chose, and error.message quotes
    values, so neither is ever used.
    """
    error = best_match(validator.iter_errors(instance))
    if error is None:
        return None
    return f"'{error.validator}' at schema path {list(error.absolute_schema_path) or 'top level'}"


def elapsed_ms(started: float) -> int:
    """Milliseconds since `started` (a perf_counter value), rounded to a whole number."""
    return round((time.perf_counter() - started) * 1000)
