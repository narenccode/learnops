"""Every model call attempt is logged (PRD B5.3), and required logging is never skipped.

Outside LEARNOPS_ENV=test, run() refuses before any model call when no logger is configured. In a
test run it falls back to an in-memory logger. Failed attempts are recorded with null usage, never
0 (decision record 0001 #1). Records and repr() never carry inputs, prompts or model output.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

from model_interface.call_log import (
    CallRecord,
    InMemoryCallLogger,
    configure_call_logger,
    get_call_logger,
)
from model_interface.config import ConfigError
from model_interface.errors import (
    CallLoggerMissing,
    InvalidMeta,
    InvalidOutput,
    ProviderUnavailable,
)
from model_interface.prompts import PROMPTS_DIR, load_prompt
from model_interface.providers import (
    FakeProvider,
    LocalProvider,
    ProviderRequest,
    ProviderResponse,
    TransportReply,
    configure_provider,
    get_provider,
)
from model_interface.registry import TaskRegistry
from model_interface.runner import Result, run

from .echo_task import ECHO_OUTPUT

B5_SCHEMA = (
    Path(__file__).resolve().parents[3] / "contracts" / "model-interface.v1.schema.json"
)
INPUTS = {"text": "a learner's private answer"}
SECRET_OUTPUT = "private model text"
NULL_USAGE = {"input_tokens": None, "output_tokens": None, "cost_estimate": None}


class Transport:
    """Counts calls, so a test can prove nothing was sent."""

    def __init__(self, reply: TransportReply | None = None) -> None:
        self.reply = reply or TransportReply(text='{"echo": "ok"}')
        self.calls = 0

    def complete(self, **_: Any) -> TransportReply:
        self.calls += 1
        return self.reply


def local(transport: Transport) -> LocalProvider:
    return LocalProvider(
        url="http://ai.lab.invalid:11434", model="m", transport=transport
    )


def usage(record: CallRecord) -> dict[str, Any]:
    return {key: record.meta[key] for key in NULL_USAGE}


@pytest.fixture
def fake(fake_env: None) -> FakeProvider:
    shared = get_provider()
    assert isinstance(shared, FakeProvider)
    return shared


# --- missing logger ------------------------------------------------------------------------


@pytest.mark.parametrize("environment", ["lab", "production", None])
def test_run_refuses_without_a_logger_outside_a_test_run(
    registry: TaskRegistry, monkeypatch: pytest.MonkeyPatch, environment: str | None
) -> None:
    if environment is not None:
        monkeypatch.setenv("LEARNOPS_ENV", environment)
    transport = Transport()
    with pytest.raises(CallLoggerMissing, match="Nothing was sent to the model"):
        run(
            "example_echo",
            INPUTS,
            ECHO_OUTPUT,
            provider=local(transport),
            registry=registry,
        )
    assert transport.calls == 0  # refused before any model call


def test_a_configured_logger_is_used_outside_a_test_run(
    registry: TaskRegistry, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("LEARNOPS_ENV", "lab")
    logger = InMemoryCallLogger()
    configure_call_logger(logger)
    run(
        "example_echo",
        INPUTS,
        ECHO_OUTPUT,
        provider=local(Transport()),
        registry=registry,
    )
    assert [r.outcome for r in logger.records] == ["ok"]


def test_a_logger_passed_to_the_call_is_used_outside_a_test_run(
    registry: TaskRegistry, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("LEARNOPS_ENV", "production")
    logger = InMemoryCallLogger()
    run(
        "example_echo",
        INPUTS,
        ECHO_OUTPUT,
        provider=local(Transport()),
        registry=registry,
        logger=logger,
    )
    assert len(logger.records) == 1


def test_a_test_run_falls_back_to_the_in_memory_logger(
    registry: TaskRegistry, fake: FakeProvider
) -> None:
    fake.add_response("example_echo", INPUTS, {"echo": "ok"})
    run("example_echo", INPUTS, ECHO_OUTPUT, registry=registry)
    logger = get_call_logger()
    assert isinstance(logger, InMemoryCallLogger)
    assert [r.outcome for r in logger.records] == ["ok"]


def test_the_in_memory_fallback_does_not_survive_leaving_the_test_run(
    registry: TaskRegistry, fake: FakeProvider, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Using the fallback once must not leave it in place for a later non-test environment."""
    fake.add_response("example_echo", INPUTS, {"echo": "ok"})
    run("example_echo", INPUTS, ECHO_OUTPUT, registry=registry)
    monkeypatch.setenv("LEARNOPS_ENV", "lab")
    with pytest.raises(CallLoggerMissing):
        get_call_logger()


