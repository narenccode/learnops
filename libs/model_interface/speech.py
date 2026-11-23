"""speech.transcribe(audio_path, language="en") (PRD B5.4, FR-M-02 skeleton).

Steps: refuse a language that is not text and an audio file that cannot be read, before any
provider call; find the provider named by SPEECH_PROVIDER (a passed one is for test runs only);
call it; check the answer against the B5 transcript schema and the time rule (segment and word
end at or after start); on an invalid answer retry once, then raise InvalidOutput. An invalid or
partial transcript is never returned.

latency_ms is LearnOps's own measurement, rounded to whole milliseconds (guide, 15 Nov, decision
0001 row 2). Not checked, by the guide's decision (rows 10 and 11): time order, and times past
duration_s.

Not in this skeleton: logging speech calls to shared.model_calls (decided by the guide on issue
#186, 23 Nov 2026, and built in PR #187), SPEECH_TIMEOUT_S and the budget (design proposals), and how
long audio is split (a lab check with a 90-minute file). Provider failures are not retried here.
"""

from __future__ import annotations

import copy
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Final

from . import messages
from .call_log import is_test_run
from .config import ConfigError
from .errors import AudioNotReadable, InvalidInput, InvalidOutput
from .speech_providers import SpeechProvider, SpeechReply, create_speech_provider
from .transcript import time_errors
from .validation import b5_validator, elapsed_ms, first_problem

# PRD B5.2 ("same rules" for speech, B5.4): one retry on invalid output.
MAX_ATTEMPTS: Final = 2


@dataclass(frozen=True)
class Transcript:
    # Spoken content of a recording: repr() leaves it out.
    segments: list[dict[str, Any]] = field(repr=False)
    # provider, model, duration_s, latency_ms, cost_estimate (B5.4).
    meta: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        """The B5 transcript document: {"segments": [...], "meta": {...}}."""
        return {"segments": copy.deepcopy(self.segments), "meta": dict(self.meta)}


def _readable_file(audio_path: str | os.PathLike[str]) -> Path:
    path = Path(audio_path)
    if not (path.is_file() and os.access(path, os.R_OK)):
        raise AudioNotReadable(messages.AUDIO_NOT_READABLE)  # the path is never echoed
    return path


def _resolve(provider: SpeechProvider | None) -> SpeechProvider:
    if provider is None:
        return create_speech_provider()
    if not is_test_run():
        raise ConfigError(messages.SPEECH_PROVIDER_PASSED)
    return provider


def _document(
    provider: SpeechProvider, reply: SpeechReply, latency_ms: int
) -> dict[str, Any]:
    return {
        "segments": copy.deepcopy(reply.segments),
        "meta": {
            "provider": provider.name,
            "model": reply.model,
            "duration_s": reply.duration_s,
            "latency_ms": latency_ms,
            "cost_estimate": reply.cost_estimate,
        },
    }


def _problem(document: dict[str, Any]) -> str | None:
    problem = first_problem(b5_validator(), document)
    if problem is None and time_errors(document):
        # Never the times or the text: only that the rule is broken.
        problem = messages.SPEECH_TIMES_BACKWARDS
    return problem


def transcribe(
    audio_path: str | os.PathLike[str],
    language: str = "en",
    *,
    provider: SpeechProvider | None = None,
) -> Transcript:
    """One transcript with times from the start of the original audio (PRD B5.4)."""
    if not isinstance(language, str) or not language.strip():
        raise InvalidInput(messages.SPEECH_BAD_LANGUAGE)
    path = _readable_file(audio_path)
    chosen = _resolve(provider)
    problem: str | None = None
    for _ in range(MAX_ATTEMPTS):
        started = time.perf_counter()
        reply = chosen.transcribe(path, language)
        document = _document(chosen, reply, elapsed_ms(started))
        problem = _problem(document)
        if problem is None:
            return Transcript(segments=document["segments"], meta=document["meta"])
    raise InvalidOutput(messages.SPEECH_INVALID_OUTPUT.format(problem=problem))
