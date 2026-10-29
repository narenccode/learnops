"""model.run(task, inputs, output_schema) (PRD B5.1, B5.2).

Steps: look up the registered task; refuse an output_schema that is not the registered one;
validate the inputs before any provider call; call the provider; parse and validate the output;
on invalid output retry once, then raise InvalidOutput. Partial or invalid output is never
returned. Every attempt's meta is checked against the B5 contract and given to the call logger.

Provider failures (ProviderUnavailable) are not retried here: transport retries, timeouts and the
budget guard are design proposals (grading.md §4.2), not part of this skeleton.
"""

from __future__ import annotations

import copy
import json
import time
from collections.abc import Mapping
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import Any, Final

from jsonschema import Draft202012Validator
from jsonschema.exceptions import best_match

from . import messages
from .call_log import CallLogger, CallRecord, Outcome
from .errors import InvalidInput, InvalidMeta, InvalidOutput, SchemaMismatch
from .providers import Provider, ProviderRequest, ProviderResponse, create_provider
from .registry import DEFAULT_REGISTRY, Schema, TaskRegistry

MAX_ATTEMPTS: Final = 2  # PRD B5.2: on invalid output, one retry
B5_SCHEMA_PATH: Final = (
    Path(__file__).resolve().parents[2] / "contracts" / "model-interface.v1.schema.json"
)


@dataclass(frozen=True)
class Result:
    data: Any  # validated against the task's output schema
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


def _parse_output(text: str, schema: Schema) -> tuple[Any, str | None]:
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return None, "output is not JSON"
    return data, _problem(Draft202012Validator(schema), data)


def _meta(
    provider: Provider, response: ProviderResponse, latency_ms: int, version: str
) -> dict[str, Any]:
    meta: dict[str, Any] = {
        "provider": provider.name,
        "model": provider.model,
        "input_tokens": response.input_tokens,
        "output_tokens": response.output_tokens,
        "latency_ms": latency_ms,
        "cost_estimate": response.cost_estimate,
        "prompt_version": version,
    }
    problem = _problem(_meta_validator(), meta)
    if problem is not None:
        raise InvalidMeta(
            messages.INVALID_META.format(provider=provider.name, detail=problem)
        )
    return meta


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

    provider defaults to create_provider(), the configured provider. logger receives one
    CallRecord per attempt (meta only).
    """
    spec = registry.get(task)
    if output_schema != spec.output_schema:
        raise SchemaMismatch(messages.SCHEMA_MISMATCH.format(task=task))
    problem = _problem(Draft202012Validator(spec.input_schema), inputs)
    if problem is not None:
        raise InvalidInput(messages.INVALID_INPUT.format(task=task, detail=problem))

    chosen = provider if provider is not None else create_provider()
    request = ProviderRequest(
        task=task,
        prompt=spec.prompt.text,
        prompt_version=spec.prompt.prompt_version,
        inputs=copy.deepcopy(dict(inputs)),
        output_schema=spec.output_schema,
    )
    for attempt in range(1, MAX_ATTEMPTS + 1):
        started = time.perf_counter()
        response = chosen.complete(request)
        latency_ms = round((time.perf_counter() - started) * 1000)
        meta = _meta(chosen, response, latency_ms, spec.prompt.prompt_version)
        data, problem = _parse_output(response.text, spec.output_schema)
        if logger is not None:
            outcome: Outcome = "ok" if problem is None else "invalid_output"
            logger.record(
                CallRecord(task=task, attempt=attempt, outcome=outcome, meta=meta)
            )
        if problem is None:
            return Result(data=data, meta=meta)
    raise InvalidOutput(
        messages.INVALID_OUTPUT.format(
            task=task, detail=problem, prompt_version=spec.prompt.prompt_version
        )
    )
