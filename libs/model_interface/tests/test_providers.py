"""Providers (PRD B5.2): the fake provider's guard and behaviour, and the local provider's transport.

The fake provider can only be built when the real process environment passes config.py's rule
(decision record 0001 #3); no argument or mapping can switch that off.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pytest

from model_interface.config import ConfigError
from model_interface.errors import ProviderUnavailable
from model_interface.providers import (
    FakeProvider,
    LocalProvider,
    ProviderRequest,
    TransportError,
    TransportReply,
    create_provider,
)

from .echo_task import ECHO_OUTPUT


def request(inputs: Mapping[str, Any], task: str = "example_echo") -> ProviderRequest:
    return ProviderRequest(
        task=task,
        prompt="p",
        prompt_version=f"{task}/v1",
        inputs=inputs,
        output_schema=ECHO_OUTPUT,
    )


class RecordingTransport:
    def __init__(
        self, reply: TransportReply | None = None, error: Exception | None = None
    ) -> None:
        self.reply = reply or TransportReply(
            text='{"echo": "hi"}', input_tokens=12, output_tokens=3
        )
        self.error = error
        self.calls: list[dict[str, Any]] = []

    def complete(self, **kwargs: Any) -> TransportReply:
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return self.reply


# --- fake provider guard -------------------------------------------------------------------


def test_fake_is_built_only_in_a_test_run(fake_env: None) -> None:
    assert isinstance(create_provider(), FakeProvider)
    assert isinstance(FakeProvider(), FakeProvider)


@pytest.mark.parametrize(
    "env",
    [
        {"MODEL_PROVIDER": "fake"},
        {"MODEL_PROVIDER": "fake", "LEARNOPS_ENV": "test"},
        {"MODEL_PROVIDER": "fake", "LEARNOPS_ENV": "lab", "MODEL_ALLOW_FAKE": "true"},
        {
            "MODEL_PROVIDER": "fake",
            "LEARNOPS_ENV": "production",
            "MODEL_ALLOW_FAKE": "true",
        },
        {"MODEL_PROVIDER": "fake", "MODEL_ALLOW_FAKE": "true"},
    ],
    ids=repr,
)
def test_fake_cannot_be_built_outside_a_test_run(
    monkeypatch: pytest.MonkeyPatch, env: dict[str, str]
) -> None:
    for name, value in env.items():
        monkeypatch.setenv(name, value)
    with pytest.raises(ConfigError):
        create_provider()
    with pytest.raises(ConfigError):
        FakeProvider()  # building it directly goes through the same guard


def test_fake_needs_model_provider_fake_even_in_a_test_run(
    fake_env: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("MODEL_PROVIDER", "local")
    with pytest.raises(ConfigError, match="MODEL_PROVIDER is 'local'"):
        FakeProvider()


def test_fake_takes_no_environment_argument() -> None:
    """A caller cannot hand the fake provider a made-up environment to get past the guard."""
    with pytest.raises(TypeError):
        FakeProvider({"LEARNOPS_ENV": "test", "MODEL_ALLOW_FAKE": "true"})  # type: ignore[call-arg]


# --- fake provider behaviour ---------------------------------------------------------------


def test_fake_answers_by_task_and_inputs_whatever_the_key_order(fake_env: None) -> None:
    fake = FakeProvider()
    fake.add_response("example_echo", {"a": 1, "b": 2}, {"echo": "x"})
    reply = fake.complete(request({"b": 2, "a": 1}))
    assert reply.text == '{"echo": "x"}'
    assert (reply.input_tokens, reply.output_tokens, reply.cost_estimate) == (0, 0, 0.0)


def test_fake_without_a_fixture_says_so(fake_env: None) -> None:
    fake = FakeProvider()
    fake.add_response("example_echo", {"text": "a"}, {"echo": "a"})
    with pytest.raises(ProviderUnavailable, match="no response"):
        fake.complete(request({"text": "other"}))
    with pytest.raises(ProviderUnavailable, match="no response"):
        fake.complete(request({"text": "a"}, task="other_task"))


def test_fake_plays_queued_outputs_in_order_then_repeats_the_last(
    fake_env: None,
) -> None:
    fake = FakeProvider()
    fake.add_response("example_echo", {"text": "a"}, "not json", {"echo": "a"})
    texts = [fake.complete(request({"text": "a"})).text for _ in range(3)]
    assert texts == ["not json", '{"echo": "a"}', '{"echo": "a"}']


def test_fake_failure_injection_raises_once(fake_env: None) -> None:
    fake = FakeProvider()
    fake.add_response("example_echo", {"text": "a"}, {"echo": "a"})
    fake.fail_next(ProviderUnavailable("down"))
    with pytest.raises(ProviderUnavailable, match="down"):
        fake.complete(request({"text": "a"}))
    assert fake.complete(request({"text": "a"})).text == '{"echo": "a"}'


# --- provider selection --------------------------------------------------------------------


def test_hosted_is_not_implemented_yet(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MODEL_PROVIDER", "hosted")
    with pytest.raises(ProviderUnavailable, match="Q19"):
        create_provider()


def test_local_without_a_transport_is_not_integrated_yet(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MODEL_PROVIDER", "local")
    with pytest.raises(ProviderUnavailable, match="Q19"):
        create_provider()


@pytest.mark.parametrize("missing", ["MODEL_LOCAL_URL", "MODEL_NAME"])
def test_local_needs_its_settings(
    monkeypatch: pytest.MonkeyPatch, missing: str
) -> None:
    monkeypatch.setenv("MODEL_PROVIDER", "local")
    monkeypatch.setenv("MODEL_LOCAL_URL", "http://ai.lab.invalid:11434")
    monkeypatch.setenv("MODEL_NAME", "example-local-model")
    monkeypatch.delenv(missing)
    with pytest.raises(ConfigError, match=f"{missing} is not set"):
        create_provider(local_transport=RecordingTransport())


# --- local provider ------------------------------------------------------------------------


def local(transport: RecordingTransport) -> LocalProvider:
    return LocalProvider(
        url="http://ai.lab.invalid:11434", model="m", transport=transport, timeout_s=5
    )


def test_local_passes_the_request_to_its_transport() -> None:
    transport = RecordingTransport()
    reply = local(transport).complete(request({"text": "hi"}))
    assert transport.calls == [
        {
            "url": "http://ai.lab.invalid:11434",
            "model": "m",
            "prompt": "p",
            "inputs": {"text": "hi"},
            "output_schema": ECHO_OUTPUT,
            "timeout_s": 5,
        }
    ]
    assert (reply.text, reply.input_tokens, reply.output_tokens) == (
        '{"echo": "hi"}',
        12,
        3,
    )
    assert reply.cost_estimate == 0.0  # local: no billed cost (decision record 0001 #2)


def test_local_keeps_unreported_usage_as_none() -> None:
    reply = local(RecordingTransport(TransportReply(text="{}"))).complete(
        request({"text": "x"})
    )
    assert (reply.input_tokens, reply.output_tokens) == (None, None)


@pytest.mark.parametrize(
    "error",
    [
        TransportError("secret learner text in the request"),
        # A transport bug or a library error that is not a TransportError is wrapped the same way.
        RuntimeError("secret learner text at http://ai.lab.invalid:11434/?token=abc"),
        TimeoutError("secret learner text"),
    ],
    ids=lambda e: type(e).__name__,
)
def test_transport_failure_becomes_provider_unavailable_without_content(
    error: Exception,
) -> None:
    with pytest.raises(ProviderUnavailable) as caught:
        local(RecordingTransport(error=error)).complete(request({"text": "x"}))
    shown = f"{caught.value!s} {caught.value!r}"
    assert "secret learner text" not in shown
    assert "token=abc" not in shown
    assert type(error).__name__ in shown
    # The original exception is not chained, so a printed traceback cannot show its message.
    assert caught.value.__cause__ is None
    assert caught.value.__suppress_context__ is True
