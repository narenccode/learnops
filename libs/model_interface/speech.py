"""speech.transcribe(audio_path, language="en") (PRD B5.4, FR-M-02 skeleton).

Steps: refuse a language that is not text and an audio file that cannot be read, before any
provider call; find the provider named by SPEECH_PROVIDER (a passed one is for test runs only);
call it; check the answer against the B5 transcript schema and the time rule (segment and word
end at or after start); on an invalid answer retry once, then raise InvalidOutput. An invalid or
partial transcript is never returned.

latency_ms is LearnOps's own measurement, rounded to whole milliseconds (guide, 15 Nov, decision
0001 row 2). Not checked, by the guide's decision (rows 10 and 11): time order, and times past
duration_s.

Every attempt is logged (PRD B5.3 "every call"; guide, issue #186, 23 Nov 2026): one CallRecord
with kind "speech" per attempt, also a failed one, holding the transcript meta only (no audio path,
no transcript text). A provider failure and a broken meta are logged with unknown (null) values.
If the logger fails, that error is raised, so a call that could not be logged never returns a
transcript. With no logger configured outside a test run the call is refused before the provider is
called.

Not in this skeleton (design proposals, not decided): SPEECH_TIMEOUT_S and the budget, and how
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
from .call_log import CallLogger, CallRecord, is_test_run, resolve_call_logger
from .config import ConfigError
from .errors import AudioNotReadable, InvalidInput, InvalidOutput
from .speech_providers import (
    SpeechProvider,
    SpeechReply,
    create_speech_provider,
    ensure_integrated,
)
from .transcript import time_errors
from .validation import b5_validator, elapsed_ms, first_problem

# PRD B5.2 ("same rules" for speech, B5.4): one retry on invalid output.
MAX_ATTEMPTS: Final = 2

TASK: Final = "speech.transcribe"  # the task name in the call log


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


def _meta(
    provider: SpeechProvider,
    latency_ms: int,
    document: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """The transcript meta to log. Without a usable answer the model, the audio length and the cost
    are not known, so they are null, never 0. Nothing but these five fields is ever logged."""
    meta = document["meta"] if document is not None else {}
    return {
        "provider": provider.name,
        "model": meta.get("model"),
        "duration_s": meta.get("duration_s"),
        "latency_ms": latency_ms,
        "cost_estimate": meta.get("cost_estimate"),
    }


def _meta_is_valid(meta: dict[str, Any]) -> bool:
    # The meta alone, in a transcript with no segments, so a bad meta is told from bad segments.
    return first_problem(b5_validator(), {"segments": [], "meta": meta}) is None


def transcribe(
    audio_path: str | os.PathLike[str],
    language: str = "en",
    *,
    provider: SpeechProvider | None = None,
    logger: CallLogger | None = None,
) -> Transcript:
    """One transcript with times from the start of the original audio (PRD B5.4).

    Services pass neither provider nor logger and get the configured ones; passing a different
    provider or logger is for test runs only. The logger receives one CallRecord per attempt."""
    if not isinstance(language, str) or not language.strip():
        raise InvalidInput(messages.SPEECH_BAD_LANGUAGE)
    path = _readable_file(audio_path)
    chosen = _resolve(provider)
    ensure_integrated(
        chosen
    )  # the clear "not integrated" error comes before the call log is read
    call_logger = resolve_call_logger(logger)
    problem: str | None = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        started = time.perf_counter()
        try:
            reply = chosen.transcribe(path, language)
        except Exception:
            meta = _meta(chosen, elapsed_ms(started))
            call_logger.record(
                CallRecord(TASK, attempt, "provider_error", meta, "speech")
            )
            raise
        document = _document(chosen, reply, elapsed_ms(started))
        problem = _problem(document)
        if problem is None:
            call_logger.record(
                CallRecord(
                    TASK,
                    attempt,
                    "ok",
                    _meta(chosen, document["meta"]["latency_ms"], document),
                    "speech",
                )
            )
            return Transcript(segments=document["segments"], meta=document["meta"])
        # A broken answer: keep the reported meta only if it is itself valid.
        usable = document if _meta_is_valid(document["meta"]) else None
        latency_ms = document["meta"]["latency_ms"]
        call_logger.record(
            CallRecord(
                TASK,
                attempt,
                "invalid_output",
                _meta(chosen, latency_ms, usable),
                "speech",
            )
        )
    raise InvalidOutput(messages.SPEECH_INVALID_OUTPUT.format(problem=problem))
