"""One interface over the local, hosted and fake providers (PRD B5.1, B5.2).

Every provider gives the same validated result and logs through the shared logger. There is no
fallback between providers. An API key never reaches a repr(), an error or a log record. No real
endpoint, SDK or key is used: the transports here are test doubles (design Q19).
"""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

from model_interface.call_log import InMemoryCallLogger
from model_interface.config import ConfigError
from model_interface.errors import ProviderUnavailable
from model_interface.providers import (
    FakeProvider,
    HostedProvider,
    LocalProvider,
    Provider,
    ProviderRequest,
    TransportError,
    TransportReply,
    configure_provider,
    create_provider,
    get_provider,
)
from model_interface.registry import TaskRegistry
from model_interface.runner import Result, run

from .echo_task import ECHO_OUTPUT

B5_SCHEMA = (
    Path(__file__).resolve().parents[3] / "contracts" / "model-interface.v1.schema.json"
)
INPUTS = {"text": "a learner's private answer"}
SENTINEL_KEY = "sentinel-not-a-real-key-123"
URL = "http://ai.lab.invalid:11434"


class Transport:
    """A test double for a real transport. Records calls, so a test can prove none happened."""

    def __init__(
        self,
        reply: TransportReply | None = None,
        error: Exception | None = None,
    ) -> None:
        self.reply = reply or TransportReply(text='{"echo": "ok"}')
        self.error = error
        self.calls: list[dict[str, Any]] = []

    def complete(self, **kwargs: Any) -> TransportReply:
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return self.reply


def request() -> ProviderRequest:
    return ProviderRequest(
        task="example_echo",
        prompt="p",
        prompt_version="example_echo/v1",
        inputs=INPUTS,
        output_schema=ECHO_OUTPUT,
    )


def b5_errors(meta: dict[str, Any]) -> list[str]:
    validator = Draft202012Validator(json.loads(B5_SCHEMA.read_text(encoding="utf-8")))
    return [e.message for e in validator.iter_errors(meta)]


def local() -> Provider:
    return LocalProvider(url=URL, model="local-model", transport=Transport())


def hosted() -> Provider:
    return HostedProvider(model="hosted-model", transport=Transport())


def fake() -> Provider:
    provider = FakeProvider()
    provider.add_response("example_echo", INPUTS, {"echo": "ok"})
    return provider


# --- the same result from every provider ---------------------------------------------------


@pytest.mark.parametrize(
    ("build", "name"),
    [(local, "local"), (hosted, "hosted"), (fake, "fake")],
    ids=["local", "hosted", "fake"],
)
def test_every_provider_gives_the_same_validated_result_and_logs_it(
    registry: TaskRegistry,
    fake_env: None,
    build: Callable[[], Provider],
    name: str,
) -> None:
    logger = InMemoryCallLogger()
    result = run(
        "example_echo",
        INPUTS,
        ECHO_OUTPUT,
        provider=build(),
        registry=registry,
        logger=logger,
    )
    assert isinstance(result, Result)
    assert result.data == {"echo": "ok"}
    assert b5_errors(result.meta) == []
    assert result.meta["provider"] == name
    assert [(r.outcome, r.meta) for r in logger.records] == [("ok", result.meta)]


def test_a_hosted_failure_is_logged_through_the_shared_logger(
    registry: TaskRegistry,
) -> None:
    provider = HostedProvider(
        model="m", transport=Transport(error=TransportError("down"))
    )
    logger = InMemoryCallLogger()
    with pytest.raises(ProviderUnavailable):
        run(
            "example_echo",
            INPUTS,
            ECHO_OUTPUT,
            provider=provider,
            registry=registry,
            logger=logger,
        )
    (record,) = logger.records
    assert (record.outcome, record.meta["provider"]) == ("provider_error", "hosted")
    assert record.meta["cost_estimate"] is None


# --- hosted provider -----------------------------------------------------------------------


