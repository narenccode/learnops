"""Shared fixtures. The fake provider reads only the real process environment, so tests set it
with monkeypatch instead of passing a mapping."""

from __future__ import annotations

from collections.abc import Iterator

import pytest

from model_interface.call_log import reset_call_logger
from model_interface.providers import reset_provider
from model_interface.registry import TaskRegistry

from .echo_task import ECHO_INPUT, ECHO_OUTPUT

SETTINGS = (
    "LEARNOPS_ENV",
    "MODEL_ALLOW_FAKE",
    "MODEL_PROVIDER",
    "MODEL_NAME",
    "MODEL_LOCAL_URL",
    "MODEL_HOSTED_API_KEY",
)


@pytest.fixture(autouse=True)
def clean_env(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Start every test with no provider settings, shared provider or configured logger."""
    for name in SETTINGS:
        monkeypatch.delenv(name, raising=False)
    reset_provider()
    reset_call_logger()
    yield
    reset_provider()
    reset_call_logger()


@pytest.fixture
def fake_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LEARNOPS_ENV", "test")
    monkeypatch.setenv("MODEL_ALLOW_FAKE", "true")
    monkeypatch.setenv("MODEL_PROVIDER", "fake")


@pytest.fixture
def test_run(monkeypatch: pytest.MonkeyPatch) -> None:
    """Declares a test run, where injecting a provider or logger into run() is allowed."""
    monkeypatch.setenv("LEARNOPS_ENV", "test")


@pytest.fixture
def registry(test_run: None) -> TaskRegistry:
    """A private registry with the test-only example_echo task (never the shared one).

    Using it declares a test run. A test of a service sets LEARNOPS_ENV itself afterwards.
    """
    reg = TaskRegistry()
    reg.register("example_echo", ECHO_INPUT, ECHO_OUTPUT)
    return reg
