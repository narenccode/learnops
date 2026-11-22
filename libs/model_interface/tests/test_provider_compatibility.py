"""Local and hosted work through the same model.run(), proven with mock transports only.

No real server, SDK, endpoint or credential is used, so this proves the ARCHITECTURE and MOCK
COMPATIBILITY only. Real integration is pending the lab and design Q19. The numbers in the section
headings follow the FR-M-01 preparation checklist.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

import model_interface
from model_interface.call_log import InMemoryCallLogger
from model_interface.config import ConfigError
from model_interface.errors import InvalidMeta, InvalidOutput, ProviderUnavailable
from model_interface.providers import (
    FakeProvider,
    HostedProvider,
    LocalProvider,
    Provider,
    ProviderRequest,
    ProviderResponse,
    TransportError,
    TransportProvider,
    TransportReply,
    configure_provider,
    create_provider,
    ensure_provider,
    get_provider,
    reset_provider,
)
from model_interface.registry import TaskRegistry
from model_interface.runner import run

from .echo_task import ECHO_INPUT, ECHO_OUTPUT
from .mock_transport import MockTransport

B5_SCHEMA = (
    Path(__file__).resolve().parents[3] / "contracts" / "model-interface.v1.schema.json"
)
INPUTS = {"text": "a learner's private answer"}
URL = "http://ai.lab.invalid:11434"
OK_TEXT = '{"echo": "ok"}'
B5_META_FIELDS = {
    "provider",
    "model",
    "input_tokens",
    "output_tokens",
    "latency_ms",
    "cost_estimate",
    "prompt_version",
}
NAMES = ["local", "hosted"]


def provider_for(name: str, transport: MockTransport) -> Provider:
    if name == "local":
        return LocalProvider(url=URL, model="m", transport=transport)
    return HostedProvider(model="m", transport=transport)


def call(
    provider: Provider, registry: TaskRegistry, logger: InMemoryCallLogger
) -> model_interface.Result:
    return run(
        "example_echo",
        INPUTS,
        ECHO_OUTPUT,
        provider=provider,
        registry=registry,
        logger=logger,
    )


@pytest.fixture
def real_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    """Placeholder settings, the ones in .env.example, on a test run with the fake allowed."""
    monkeypatch.setenv("LEARNOPS_ENV", "test")
    monkeypatch.setenv("MODEL_ALLOW_FAKE", "true")
    monkeypatch.setenv("MODEL_LOCAL_URL", URL)
    monkeypatch.setenv("MODEL_NAME", "m")


# --- 1, 2. provider selection --------------------------------------------------------------


@pytest.mark.parametrize(
    ("name", "kind"), [("local", LocalProvider), ("hosted", HostedProvider)], ids=NAMES
)
def test_model_provider_selects_the_provider(
    real_settings: None,
    monkeypatch: pytest.MonkeyPatch,
    name: str,
    kind: type[TransportProvider],
) -> None:
    monkeypatch.setenv("MODEL_PROVIDER", name)
    provider = create_provider(
        local_transport=MockTransport(), hosted_transport=MockTransport()
    )
    assert isinstance(provider, kind)
    assert isinstance(provider, TransportProvider)
    assert isinstance(provider, Provider)


def test_fake_is_selected_in_a_test_run(
    real_settings: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("MODEL_PROVIDER", "fake")
    assert isinstance(create_provider(), FakeProvider)


# --- 8. structured-output validation -------------------------------------------------------


@pytest.mark.parametrize("name", NAMES)
def test_output_that_breaks_the_schema_is_rejected(
    registry: TaskRegistry, name: str
) -> None:
    transport = MockTransport(TransportReply('{"echo": 5}'))
    with pytest.raises(InvalidOutput, match="on both attempts"):
        call(provider_for(name, transport), registry, InMemoryCallLogger())


# --- 9. invalid provider output ------------------------------------------------------------


@pytest.mark.parametrize("name", NAMES)
@pytest.mark.parametrize(
    "text",
    ["not json", "", "[]", '{"wrong": 1}', None, 5, b"\xff"],
    ids=["text", "empty", "list", "wrong-shape", "none", "number", "bytes"],
)
def test_invalid_output_gets_one_retry_then_a_clear_error(
    registry: TaskRegistry, name: str, text: Any
) -> None:
    transport = MockTransport(TransportReply(text))
    logger = InMemoryCallLogger()
    with pytest.raises(InvalidOutput):
        call(provider_for(name, transport), registry, logger)
    assert len(transport.calls) == 2
    assert [r.outcome for r in logger.records] == ["invalid_output"] * 2


@pytest.fixture
def any_object_registry(test_run: None, tmp_path: Path) -> TaskRegistry:
    """A task whose output schema accepts any object, so only the JSON parser can refuse."""
    folder = tmp_path / "any_object"
    folder.mkdir()
    (folder / "v1.md").write_text(
        "---\nprompt_version: any_object/v1\n---\nAnswer.\n", encoding="utf-8"
    )
    reg = TaskRegistry()
    reg.register("any_object", ECHO_INPUT, {"type": "object"}, prompt_dir=folder)
    return reg


@pytest.mark.parametrize("name", NAMES)
@pytest.mark.parametrize("text", [b"{}", bytearray(b"{}")], ids=["bytes", "bytearray"])
def test_bytes_are_refused_even_when_they_hold_valid_json(
    any_object_registry: TaskRegistry, name: str, text: Any
) -> None:
    """json.loads would accept these, but the provider contract says text is a str."""
    transport = MockTransport(TransportReply(text))
    logger = InMemoryCallLogger()
    with pytest.raises(InvalidOutput, match="output is not text"):
        run(
            "any_object",
            INPUTS,
            {"type": "object"},
            provider=provider_for(name, transport),
            registry=any_object_registry,
            logger=logger,
        )
    assert [r.outcome for r in logger.records] == ["invalid_output"] * 2


@pytest.mark.parametrize("name", NAMES)
@pytest.mark.parametrize("value", ["NaN", "Infinity", "-Infinity"])
def test_nan_and_infinity_are_not_json(
    any_object_registry: TaskRegistry, name: str, value: str
) -> None:
    transport = MockTransport(TransportReply('{"a": ' + value + "}"))
    with pytest.raises(InvalidOutput, match="output is not JSON"):
        run(
            "any_object",
            INPUTS,
            {"type": "object"},
            provider=provider_for(name, transport),
            registry=any_object_registry,
            logger=InMemoryCallLogger(),
        )


# --- 10. provider failure ------------------------------------------------------------------


@pytest.mark.parametrize("name", NAMES)
@pytest.mark.parametrize(
    "error",
    [TransportError("secret"), TimeoutError("secret"), ValueError("secret")],
    ids=lambda e: type(e).__name__,
)
def test_provider_failure_is_one_clear_error_logged_and_not_retried(
    registry: TaskRegistry, name: str, error: Exception
) -> None:
    transport = MockTransport(error=error)
    logger = InMemoryCallLogger()
    with pytest.raises(ProviderUnavailable) as caught:
        call(provider_for(name, transport), registry, logger)
    assert "secret" not in str(caught.value)
    assert len(transport.calls) == 1
    (record,) = logger.records
    assert record.outcome == "provider_error"
    assert record.meta["provider"] == name


@pytest.mark.parametrize("name", NAMES)
@pytest.mark.parametrize("reply", ["not a reply", 7, {"text": "x"}], ids=str)
def test_a_malformed_transport_reply_is_a_clear_logged_error(
    registry: TaskRegistry, name: str, reply: Any
) -> None:
    logger = InMemoryCallLogger()
    with pytest.raises(ProviderUnavailable):
        call(provider_for(name, MockTransport(reply)), registry, logger)
    assert [r.outcome for r in logger.records] == ["provider_error"]


def test_a_provider_that_returns_the_wrong_type_is_logged(
    registry: TaskRegistry,
) -> None:
    class Wrong:
        name = "local"
        model = "m"

        def complete(self, request: ProviderRequest) -> ProviderResponse:
            return "not a response"  # type: ignore[return-value]

    logger = InMemoryCallLogger()
    with pytest.raises(ProviderUnavailable, match="not a provider response"):
        run(
            "example_echo",
            INPUTS,
            ECHO_OUTPUT,
            provider=Wrong(),  # type: ignore[arg-type]
            registry=registry,
            logger=logger,
        )
    assert [r.outcome for r in logger.records] == ["provider_error"]


# --- 11. metadata consistency --------------------------------------------------------------


@pytest.mark.parametrize("name", [*NAMES, "fake"])
def test_meta_has_exactly_the_b5_fields_for_every_provider(
    registry: TaskRegistry, fake_env: None, name: str
) -> None:
    provider: Provider
    if name == "fake":
        fake = FakeProvider()
        fake.add_response("example_echo", INPUTS, {"echo": "ok"})
        provider = fake
    else:
        provider = provider_for(name, MockTransport())
    result = call(provider, registry, InMemoryCallLogger())
    assert set(result.meta) == B5_META_FIELDS
    validator = Draft202012Validator(json.loads(B5_SCHEMA.read_text(encoding="utf-8")))
    assert list(validator.iter_errors(result.meta)) == []
    assert result.meta["provider"] == name
    assert result.meta["prompt_version"] == "example_echo/v1"


@pytest.mark.parametrize("name", NAMES)
def test_failed_attempts_have_the_same_b5_fields(
    registry: TaskRegistry, name: str
) -> None:
    logger = InMemoryCallLogger()
    with pytest.raises(ProviderUnavailable):
        call(
            provider_for(name, MockTransport(error=TransportError())), registry, logger
        )
    assert set(logger.records[0].meta) == B5_META_FIELDS


# --- 12. logging behaviour -----------------------------------------------------------------


@pytest.mark.parametrize("name", NAMES)
def test_every_outcome_reaches_the_shared_logger(
    registry: TaskRegistry, name: str
) -> None:
    logger = InMemoryCallLogger()
    call(provider_for(name, MockTransport()), registry, logger)
    with pytest.raises(InvalidOutput):
        call(provider_for(name, MockTransport(TransportReply("x"))), registry, logger)
    with pytest.raises(ProviderUnavailable):
        call(
            provider_for(name, MockTransport(error=TransportError())), registry, logger
        )
    with pytest.raises(InvalidMeta):
        bad_usage = TransportReply(OK_TEXT, input_tokens=-1)
        call(provider_for(name, MockTransport(bad_usage)), registry, logger)
    assert [r.outcome for r in logger.records] == [
        "ok",
        "invalid_output",
        "invalid_output",
        "provider_error",
        "invalid_meta",
    ]


@pytest.mark.parametrize("name", NAMES)
def test_no_attempt_logs_inputs_prompt_or_output(
    registry: TaskRegistry, name: str
) -> None:
    logger = InMemoryCallLogger()
    reply = TransportReply('{"echo": "private model text"}')
    call(provider_for(name, MockTransport(reply)), registry, logger)
    logged = repr(logger.records)
    assert "private answer" not in logged
    assert "private model text" not in logged
    assert "TEST-ONLY" not in logged  # the prompt


# --- 13. switching provider by configuration only ------------------------------------------


def application_code(registry: TaskRegistry) -> dict[str, Any]:
    """Stands for a module: it names no provider and passes none."""
    return run("example_echo", INPUTS, ECHO_OUTPUT, registry=registry).meta


def test_switching_local_to_hosted_needs_no_application_change(
    registry: TaskRegistry, real_settings: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    local_transport = MockTransport()
    hosted_transport = MockTransport()

    def service_start() -> None:
        configure_provider(
            create_provider(
                local_transport=local_transport, hosted_transport=hosted_transport
            )
        )

    monkeypatch.setenv("MODEL_PROVIDER", "local")
    service_start()
    assert application_code(registry)["provider"] == "local"

    reset_provider()  # a restart
    monkeypatch.setenv("MODEL_PROVIDER", "hosted")
    service_start()
    assert application_code(registry)["provider"] == "hosted"

    assert len(local_transport.calls) == 1
    assert len(hosted_transport.calls) == 1


# --- 14. no automatic fallback and no silent switch ----------------------------------------


@pytest.mark.parametrize("name", NAMES)
def test_a_configured_provider_never_becomes_the_fake(
    registry: TaskRegistry,
    real_settings: None,
    monkeypatch: pytest.MonkeyPatch,
    name: str,
) -> None:
    monkeypatch.setenv("MODEL_PROVIDER", name)
    transport = MockTransport()
    configure_provider(
        create_provider(local_transport=transport, hosted_transport=transport)
    )
    monkeypatch.setenv("MODEL_PROVIDER", "fake")
    with pytest.raises(ConfigError, match="never switches provider"):
        get_provider()
    with pytest.raises(ConfigError, match="never switches provider"):
        application_code(registry)
    assert transport.calls == []


def test_a_failing_hosted_provider_never_tries_local_or_fake(
    registry: TaskRegistry, real_settings: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("MODEL_PROVIDER", "hosted")
    local_transport = MockTransport()
    hosted_transport = MockTransport(error=TransportError("down"))
    configure_provider(
        create_provider(
            local_transport=local_transport, hosted_transport=hosted_transport
        )
    )
    with pytest.raises(ProviderUnavailable):
        application_code(registry)
    assert len(hosted_transport.calls) == 1
    assert local_transport.calls == []


# --- provider validation -------------------------------------------------------------------


class Complete:
    """A well-formed provider; tests below break it one attribute at a time."""

    name: Any = "local"
    model: Any = "m"

    def complete(self, request: ProviderRequest) -> ProviderResponse:
        return ProviderResponse(OK_TEXT, None, None, None)


class NoComplete:
    name = "local"
    model = "m"


class CompleteNotCallable(Complete):
    complete = 5  # type: ignore[assignment]


class UnknownName(Complete):
    name = "openai"


class NoModel(Complete):
    model = "  "


class ModelNotText(Complete):
    model = 5


class NameIsCallable(Complete):
    name = staticmethod(lambda: "local")


@pytest.mark.parametrize(
    ("kind", "reason"),
    [
        (object, "needs name, model and complete"),
        (NoComplete, "needs name, model and complete"),
        (CompleteNotCallable, "complete is not callable"),
        (UnknownName, "its name must be one of local, hosted, fake"),
        (NameIsCallable, "its name must be one of"),
        (NoModel, "its model is empty"),
        (ModelNotText, "its model is empty"),
    ],
    ids=lambda v: v.__name__ if isinstance(v, type) else None,
)
def test_invalid_providers_are_refused(
    registry: TaskRegistry,
    real_settings: None,
    monkeypatch: pytest.MonkeyPatch,
    kind: type,
    reason: str,
) -> None:
    monkeypatch.setenv("MODEL_PROVIDER", "local")
    with pytest.raises(ConfigError, match=reason):
        ensure_provider(kind())
    with pytest.raises(ConfigError, match=reason):
        configure_provider(kind())
    with pytest.raises(ConfigError, match=reason):
        run(
            "example_echo",
            INPUTS,
            ECHO_OUTPUT,
            provider=kind(),
            registry=registry,
            logger=InMemoryCallLogger(),
        )


def test_a_valid_provider_passes(real_settings: None) -> None:
    provider = Complete()
    assert ensure_provider(provider) is provider


@pytest.mark.parametrize("environment", ["lab", "production", None])
def test_a_look_alike_calling_itself_fake_is_refused_outside_a_test_run(
    monkeypatch: pytest.MonkeyPatch, environment: str | None
) -> None:
    """A name is not enough: this object never went through FakeProvider's guard."""

    class LookAlike(Complete):
        name = "fake"

    if environment is not None:
        monkeypatch.setenv("LEARNOPS_ENV", environment)
    with pytest.raises(ConfigError, match="automated test runs only"):
        ensure_provider(LookAlike())


