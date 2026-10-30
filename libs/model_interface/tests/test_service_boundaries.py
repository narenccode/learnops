"""What a service can and cannot do through run() (PRD B5.2, B5.3).

Outside LEARNOPS_ENV=test, also with it unset, a call runs only on the configured provider and logs
only to the configured logger. Passing anything else is refused before any model call, so a service
cannot silently send data to another provider or miss the shared log. Injection stays open in test
runs. Mock transports only; no logger here is a real shared.model_calls logger (design Q36).
"""

from __future__ import annotations

from typing import Any

import pytest

from model_interface.call_log import (
    CallRecord,
    InMemoryCallLogger,
    configure_call_logger,
    get_call_logger,
)
from model_interface.config import ConfigError
from model_interface.errors import CallLoggerMissing, ProviderUnavailable
from model_interface.providers import (
    FakeProvider,
    HostedProvider,
    LocalProvider,
    Provider,
    ProviderRequest,
    ProviderResponse,
    TransportError,
    TransportReply,
    configure_provider,
    resolve_provider,
)
from model_interface.registry import TaskRegistry
from model_interface.runner import run

from .echo_task import ECHO_OUTPUT
from .mock_transport import MockTransport

INPUTS = {"text": "a learner's private answer"}
URL = "http://ai.lab.invalid:11434"
SERVICE_ENVIRONMENTS = ["lab", "production", None]


class SharedLogger:
    """Stands for the configured service logger. Not InMemoryCallLogger, which services can't use."""

    def __init__(self) -> None:
        self.records: list[CallRecord] = []

    def record(self, record: CallRecord) -> None:
        self.records.append(record)


def build(name: str, transport: MockTransport) -> Provider:
    if name == "local":
        return LocalProvider(url=URL, model="m", transport=transport)
    return HostedProvider(model="m", transport=transport)


def become_service(
    monkeypatch: pytest.MonkeyPatch,
    environment: str | None,
    selected: str,
    transport: MockTransport,
) -> SharedLogger:
    """Set a service up the documented way and return its shared logger."""
    if environment is None:
        monkeypatch.delenv("LEARNOPS_ENV", raising=False)
    else:
        monkeypatch.setenv("LEARNOPS_ENV", environment)
    monkeypatch.setenv("MODEL_PROVIDER", selected)
    configure_provider(build(selected, transport))
    logger = SharedLogger()
    configure_call_logger(logger)
    return logger


def service_call(registry: TaskRegistry, **overrides: Any) -> Any:
    return run("example_echo", INPUTS, ECHO_OUTPUT, registry=registry, **overrides)


# --- provider selection --------------------------------------------------------------------


@pytest.mark.parametrize("environment", SERVICE_ENVIRONMENTS)
@pytest.mark.parametrize(
    ("selected", "other"),
    [("local", "hosted"), ("hosted", "local")],
    ids=["local-service", "hosted-service"],
)
def test_a_service_cannot_silently_run_on_the_other_provider(
    registry: TaskRegistry,
    monkeypatch: pytest.MonkeyPatch,
    environment: str | None,
    selected: str,
    other: str,
) -> None:
    configured = MockTransport()
    logger = become_service(monkeypatch, environment, selected, configured)
    other_transport = MockTransport()
    with pytest.raises(ConfigError, match="never switches provider"):
        service_call(registry, provider=build(other, other_transport))
    assert other_transport.calls == []  # the learner's data never left
    assert configured.calls == []
    assert logger.records == []  # no attempt happened, so there is nothing to log


@pytest.mark.parametrize("environment", SERVICE_ENVIRONMENTS)
@pytest.mark.parametrize("selected", ["local", "hosted"])
def test_a_service_cannot_swap_in_another_provider_of_the_same_kind(
    registry: TaskRegistry,
    monkeypatch: pytest.MonkeyPatch,
    environment: str | None,
    selected: str,
) -> None:
    """The same name is not enough: this one could point at another endpoint."""
    become_service(monkeypatch, environment, selected, MockTransport())
    other_transport = MockTransport()
    with pytest.raises(ConfigError, match="not the configured one"):
        service_call(registry, provider=build(selected, other_transport))
    assert other_transport.calls == []


