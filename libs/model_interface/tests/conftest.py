"""Shared fixtures. The fake provider reads only the real process environment, so tests set it
with monkeypatch instead of passing a mapping."""

from __future__ import annotations

import pytest

from model_interface.registry import TaskRegistry

from .echo_task import ECHO_INPUT, ECHO_OUTPUT

SETTINGS = (
    "LEARNOPS_ENV",
    "MODEL_ALLOW_FAKE",
    "MODEL_PROVIDER",
    "MODEL_NAME",
    "MODEL_LOCAL_URL",
)


@pytest.fixture(autouse=True)
def clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Start every test with no provider settings, whatever the developer's shell has."""
    for name in SETTINGS:
        monkeypatch.delenv(name, raising=False)


@pytest.fixture
def fake_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LEARNOPS_ENV", "test")
    monkeypatch.setenv("MODEL_ALLOW_FAKE", "true")
    monkeypatch.setenv("MODEL_PROVIDER", "fake")


@pytest.fixture
def registry() -> TaskRegistry:
    """A private registry with the test-only example_echo task (never the shared one)."""
    reg = TaskRegistry()
    reg.register("example_echo", ECHO_INPUT, ECHO_OUTPUT)
    return reg