# --- provider configuration ----------------------------------------------------------------


def test_a_provider_that_disagrees_with_the_setting_is_refused(
    real_settings: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("MODEL_PROVIDER", "local")
    hosted = HostedProvider(model="m", transport=MockTransport())
    with pytest.raises(ConfigError, match="'hosted' but MODEL_PROVIDER is 'local'"):
        configure_provider(hosted)
    with pytest.raises(ProviderUnavailable, match="Q19"):
        get_provider()  # nothing was left configured, so it tries to build local and cannot


def test_a_second_provider_is_refused_and_the_first_stays(
    real_settings: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("MODEL_PROVIDER", "local")
    first = create_provider(local_transport=MockTransport())
    second = create_provider(local_transport=MockTransport())
    configure_provider(first)
    with pytest.raises(ConfigError, match="never replaced silently"):
        configure_provider(second)
    assert get_provider() is first


def test_setting_the_same_provider_again_is_harmless(
    real_settings: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("MODEL_PROVIDER", "local")
    provider = create_provider(local_transport=MockTransport())
    configure_provider(provider)
    configure_provider(provider)
    assert get_provider() is provider


def test_a_shared_fake_cannot_be_replaced_either(fake_env: None) -> None:
    get_provider()
    with pytest.raises(ConfigError, match="never replaced silently"):
        configure_provider(FakeProvider())


def test_reset_clears_state_so_tests_stay_independent(
    real_settings: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("MODEL_PROVIDER", "local")
    configure_provider(create_provider(local_transport=MockTransport()))
    reset_provider()
    replacement = create_provider(local_transport=MockTransport())
    configure_provider(replacement)
    assert get_provider() is replacement


def test_state_from_another_test_does_not_leak(
    real_settings: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Whatever ran before, the shared provider starts empty (the autouse fixture resets it)."""
    monkeypatch.setenv("MODEL_PROVIDER", "hosted")
    with pytest.raises(ProviderUnavailable, match="Q19"):
        get_provider()


def test_reset_is_not_part_of_the_public_api() -> None:
    assert "reset_provider" not in model_interface.__all__
    assert not hasattr(model_interface, "reset_provider")


# --- credentials: real handling is pending Q19 ---------------------------------------------


def test_a_mock_hosted_provider_needs_no_credential(
    registry: TaskRegistry, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("MODEL_PROVIDER", "hosted")
    monkeypatch.setenv("MODEL_NAME", "m")
    monkeypatch.delenv("MODEL_HOSTED_API_KEY", raising=False)
    provider = create_provider(hosted_transport=MockTransport())
    assert call(provider, registry, InMemoryCallLogger()).data == {"echo": "ok"}


def test_no_hosted_provider_exists_without_a_transport(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Setting a key does not make a real hosted provider appear: that needs a transport (Q19)."""
    monkeypatch.setenv("MODEL_PROVIDER", "hosted")
    monkeypatch.setenv("MODEL_NAME", "m")
    monkeypatch.setenv("MODEL_HOSTED_API_KEY", "placeholder")
    with pytest.raises(ProviderUnavailable, match="Q19"):
        create_provider()
