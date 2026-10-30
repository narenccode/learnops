"""model.run(task, inputs, output_schema) (PRD B5.1, B5.2).

Steps: look up the registered task; refuse an output_schema that is not the registered one;
validate the inputs before any provider call; find the provider and the call logger, refusing
before any model call if there is no logger outside a test run; call the provider; parse and
validate the output; on invalid output retry once, then raise InvalidOutput. Partial or invalid
output is never returned.

Every attempt is logged (PRD B5.3), also one that fails: a provider failure and meta that breaks
the B5 contract are recorded with null usage, because the usage is not known (decision record 0001
#1), and then raised. If the logger itself fails, that error is raised too, so a call that could
not be logged never returns a result.

Provider failures are not retried here: transport retries, timeouts and the budget guard are
design proposals (grading.md §4.2), not part of this skeleton.
"""

from __future__ import annotations

import copy
import json
import time
from collections.abc import Mapping
from dataclasses import dataclass, field
from functools import cache
from pathlib import Path
from typing import Any, Final

from jsonschema import Draft202012Validator
from jsonschema.exceptions import best_match

from . import messages
from .call_log import CallLogger, CallRecord, resolve_call_logger
from .errors import (
    InvalidInput,
    InvalidMeta,
    InvalidOutput,
    ProviderUnavailable,
    SchemaMismatch,
)
from .providers import (
    Provider,
    ProviderRequest,
    ProviderResponse,
    resolve_provider,
)
from .registry import DEFAULT_REGISTRY, Schema, TaskRegistry

MAX_ATTEMPTS: Final = 2  # PRD B5.2: on invalid output, one retry
B5_SCHEMA_PATH: Final = (
    Path(__file__).resolve().parents[2] / "contracts" / "model-interface.v1.schema.json"
)


@dataclass(frozen=True)
class Result:
    # Validated against the task's output schema. repr() leaves it out: it is model output.
    data: Any = field(repr=False)
    meta: dict[str, Any]  # a B5 model_result_meta record (PRD B5.1)


@cache
def _meta_validator() -> Draft202012Validator:
    schema = json.loads(B5_SCHEMA_PATH.read_text(encoding="utf-8"))
    return Draft202012Validator(schema)


def _problem(validator: Draft202012Validator, instance: Any) -> str | None:
    """The first problem, named by its place in the SCHEMA only.

    The schema is code we wrote; the instance is learner input or model output. The place in the
    instance (absolute_path) can hold keys the model or learner chose, and error.message quotes
    values, so neither is ever used.
    """
    error = best_match(validator.iter_errors(instance))
    if error is None:
        return None
    return f"'{error.validator}' at schema path {list(error.absolute_schema_path) or 'top level'}"


def _refuse_constant(name: str) -> None:
    """NaN and Infinity are not JSON, though Python's parser accepts them by default."""
    raise ValueError(name)


def _parse_output(text: Any, schema: Schema) -> tuple[Any, str | None]:
    # The provider contract says str. Checked here because json.loads would also accept bytes.
    if not isinstance(text, str):
        return None, "output is not text"
    try:
        data = json.loads(text, parse_constant=_refuse_constant)
    except (ValueError, RecursionError):
        return None, "output is not JSON"
    return data, _problem(Draft202012Validator(schema), data)


def _meta(
    provider: Provider,
    version: str,
    latency_ms: int,
    response: ProviderResponse | None = None,
) -> dict[str, Any]:
    """A B5 meta record. Without a response the usage is not known, so it is null, never 0."""
    return {
        "provider": provider.name,
        "model": provider.model,
        "input_tokens": response.input_tokens if response else None,
        "output_tokens": response.output_tokens if response else None,
        "latency_ms": latency_ms,
        "cost_estimate": response.cost_estimate if response else None,
        "prompt_version": version,
    }


def _elapsed_ms(started: float) -> int:
    return round((time.perf_counter() - started) * 1000)


def run(
    task: str,
    inputs: Mapping[str, Any],
    output_schema: Schema,
    *,
    provider: Provider | None = None,
    registry: TaskRegistry = DEFAULT_REGISTRY,
    logger: CallLogger | None = None,
) -> Result:
    """Run one registered task and return validated data with its meta, or raise a ModelError.

    Application services pass neither provider nor logger and get the configured ones; with no
    logger configured outside a test run, the call is refused. Passing a different provider or
    logger is for test runs only, and is refused anywhere else. The logger receives one CallRecord
    per attempt, including failed attempts (meta only).
    """
    spec = registry.get(task)
    if output_schema != spec.output_schema:
        raise SchemaMismatch(messages.SCHEMA_MISMATCH.format(task=task))
    problem = _problem(Draft202012Validator(spec.input_schema), inputs)
    if problem is not None:
        raise InvalidInput(messages.INVALID_INPUT.format(task=task, detail=problem))

    chosen = resolve_provider(provider)
    call_logger = resolve_call_logger(logger)
    version = spec.prompt.prompt_version
    request = ProviderRequest(
        task=task,
        prompt=spec.prompt.text,
        prompt_version=version,
        inputs=copy.deepcopy(dict(inputs)),
        output_schema=spec.output_schema,
    )
    for attempt in range(1, MAX_ATTEMPTS + 1):
        started = time.perf_counter()
        try:
            response = chosen.complete(request)
            if not isinstance(response, ProviderResponse):
                raise ProviderUnavailable(
                    messages.BAD_PROVIDER_RESPONSE.format(provider=chosen.name)
                )
        except Exception:
            meta = _meta(chosen, version, _elapsed_ms(started))
            call_logger.record(CallRecord(task, attempt, "provider_error", meta))
            raise
        latency_ms = _elapsed_ms(started)
        meta = _meta(chosen, version, latency_ms, response)
        meta_problem = _problem(_meta_validator(), meta)
        if meta_problem is not None:
            # The reported usage broke the contract, so it is dropped from the record.
            usage_unknown = _meta(chosen, version, latency_ms)
            call_logger.record(CallRecord(task, attempt, "invalid_meta", usage_unknown))
            raise InvalidMeta(
                messages.INVALID_META.format(provider=chosen.name, detail=meta_problem)
            )
        data, problem = _parse_output(response.text, spec.output_schema)
        if problem is None:
            call_logger.record(CallRecord(task, attempt, "ok", meta))
            return Result(data=data, meta=meta)
        call_logger.record(CallRecord(task, attempt, "invalid_output", meta))
    raise InvalidOutput(
        messages.INVALID_OUTPUT.format(
            task=task, detail=problem, prompt_version=version
        )
    )
