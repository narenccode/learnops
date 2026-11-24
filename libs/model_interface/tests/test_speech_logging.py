"""Speech calls are logged like model calls (PRD B5.3 "every call", guide's decision on issue #186,
23 Nov 2026): the same call log, a `kind` field that says "speech", metadata only, failed calls
too, and a call that cannot be logged never returns a transcript.

The record is the B5 transcript meta (provider, model, duration_s, latency_ms, cost_estimate).
There is no token count or prompt_version for speech, and nothing in contracts/ changes."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from model_interface import call_log
from model_interface.call_log import (
    CallRecord,
    InMemoryCallLogger,
    get_call_logger,
)
from model_interface.errors import (
    CallLoggerMissing,
    InvalidOutput,
    ProviderUnavailable,
)
from model_interface.speech import transcribe
from model_interface.speech_providers import FakeSpeechProvider

from .test_speech import (
    broken,
    drop_text,
    example_reply,
    segment_backwards,
)

SPEECH_META_KEYS = {"provider", "model", "duration_s", "latency_ms", "cost_estimate"}


@pytest.fixture
def audio(tmp_path: Path) -> Path:
    path = tmp_path / "lecture.wav"
    path.write_bytes(b"RIFF\x00\x00\x00\x00WAVE")
    return path


@pytest.fixture
def speech_fake(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LEARNOPS_ENV", "test")
    monkeypatch.setenv("MODEL_ALLOW_FAKE", "true")
    monkeypatch.setenv("SPEECH_PROVIDER", "fake")


def logged() -> list[CallRecord]:
    logger = get_call_logger()
    assert isinstance(logger, InMemoryCallLogger)
    return logger.records


# --- the record ----------------------------------------------------------------------------


def test_a_call_record_is_a_model_record_unless_it_says_otherwise() -> None:
    assert CallRecord("task", 1, "ok", {}).kind == "model"
    assert CallRecord("speech.transcribe", 1, "ok", {}, kind="speech").kind == "speech"


def test_the_in_memory_logger_keeps_the_kind() -> None:
    logger = InMemoryCallLogger()
    logger.record(CallRecord("speech.transcribe", 1, "ok", {}, kind="speech"))
    logger.record(CallRecord("echo", 1, "ok", {}))
    assert [r.kind for r in logger.records] == ["speech", "model"]


# --- what is logged ------------------------------------------------------------------------


def test_one_successful_call_logs_one_speech_record(
    speech_fake: None,
    audio: Path,
) -> None:
    transcript = transcribe(audio, provider=FakeSpeechProvider())
    (record,) = logged()
    assert record.kind == "speech"
    assert record.task == "speech.transcribe"
    assert (record.attempt, record.outcome) == (1, "ok")
    assert set(record.meta) == SPEECH_META_KEYS
    assert record.meta == transcript.meta


def test_an_invalid_answer_then_a_good_one_logs_both_attempts(
    speech_fake: None,
    audio: Path,
) -> None:
    fake = FakeSpeechProvider(replies=[broken(drop_text), example_reply()])
    transcribe(audio, provider=fake)
    assert [(r.attempt, r.outcome) for r in logged()] == [
        (1, "invalid_output"),
        (2, "ok"),
    ]
    assert {r.kind for r in logged()} == {"speech"}
    # The meta of an invalid answer is the provider's own report, so it is kept.
    assert set(logged()[0].meta) == SPEECH_META_KEYS


def test_two_invalid_answers_log_two_failed_attempts_and_raise(
    speech_fake: None,
    audio: Path,
) -> None:
    fake = FakeSpeechProvider(replies=[broken(segment_backwards)] * 2)
    with pytest.raises(InvalidOutput):
        transcribe(audio, provider=fake)
    assert [(r.attempt, r.outcome) for r in logged()] == [
        (1, "invalid_output"),
        (2, "invalid_output"),
    ]


def test_a_provider_failure_is_logged_with_unknown_values(
    speech_fake: None,
    audio: Path,
) -> None:
    fake = FakeSpeechProvider(fail_with=ProviderUnavailable("down"))
    with pytest.raises(ProviderUnavailable):
        transcribe(audio, provider=fake)
    (record,) = logged()
    assert (record.kind, record.attempt, record.outcome) == (
        "speech",
        1,
        "provider_error",
    )
    # Nothing was answered, so the model, the audio length and the cost are not known (null,
    # never 0), as for a failed model call. The time spent is known.
    assert record.meta["provider"] == "fake"
    assert record.meta["model"] is None
    assert record.meta["duration_s"] is None
    assert record.meta["cost_estimate"] is None
    assert isinstance(record.meta["latency_ms"], int)


def test_a_reply_with_a_broken_meta_is_logged_with_unknown_values(
    speech_fake: None,
    audio: Path,
) -> None:
    reply = example_reply()
    bad = type(reply)(reply.segments, reply.model, -5.0, reply.cost_estimate)
    fake = FakeSpeechProvider(replies=[bad, example_reply()])
    transcribe(audio, provider=fake)
    first = logged()[0]
    assert first.outcome == "invalid_output"
    assert first.meta["duration_s"] is None  # the reported -5.0 is not logged


# --- metadata only -------------------------------------------------------------------------


def test_a_record_holds_no_audio_path_and_no_transcript_text(
    speech_fake: None,
    audio: Path,
) -> None:
    fake = FakeSpeechProvider(replies=[broken(drop_text), example_reply()])
    transcript = transcribe(audio, provider=fake)
    text = repr(logged())
    assert audio.name not in text and str(audio.parent) not in text
    for segment in transcript.segments:
        assert segment["text"] == "" or segment["text"] not in text
    assert set(logged()[0].meta) <= SPEECH_META_KEYS


# --- a call that cannot be logged never returns a transcript --------------------------------


class FailingLogger:
    def record(self, record: CallRecord) -> None:
        raise RuntimeError("the log is down")


def test_a_logger_that_fails_stops_the_call(
    speech_fake: None,
    audio: Path,
) -> None:
    with pytest.raises(RuntimeError, match="log is down"):
        transcribe(audio, provider=FakeSpeechProvider(), logger=FailingLogger())


def test_no_call_logger_outside_a_test_run_refuses_before_the_provider_is_called(
    monkeypatch: pytest.MonkeyPatch,
    audio: Path,
) -> None:
    fake = FakeSpeechProvider()
    monkeypatch.setattr("model_interface.speech._resolve", lambda provider: fake)
    monkeypatch.setattr(call_log, "is_test_run", lambda: False)
    with pytest.raises(CallLoggerMissing):
        transcribe(audio)
    assert fake.calls == 0


def test_logging_does_not_change_what_the_caller_gets(
    speech_fake: None,
    audio: Path,
) -> None:
    first: Any = transcribe(audio, provider=FakeSpeechProvider())
    assert first.as_dict()["meta"].keys() == SPEECH_META_KEYS