def test_a_logger_that_fails_stops_the_call_from_returning(
    registry: TaskRegistry, fake: FakeProvider
) -> None:
    class Broken:
        def record(self, record: CallRecord) -> None:
            raise OSError("log store down")

    fake.add_response("example_echo", INPUTS, {"echo": "ok"})
    with pytest.raises(OSError, match="log store down"):
        run("example_echo", INPUTS, ECHO_OUTPUT, registry=registry, logger=Broken())


# --- every attempt is logged ---------------------------------------------------------------


def test_success_is_logged_with_b5_meta(
    registry: TaskRegistry, fake: FakeProvider
) -> None:
    fake.add_response("example_echo", INPUTS, {"echo": "ok"})
    logger = InMemoryCallLogger()
    result = run("example_echo", INPUTS, ECHO_OUTPUT, registry=registry, logger=logger)
    (record,) = logger.records
    assert (record.task, record.attempt, record.outcome) == ("example_echo", 1, "ok")
    assert record.meta == result.meta


def test_provider_failure_is_logged_with_null_usage_and_raised(
    registry: TaskRegistry, fake: FakeProvider
) -> None:
    fake.fail_next(ProviderUnavailable("down"))
    logger = InMemoryCallLogger()
    with pytest.raises(ProviderUnavailable, match="down"):
        run("example_echo", INPUTS, ECHO_OUTPUT, registry=registry, logger=logger)
    (record,) = logger.records
    assert (record.attempt, record.outcome) == (1, "provider_error")
    assert usage(record) == NULL_USAGE
    assert record.meta["provider"] == "fake"
    assert record.meta["prompt_version"] == "example_echo/v1"


def test_an_unexpected_provider_exception_is_logged_and_raised(
    registry: TaskRegistry,
) -> None:
    """A provider that raises something other than a ModelError is still one logged attempt."""

    class Exploding:
        name = "local"
        model = "m"

        def complete(self, request: ProviderRequest) -> ProviderResponse:
            raise ValueError("bug in a provider")

    logger = InMemoryCallLogger()
    with pytest.raises(ValueError, match="bug in a provider"):
        run(
            "example_echo",
            INPUTS,
            ECHO_OUTPUT,
            provider=Exploding(),  # type: ignore[arg-type]
            registry=registry,
            logger=logger,
        )
    assert [r.outcome for r in logger.records] == ["provider_error"]


def test_failure_records_are_valid_b5_meta(
    registry: TaskRegistry, fake: FakeProvider
) -> None:
    """Null usage is what B5 allows for "not reported", so a failure record stays contract-valid."""
    fake.fail_next(ProviderUnavailable("down"))
    logger = InMemoryCallLogger()
    with pytest.raises(ProviderUnavailable):
        run("example_echo", INPUTS, ECHO_OUTPUT, registry=registry, logger=logger)
    validator = Draft202012Validator(json.loads(B5_SCHEMA.read_text(encoding="utf-8")))
    assert [e.message for e in validator.iter_errors(logger.records[0].meta)] == []


def test_invalid_meta_is_logged_with_null_usage_and_raised(
    registry: TaskRegistry,
) -> None:
    transport = Transport(TransportReply(text='{"echo": "ok"}', input_tokens=-1))
    logger = InMemoryCallLogger()
    with pytest.raises(InvalidMeta):
        run(
            "example_echo",
            INPUTS,
            ECHO_OUTPUT,
            provider=local(transport),
            registry=registry,
            logger=logger,
        )
    (record,) = logger.records
    assert record.outcome == "invalid_meta"
    assert usage(record) == NULL_USAGE  # the bad -1 is not stored


def test_a_provider_failure_on_the_retry_is_logged_as_attempt_two(
    registry: TaskRegistry, fake: FakeProvider
) -> None:
    fake.add_response("example_echo", INPUTS, "not json")

    class FailsOnRetry:
        name = "fake"
        model = "m"
        calls = 0

        def complete(self, request: ProviderRequest) -> ProviderResponse:
            self.calls += 1
            if self.calls == 2:
                raise ProviderUnavailable("down")
            return fake.complete(request)

    logger = InMemoryCallLogger()
    with pytest.raises(ProviderUnavailable):
        run(
            "example_echo",
            INPUTS,
            ECHO_OUTPUT,
            provider=FailsOnRetry(),  # type: ignore[arg-type]
            registry=registry,
            logger=logger,
        )
    assert [(r.attempt, r.outcome) for r in logger.records] == [
        (1, "invalid_output"),
        (2, "provider_error"),
    ]