def test_hosted_passes_the_request_to_its_transport_without_a_url() -> None:
    transport = Transport()
    HostedProvider(model="m", transport=transport, timeout_s=5).complete(request())
    assert transport.calls == [
        {
            "model": "m",
            "prompt": "p",
            "inputs": INPUTS,
            "output_schema": ECHO_OUTPUT,
            "timeout_s": 5,
        }
    ]


def test_hosted_keeps_a_reported_cost() -> None:
    reply = TransportReply(text="{}", input_tokens=7, cost_estimate=0.0002)
    response = HostedProvider(model="m", transport=Transport(reply)).complete(request())
    assert (response.input_tokens, response.cost_estimate) == (7, 0.0002)


def test_hosted_cost_not_reported_is_none_never_zero() -> None:
    reply = TransportReply(text="{}")
    response = HostedProvider(model="m", transport=Transport(reply)).complete(request())
    assert response.cost_estimate is None


def test_local_cost_stays_zero_whatever_the_transport_reports() -> None:
    reply = TransportReply(text="{}", cost_estimate=9.0)
    provider = LocalProvider(url=URL, model="m", transport=Transport(reply))
    assert provider.complete(request()).cost_estimate == 0.0


@pytest.mark.parametrize(
    "error",
    [TransportError("secret text"), RuntimeError("secret text"), TimeoutError()],
    ids=lambda e: type(e).__name__,
)
def test_hosted_transport_failure_shows_no_content(error: Exception) -> None:
    provider = HostedProvider(model="m", transport=Transport(error=error))
    with pytest.raises(ProviderUnavailable) as caught:
        provider.complete(request())
    assert "secret text" not in f"{caught.value!s} {caught.value!r}"
    assert type(error).__name__ in str(caught.value)
    assert caught.value.__cause__ is None
    assert caught.value.__suppress_context__ is True


