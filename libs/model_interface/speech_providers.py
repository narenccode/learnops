"""Speech providers behind one interface (PRD B5.4: same rules as B5.2).

create_speech_provider() builds the provider named by SPEECH_PROVIDER, through the same
fake-provider rule as the model providers (config.provider_from_env, decision record 0001 #3).
There is no fallback: the selected provider is used or the call fails.

The local (lab Whisper-family) and hosted speech services are not integrated yet (design Q19), so
both refuse with a clear error and send nothing. The fake provider is for automated tests: it calls
no model and is built from the B5 contract example.
"""

from __future__ import annotations

import copy
import json
import os
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Final, Protocol

from . import messages
from .config import Provider, provider_from_env
from .errors import ModelError, ProviderUnavailable
from .validation import B5_SCHEMA_PATH

EXAMPLE_TRANSCRIPT: Final = (
    B5_SCHEMA_PATH.parent / "examples" / "model-interface.v1.transcript.json"
)


@dataclass(frozen=True)
class SpeechReply:
    """What a provider returns. The interface adds provider and latency_ms to meta itself."""

    segments: Any = field(repr=False)  # spoken content: never printed
    model: str
    duration_s: float
    # USD; 0.0 for a local model, None when not known (B5.1).
    cost_estimate: float | None


class SpeechProvider(Protocol):
    name: Provider

    def transcribe(self, audio_path: Path, language: str) -> SpeechReply: ...


class _NotIntegrated:
    """A real speech service whose protocol is not decided yet (design Q19)."""

    name: Provider

    def transcribe(self, audio_path: Path, language: str) -> SpeechReply:
        raise ProviderUnavailable(
            messages.SPEECH_NO_TRANSPORT.format(provider=self.name)
        )


class LocalSpeechProvider(_NotIntegrated):
    name: Provider = "local"


class HostedSpeechProvider(_NotIntegrated):
    name: Provider = "hosted"


class FakeSpeechProvider:
    """Deterministic, for tests. Answers from `replies` in order, then from the contract example.

    `fail_with` makes every call raise that error, to test failure handling. It records the calls,
    the languages asked for and the replies it sent, so tests can check what happened.
    """

    name: Provider = "fake"

    def __init__(
        self,
        replies: Sequence[SpeechReply] = (),
        fail_with: ModelError | None = None,
    ) -> None:
        self._replies = list(replies)
        self._fail_with = fail_with
        self.calls = 0
        self.languages: list[str] = []
        self.replies_sent: list[SpeechReply] = []

    def transcribe(self, audio_path: Path, language: str) -> SpeechReply:
        self.calls += 1
        self.languages.append(language)
        if self._fail_with is not None:
            raise self._fail_with
        reply = self._replies.pop(0) if self._replies else _example_reply()
        self.replies_sent.append(reply)
        return reply


def _example_reply() -> SpeechReply:
    doc = json.loads(EXAMPLE_TRANSCRIPT.read_text(encoding="utf-8"))
    return SpeechReply(
        segments=copy.deepcopy(doc["segments"]),
        model="fake-speech",
        duration_s=doc["meta"]["duration_s"],
        cost_estimate=0.0,
    )


def create_speech_provider() -> SpeechProvider:
    """The provider named by SPEECH_PROVIDER, after the fake-provider rule (reads os.environ)."""
    selected = provider_from_env(os.environ, "SPEECH_PROVIDER")
    if selected == "fake":
        return FakeSpeechProvider()
    if selected == "local":
        return LocalSpeechProvider()
    return HostedSpeechProvider()