def test_a_service_with_no_configured_provider_cannot_pass_one(
    registry: TaskRegistry, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("LEARNOPS_ENV", "production")
    monkeypatch.setenv("MODEL_PROVIDER", "local")
    transport = MockTransport()
    with pytest.raises(ConfigError, match="not the configured one"):
        service_call(registry, provider=build("local", transport))
    assert transport.calls == []


def test_passing_the_configured_provider_is_harmless(
    registry: TaskRegistry, monkeypatch: pytest.MonkeyPatch
) -> None:
    transport = MockTransport()
    become_service(monkeypatch, "production", "local", transport)
    configured = resolve_provider(None)
    service_call(registry, provider=configured)
    assert len(transport.calls) == 1


def test_a_service_runs_on_its_configured_provider(
    registry: TaskRegistry, monkeypatch: pytest.MonkeyPatch
) -> None:
    transport = MockTransport()
    become_service(monkeypatch, "production", "hosted", transport)
    assert service_call(registry).meta["provider"] == "hosted"
    assert len(transport.calls) == 1


@pytest.mark.parametrize("environment", SERVICE_ENVIRONMENTS)
def test_the_fake_stays_refused_for_a_service(
    registry: TaskRegistry, monkeypatch: pytest.MonkeyPatch, environment: str | None
) -> None:
    class LookAlike:
        name = "fake"
        model = "m"

        def complete(self, request: ProviderRequest) -> ProviderResponse:
            raise AssertionError("must never be called")

    become_service(monkeypatch, environment, "local", MockTransport())
    with pytest.raises(ConfigError, match="automated test runs only"):
        service_call(registry, provider=LookAlike())
    monkeypatch.setenv("MODEL_PROVIDER", "fake")
    with pytest.raises(ConfigError, match="fake provider is turned off"):
        FakeProvider()


def test_a_test_run_can_still_inject_any_provider_and_logger(
    registry: TaskRegistry, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Whatever MODEL_PROVIDER says, and with nothing configured."""
    monkeypatch.setenv("MODEL_PROVIDER", "local")
    transport = MockTransport()
    logger = InMemoryCallLogger()
    result = service_call(registry, provider=build("hosted", transport), logger=logger)
    assert result.meta["provider"] == "hosted"
    assert len(transport.calls) == 1
    assert len(logger.records) == 1


def test_a_test_run_can_still_inject_the_fake(
    fake_env: None, registry: TaskRegistry
) -> None:
    fake = FakeProvider()
    fake.add_response("example_echo", INPUTS, {"echo": "ok"})
    assert service_call(registry, provider=fake).data == {"echo": "ok"}


# --- shared logging ------------------------------------------------------------------------


@pytest.mark.parametrize("environment", SERVICE_ENVIRONMENTS)
@pytest.mark.parametrize("selected", ["local", "hosted"])
def test_every_service_call_reaches_the_configured_logger(
    registry: TaskRegistry,
    monkeypatch: pytest.MonkeyPatch,
    environment: str | None,
    selected: str,
) -> None:
    logger = become_service(monkeypatch, environment, selected, MockTransport())
    service_call(registry)
    service_call(registry)
    assert [r.outcome for r in logger.records] == ["ok", "ok"]
    assert {r.meta["provider"] for r in logger.records} == {selected}


@pytest.mark.parametrize("selected", ["local", "hosted"])
def test_a_failed_service_call_reaches_the_configured_logger(
    registry: TaskRegistry, monkeypatch: pytest.MonkeyPatch, selected: str
) -> None:
    transport = MockTransport(error=TransportError("down"))
    logger = become_service(monkeypatch, "production", selected, transport)
    with pytest.raises(ProviderUnavailable):
        service_call(registry)
    assert [r.outcome for r in logger.records] == ["provider_error"]


def test_invalid_output_in_a_service_reaches_the_configured_logger(
    registry: TaskRegistry, monkeypatch: pytest.MonkeyPatch
) -> None:
    transport = MockTransport(TransportReply("not json"))
    logger = become_service(monkeypatch, "production", "local", transport)
    with pytest.raises(Exception, match="on both attempts"):
        service_call(registry)
    assert [r.outcome for r in logger.records] == ["invalid_output"] * 2


@pytest.mark.parametrize("environment", SERVICE_ENVIRONMENTS)
def test_a_service_cannot_bypass_the_shared_logger(
    registry: TaskRegistry, monkeypatch: pytest.MonkeyPatch, environment: str | None
) -> None:
    transport = MockTransport()
    shared = become_service(monkeypatch, environment, "local", transport)
    throwaway = SharedLogger()
    with pytest.raises(ConfigError, match="would miss the shared log"):
        service_call(registry, logger=throwaway)
    assert transport.calls == []  # refused before any model call
    assert throwaway.records == [] and shared.records == []


def test_a_service_can_pass_the_configured_logger(
    registry: TaskRegistry, monkeypatch: pytest.MonkeyPatch
) -> None:
    shared = become_service(monkeypatch, "lab", "local", MockTransport())
    service_call(registry, logger=shared)
    assert len(shared.records) == 1


def test_a_service_with_no_logger_cannot_pass_one(
    registry: TaskRegistry, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("LEARNOPS_ENV", "lab")
    monkeypatch.setenv("MODEL_PROVIDER", "local")
    transport = MockTransport()
    configure_provider(build("local", transport))
    with pytest.raises(CallLoggerMissing):
        service_call(registry, logger=SharedLogger())
    assert transport.calls == []


# --- InMemoryCallLogger is for test runs ---------------------------------------------------


@pytest.mark.parametrize("environment", SERVICE_ENVIRONMENTS)
def test_the_in_memory_logger_cannot_be_configured_outside_a_test_run(
    monkeypatch: pytest.MonkeyPatch, environment: str | None
) -> None:
    class Subclass(InMemoryCallLogger):
        pass

    if environment is not None:
        monkeypatch.setenv("LEARNOPS_ENV", environment)
    for logger in (InMemoryCallLogger(), Subclass()):
        with pytest.raises(ConfigError, match="for test runs only"):
            configure_call_logger(logger)
    with pytest.raises(CallLoggerMissing):
        get_call_logger()  # the refused logger was not left in place


def test_the_in_memory_logger_can_be_configured_in_a_test_run(test_run: None) -> None:
    logger = InMemoryCallLogger()
    configure_call_logger(logger)
    assert get_call_logger() is logger


def test_a_service_can_configure_its_own_logger(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LEARNOPS_ENV", "production")
    logger = SharedLogger()
    configure_call_logger(logger)
    assert get_call_logger() is logger