def test_hosted_needs_model_name(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MODEL_PROVIDER", "hosted")
    monkeypatch.setenv("MODEL_HOSTED_API_KEY", SENTINEL_KEY)
    with pytest.raises(ConfigError, match="MODEL_NAME is not set"):
        create_provider(hosted_transport=Transport())


def test_model_name_reaches_hosted_meta(
    registry: TaskRegistry, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("MODEL_PROVIDER", "hosted")
    monkeypatch.setenv("MODEL_NAME", "chosen-model")
    monkeypatch.setenv("MODEL_HOSTED_API_KEY", SENTINEL_KEY)
    provider = create_provider(hosted_transport=Transport())
    result = run(
        "example_echo",
        INPUTS,
        ECHO_OUTPUT,
        provider=provider,
        registry=registry,
        logger=InMemoryCallLogger(),
    )
    assert result.meta["model"] == "chosen-model"


# --- no fallback ---------------------------------------------------------------------------


def test_a_failing_local_provider_never_tries_hosted_or_fake(
    registry: TaskRegistry, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("LEARNOPS_ENV", "test")
    monkeypatch.setenv(
        "MODEL_ALLOW_FAKE", "true"
    )  # the fake is allowed, and still not used
    monkeypatch.setenv("MODEL_PROVIDER", "local")
    monkeypatch.setenv("MODEL_LOCAL_URL", URL)
    monkeypatch.setenv("MODEL_NAME", "m")
    monkeypatch.setenv("MODEL_HOSTED_API_KEY", SENTINEL_KEY)
    local_transport = Transport(error=TransportError("down"))
    hosted_transport = Transport()
    configure_provider(
        create_provider(
            local_transport=local_transport, hosted_transport=hosted_transport
        )
    )
    with pytest.raises(ProviderUnavailable):
        run("example_echo", INPUTS, ECHO_OUTPUT, registry=registry)
    assert len(local_transport.calls) == 1
    assert hosted_transport.calls == []
    assert get_provider().name == "local"


@pytest.mark.parametrize(
    "selected, transports",
    [
        ("local", {"hosted_transport": Transport()}),
        ("hosted", {"local_transport": Transport()}),
    ],
    ids=["local", "hosted"],
)
def test_a_transport_for_the_other_provider_is_never_used(
    monkeypatch: pytest.MonkeyPatch, selected: str, transports: dict[str, Transport]
) -> None:
    """With the selected provider's transport missing, the call fails; nothing else is tried."""
    monkeypatch.setenv("LEARNOPS_ENV", "test")
    monkeypatch.setenv("MODEL_ALLOW_FAKE", "true")
    monkeypatch.setenv("MODEL_PROVIDER", selected)
    monkeypatch.setenv("MODEL_LOCAL_URL", URL)
    monkeypatch.setenv("MODEL_NAME", "m")
    monkeypatch.setenv("MODEL_HOSTED_API_KEY", SENTINEL_KEY)
    with pytest.raises(ProviderUnavailable, match="Q19"):
        create_provider(**transports)


def test_the_resolver_never_catches_a_selected_provider_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """get_provider() raises for hosted with no transport; it does not hand back anything else."""
    monkeypatch.setenv("LEARNOPS_ENV", "test")
    monkeypatch.setenv("MODEL_ALLOW_FAKE", "true")
    monkeypatch.setenv("MODEL_PROVIDER", "hosted")
    with pytest.raises(ProviderUnavailable, match="Q19"):
        get_provider()


# --- API key -------------------------------------------------------------------------------


def test_a_missing_key_names_the_variable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MODEL_PROVIDER", "hosted")
    monkeypatch.setenv("MODEL_NAME", "m")
    with pytest.raises(ConfigError, match="MODEL_HOSTED_API_KEY is not set"):
        create_provider(hosted_transport=Transport())


def test_the_key_appears_in_no_repr_error_or_log_record(
    registry: TaskRegistry, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("MODEL_PROVIDER", "hosted")
    monkeypatch.setenv("MODEL_NAME", "m")
    monkeypatch.setenv("MODEL_HOSTED_API_KEY", SENTINEL_KEY)
    transport = Transport(error=TransportError(f"bad key {SENTINEL_KEY}"))
    provider = create_provider(hosted_transport=transport)
    logger = InMemoryCallLogger()
    with pytest.raises(ProviderUnavailable) as caught:
        run(
            "example_echo",
            INPUTS,
            ECHO_OUTPUT,
            provider=provider,
            registry=registry,
            logger=logger,
        )
    shown = " ".join(
        [
            repr(provider),
            str(vars(provider)),
            str(caught.value),
            repr(caught.value),
            json.dumps([[r.task, r.outcome, r.meta] for r in logger.records]),
        ]
    )
    assert SENTINEL_KEY not in shown


def test_the_key_is_not_passed_to_the_transport(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The real transport reads it from the environment; the provider never handles it."""
    monkeypatch.setenv("MODEL_PROVIDER", "hosted")
    monkeypatch.setenv("MODEL_NAME", "m")
    monkeypatch.setenv("MODEL_HOSTED_API_KEY", SENTINEL_KEY)
    transport = Transport()
    create_provider(hosted_transport=transport).complete(request())
    assert SENTINEL_KEY not in str(transport.calls)


# --- fake provider stays test-only through the resolver -------------------------------------


@pytest.mark.parametrize("environment", ["lab", "production", None])
def test_the_resolver_refuses_the_fake_outside_a_test_run_even_with_the_flag(
    monkeypatch: pytest.MonkeyPatch, environment: str | None
) -> None:
    monkeypatch.setenv("MODEL_PROVIDER", "fake")
    monkeypatch.setenv("MODEL_ALLOW_FAKE", "true")
    if environment is not None:
        monkeypatch.setenv("LEARNOPS_ENV", environment)
    with pytest.raises(ConfigError, match="for automated tests only"):
        create_provider()
    with pytest.raises(ConfigError, match="for automated tests only"):
        FakeProvider()