def test_invalid_output_keeps_the_usage_the_provider_reported(
    registry: TaskRegistry, fake: FakeProvider
) -> None:
    """The model did answer, so its usage is known and kept (0 from the fake, not null)."""
    fake.add_response("example_echo", INPUTS, "not json")
    logger = InMemoryCallLogger()
    with pytest.raises(InvalidOutput):
        run("example_echo", INPUTS, ECHO_OUTPUT, registry=registry, logger=logger)
    assert [usage(r)["cost_estimate"] for r in logger.records] == [0.0, 0.0]


def test_failed_attempts_log_no_content(
    registry: TaskRegistry, fake: FakeProvider
) -> None:
    fake.add_response("example_echo", INPUTS, f"not json {SECRET_OUTPUT}")
    logger = InMemoryCallLogger()
    with pytest.raises(InvalidOutput):
        run("example_echo", INPUTS, ECHO_OUTPUT, registry=registry, logger=logger)
    logged = json.dumps([[r.task, r.outcome, r.meta] for r in logger.records])
    assert "private answer" not in logged and SECRET_OUTPUT not in logged


# --- shared provider -----------------------------------------------------------------------


def test_the_shared_provider_is_kept_between_calls(fake: FakeProvider) -> None:
    assert get_provider() is fake


def test_the_guard_runs_again_on_every_get_provider(
    fake: FakeProvider, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A cached fake is not handed out once the environment stops being a test run."""
    monkeypatch.setenv("LEARNOPS_ENV", "lab")
    with pytest.raises(ConfigError, match="for automated tests only"):
        get_provider()


def test_a_cached_fake_is_replaced_when_the_setting_changes(
    fake: FakeProvider, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("MODEL_PROVIDER", "hosted")
    with pytest.raises(ProviderUnavailable, match="Q19"):
        get_provider()


def test_a_configured_provider_is_used_by_the_prd_call_shape(
    registry: TaskRegistry, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("MODEL_PROVIDER", "local")
    transport = Transport()
    configure_provider(local(transport))
    logger = InMemoryCallLogger()
    run("example_echo", INPUTS, ECHO_OUTPUT, registry=registry, logger=logger)
    assert transport.calls == 1


# --- repr privacy --------------------------------------------------------------------------


def test_repr_of_a_request_shows_no_prompt_or_inputs() -> None:
    request = ProviderRequest(
        task="t",
        prompt="SECRET PROMPT",
        prompt_version="t/v1",
        inputs=INPUTS,
        output_schema=ECHO_OUTPUT,
    )
    shown = repr(request)
    assert "SECRET PROMPT" not in shown and "private answer" not in shown
    assert "t/v1" in shown


def test_repr_of_a_response_shows_no_text() -> None:
    response = ProviderResponse(
        text=SECRET_OUTPUT, input_tokens=1, output_tokens=2, cost_estimate=0.0
    )
    assert SECRET_OUTPUT not in repr(response)
    assert "input_tokens=1" in repr(response)


def test_repr_of_a_transport_reply_shows_no_text() -> None:
    assert SECRET_OUTPUT not in repr(TransportReply(text=SECRET_OUTPUT))


def test_repr_of_a_result_shows_no_data(
    registry: TaskRegistry, fake: FakeProvider
) -> None:
    fake.add_response("example_echo", INPUTS, {"echo": SECRET_OUTPUT})
    result = run("example_echo", INPUTS, ECHO_OUTPUT, registry=registry)
    assert isinstance(result, Result)
    assert SECRET_OUTPUT not in repr(result)
    assert "prompt_version" in repr(result)
    assert result.data == {"echo": SECRET_OUTPUT}  # hidden from repr, still available


def test_repr_of_a_prompt_shows_no_text() -> None:
    prompt = load_prompt("example_echo", PROMPTS_DIR / "example_echo")
    assert "TEST-ONLY" not in repr(prompt)
    assert "example_echo/v1" in repr(prompt)
