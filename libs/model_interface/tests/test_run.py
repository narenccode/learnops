"""model.run (PRD B5.1, B5.2): validated output, one retry then a clear error, B5 meta, logging."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

from model_interface import runner as run_module
from model_interface.call_log import InMemoryCallLogger
from model_interface.config import ConfigError
from model_interface.errors import (
    InvalidInput,
    InvalidMeta,
    InvalidOutput,
    ProviderUnavailable,
    SchemaMismatch,
    UnregisteredTask,
)
from model_interface.providers import FakeProvider, LocalProvider, TransportReply
from model_interface.registry import TaskRegistry
from model_interface.runner import run

from .echo_task import ECHO_OUTPUT

B5_SCHEMA = (
    Path(__file__).resolve().parents[3] / "contracts" / "model-interface.v1.schema.json"
)
INPUTS = {"text": "a learner's private answer"}


def b5_errors(meta: dict[str, Any]) -> list[str]:
    validator = Draft202012Validator(json.loads(B5_SCHEMA.read_text(encoding="utf-8")))
    return [e.message for e in validator.iter_errors(meta)]


@pytest.fixture
def fake(fake_env: None) -> FakeProvider:
    return FakeProvider()


def test_valid_output_returns_data_and_b5_meta(
    registry: TaskRegistry, fake: FakeProvider
) -> None:
    fake.add_response("example_echo", INPUTS, {"echo": "ok"})
    result = run("example_echo", INPUTS, ECHO_OUTPUT, provider=fake, registry=registry)
    assert result.data == {"echo": "ok"}
    assert b5_errors(result.meta) == []
    assert result.meta["provider"] == "fake"
    assert result.meta["prompt_version"] == "example_echo/v1"
    assert len(fake.requests) == 1


def test_invalid_output_is_retried_once(
    registry: TaskRegistry, fake: FakeProvider
) -> None:
    fake.add_response("example_echo", INPUTS, {"wrong": 1}, {"echo": "ok"})
    logger = InMemoryCallLogger()
    result = run(
        "example_echo",
        INPUTS,
        ECHO_OUTPUT,
        provider=fake,
        registry=registry,
        logger=logger,
    )
    assert result.data == {"echo": "ok"}
    assert [(r.attempt, r.outcome) for r in logger.records] == [
        (1, "invalid_output"),
        (2, "ok"),
    ]


@pytest.mark.parametrize(
    "bad", ["not json", {"echo": 5}, {"echo": "x", "extra": True}, []]
)
def test_invalid_output_twice_raises_and_returns_nothing(
    registry: TaskRegistry, fake: FakeProvider, bad: Any
) -> None:
    fake.add_response("example_echo", INPUTS, bad)
    logger = InMemoryCallLogger()
    with pytest.raises(InvalidOutput, match="on both attempts") as caught:
        run(
            "example_echo",
            INPUTS,
            ECHO_OUTPUT,
            provider=fake,
            registry=registry,
            logger=logger,
        )
    assert len(fake.requests) == 2  # one retry, not more
    assert [r.outcome for r in logger.records] == ["invalid_output", "invalid_output"]
    assert "private answer" not in str(
        caught.value
    )  # the message never carries content


def test_unregistered_task_is_refused_before_any_call(
    registry: TaskRegistry, fake: FakeProvider
) -> None:
    with pytest.raises(UnregisteredTask):
        run("grade_draft", INPUTS, ECHO_OUTPUT, provider=fake, registry=registry)
    assert fake.requests == []


def test_output_schema_must_be_the_registered_one(
    registry: TaskRegistry, fake: FakeProvider
) -> None:
    other = {**ECHO_OUTPUT, "required": []}
    with pytest.raises(SchemaMismatch, match="not the one registered"):
        run("example_echo", INPUTS, other, provider=fake, registry=registry)
    assert fake.requests == []


@pytest.mark.parametrize("inputs", [{}, {"text": 5}, {"text": "a", "extra": 1}])
def test_invalid_inputs_are_refused_before_any_call(
    registry: TaskRegistry, fake: FakeProvider, inputs: dict[str, Any]
) -> None:
    with pytest.raises(InvalidInput, match="nothing was sent"):
        run("example_echo", inputs, ECHO_OUTPUT, provider=fake, registry=registry)
    assert fake.requests == []


def test_provider_failure_is_raised_not_retried(
    registry: TaskRegistry, fake: FakeProvider
) -> None:
    fake.add_response("example_echo", INPUTS, {"echo": "ok"})
    fake.fail_next(ProviderUnavailable("down"))
    with pytest.raises(ProviderUnavailable):
        run("example_echo", INPUTS, ECHO_OUTPUT, provider=fake, registry=registry)
    assert len(fake.requests) == 1


class NegativeTokens:
    def complete(self, **_: Any) -> TransportReply:
        return TransportReply(text='{"echo": "ok"}', input_tokens=-1, output_tokens=3)


def test_meta_that_breaks_the_b5_contract_is_refused(registry: TaskRegistry) -> None:
    provider = LocalProvider(
        url="http://ai.lab.invalid:11434", model="m", transport=NegativeTokens()
    )
    with pytest.raises(InvalidMeta, match="does not match the B5 contract"):
        run("example_echo", INPUTS, ECHO_OUTPUT, provider=provider, registry=registry)


def test_local_meta_reports_unknown_usage_as_null(registry: TaskRegistry) -> None:
    class NoUsage:
        def complete(self, **_: Any) -> TransportReply:
            return TransportReply(text='{"echo": "ok"}')

    provider = LocalProvider(
        url="http://ai.lab.invalid:11434", model="m", transport=NoUsage()
    )
    result = run(
        "example_echo", INPUTS, ECHO_OUTPUT, provider=provider, registry=registry
    )
    assert (result.meta["input_tokens"], result.meta["output_tokens"]) == (None, None)
    assert result.meta["cost_estimate"] == 0.0
    assert b5_errors(result.meta) == []


def test_logger_records_meta_only(registry: TaskRegistry, fake: FakeProvider) -> None:
    fake.add_response("example_echo", INPUTS, {"echo": "model output text"})
    logger = InMemoryCallLogger()
    run(
        "example_echo",
        INPUTS,
        ECHO_OUTPUT,
        provider=fake,
        registry=registry,
        logger=logger,
    )
    (record,) = logger.records
    assert set(record.meta) == {
        "provider",
        "model",
        "input_tokens",
        "output_tokens",
        "latency_ms",
        "cost_estimate",
        "prompt_version",
    }
    logged = json.dumps([record.task, record.attempt, record.outcome, record.meta])
    assert "private answer" not in logged
    assert "model output text" not in logged


def test_default_provider_comes_from_the_guarded_configuration(
    registry: TaskRegistry, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Without an explicit provider, run() uses create_provider(), so the fake rule applies."""
    monkeypatch.setenv("MODEL_PROVIDER", "fake")  # but not a test run
    with pytest.raises(ConfigError, match="fake provider is turned off"):
        run("example_echo", INPUTS, ECHO_OUTPUT, registry=registry)


def test_default_provider_is_used_when_none_is_given(
    registry: TaskRegistry, fake_env: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    configured = FakeProvider()
    configured.add_response("example_echo", INPUTS, {"echo": "ok"})
    monkeypatch.setattr(run_module, "create_provider", lambda: configured)
    assert run("example_echo", INPUTS, ECHO_OUTPUT, registry=registry).data == {
        "echo": "ok"
    }


# --- error messages never carry content ----------------------------------------------------

SECRET_KEY = "Learner wrote: my password is hunter2"
SECRET_VALUE = "private model text about the learner"


@pytest.fixture
def open_registry(tmp_path: Path) -> TaskRegistry:
    """A task whose schemas accept any key, so keys are chosen by the learner or the model."""
    folder = tmp_path / "open_task"
    folder.mkdir()
    (folder / "v1.md").write_text(
        "---\nprompt_version: open_task/v1\n---\nAnswer.\n", encoding="utf-8"
    )
    reg = TaskRegistry()
    reg.register(
        "open_task",
        {"type": "object", "additionalProperties": {"type": "string"}},
        {"type": "object", "additionalProperties": {"type": "integer"}},
        prompt_dir=folder,
    )
    return reg


def shown(error: BaseException) -> str:
    """Everything a log line or a printed traceback would show of this error and its chain."""
    parts = [str(error), repr(error)]
    for linked in (error.__cause__, error.__context__):
        if linked is not None:
            parts += [str(linked), repr(linked)]
    return " ".join(parts)


def test_invalid_output_error_shows_no_model_output(
    open_registry: TaskRegistry, fake: FakeProvider
) -> None:
    inputs = {"q": "x"}
    fake.add_response("open_task", inputs, {SECRET_KEY: SECRET_VALUE})
    with pytest.raises(InvalidOutput) as caught:
        run(
            "open_task",
            inputs,
            open_registry.get("open_task").output_schema,
            provider=fake,
            registry=open_registry,
        )
    text = shown(caught.value)
    assert SECRET_KEY not in text and "hunter2" not in text and SECRET_VALUE not in text
    assert (
        "schema path ['additionalProperties', 'type']" in text
    )  # the place, from our schema
    assert caught.value.__cause__ is None and caught.value.__context__ is None


def test_invalid_output_error_shows_no_raw_text(
    registry: TaskRegistry, fake: FakeProvider
) -> None:
    fake.add_response("example_echo", INPUTS, f"not json: {SECRET_VALUE}")
    with pytest.raises(InvalidOutput) as caught:
        run("example_echo", INPUTS, ECHO_OUTPUT, provider=fake, registry=registry)
    assert SECRET_VALUE not in shown(caught.value)
    assert "output is not JSON" in str(caught.value)


def test_invalid_input_error_shows_no_learner_input(
    open_registry: TaskRegistry, fake: FakeProvider
) -> None:
    with pytest.raises(InvalidInput) as caught:
        run(
            "open_task",
            {SECRET_KEY: 42},
            open_registry.get("open_task").output_schema,
            provider=fake,
            registry=open_registry,
        )
    text = shown(caught.value)
    assert SECRET_KEY not in text and "hunter2" not in text and "42" not in text
    assert fake.requests == []


def test_invalid_meta_error_shows_no_output(registry: TaskRegistry) -> None:
    class BadUsage:
        def complete(self, **_: Any) -> TransportReply:
            return TransportReply(
                text=json.dumps({"echo": SECRET_VALUE}), input_tokens=-1
            )

    provider = LocalProvider(
        url="http://ai.lab.invalid:11434", model="m", transport=BadUsage()
    )
    with pytest.raises(InvalidMeta) as caught:
        run("example_echo", INPUTS, ECHO_OUTPUT, provider=provider, registry=registry)
    assert SECRET_VALUE not in shown(caught.value)
    assert "private answer" not in shown(caught.value)
