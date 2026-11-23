"""speech.transcribe(audio_path, language) (PRD B5.4, FR-M-02 skeleton).

Mock-tested only: the fake provider is built from the B5 contract example, and local and hosted
refuse until a real transport exists (ADR 0002, PR #98). No audio is decoded and no server is called.
The audio files here are a few synthetic bytes, never a real recording (CLAUDE.md rule 4).
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest

import model_interface
from model_interface.config import ConfigError
from model_interface.errors import (
    AudioNotReadable,
    InvalidInput,
    InvalidOutput,
    ProviderUnavailable,
)
from model_interface.speech import Transcript, transcribe
from model_interface.speech_providers import (
    FakeSpeechProvider,
    HostedSpeechProvider,
    LocalSpeechProvider,
    SpeechReply,
    create_speech_provider,
)
from model_interface.validation import b5_validator, first_problem

EXAMPLE = (
    Path(__file__).resolve().parents[3]
    / "contracts"
    / "examples"
    / "model-interface.v1.transcript.json"
)


@pytest.fixture
def audio(tmp_path: Path) -> Path:
    """A synthetic file: the skeleton never reads its content, only that it exists and is readable."""
    path = tmp_path / "lecture.wav"
    path.write_bytes(b"RIFF\x00\x00\x00\x00WAVE")
    return path


@pytest.fixture
def speech_fake(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LEARNOPS_ENV", "test")
    monkeypatch.setenv("MODEL_ALLOW_FAKE", "true")
    monkeypatch.setenv("SPEECH_PROVIDER", "fake")


def example_reply() -> SpeechReply:
    doc = json.loads(EXAMPLE.read_text(encoding="utf-8"))
    return SpeechReply(
        segments=doc["segments"],
        model="fake-speech",
        duration_s=doc["meta"]["duration_s"],
        cost_estimate=0.0,
    )


# --- the call shape and the B5 transcript --------------------------------------------------


def test_the_fake_returns_a_valid_b5_transcript(speech_fake: None, audio: Path) -> None:
    transcript = transcribe(audio, language="en")
    assert isinstance(transcript, Transcript)
    assert first_problem(b5_validator(), transcript.as_dict()) is None
    assert transcript.meta["provider"] == "fake"
    assert set(transcript.meta) == {
        "provider",
        "model",
        "duration_s",
        "latency_ms",
        "cost_estimate",
    }


def test_language_defaults_to_english(speech_fake: None, audio: Path) -> None:
    fake = FakeSpeechProvider()
    transcribe(audio, provider=fake)
    assert fake.languages == ["en"]


def test_latency_ms_is_measured_here_as_a_whole_number(
    speech_fake: None, audio: Path
) -> None:
    """Guide, 15 Nov (decision 0001 row 2): LearnOps measures it, rounded to whole milliseconds."""
    latency = transcribe(audio).meta["latency_ms"]
    assert type(latency) is int and latency >= 0


def test_the_transcript_is_a_copy(speech_fake: None, audio: Path) -> None:
    fake = FakeSpeechProvider(replies=[example_reply()])
    transcript = transcribe(audio, provider=fake)
    transcript.segments[0]["text"] = "changed"
    assert fake.replies_sent[0].segments[0]["text"] != "changed"


def test_the_package_exports_transcribe() -> None:
    assert model_interface.transcribe is transcribe
    assert "transcribe" in model_interface.__all__


# --- providers and the fake-provider rule (B5.2, B5.4) -------------------------------------


def test_fake_is_refused_outside_a_test_run(
    monkeypatch: pytest.MonkeyPatch, audio: Path
) -> None:
    monkeypatch.setenv("SPEECH_PROVIDER", "fake")
    with pytest.raises(ConfigError):
        transcribe(audio)


@pytest.mark.parametrize(
    ("name", "cls"), [("local", LocalSpeechProvider), ("hosted", HostedSpeechProvider)]
)
def test_local_and_hosted_refuse_until_a_transport_exists(
    monkeypatch: pytest.MonkeyPatch, audio: Path, name: str, cls: type
) -> None:
    monkeypatch.setenv("SPEECH_PROVIDER", name)
    assert isinstance(create_speech_provider(), cls)
    with pytest.raises(ProviderUnavailable) as raised:
        transcribe(audio)
    assert "ADR 0002" in str(raised.value)
    assert "Q19" not in str(
        raised.value
    )  # Q19 is the model provider, not the speech service


def test_an_unset_speech_provider_is_a_clear_error(audio: Path) -> None:
    with pytest.raises(ConfigError) as raised:
        transcribe(audio)
    assert "SPEECH_PROVIDER" in str(raised.value)


def test_passing_a_provider_is_for_test_runs_only(
    monkeypatch: pytest.MonkeyPatch, audio: Path
) -> None:
    monkeypatch.setenv("SPEECH_PROVIDER", "local")
    with pytest.raises(ConfigError):
        transcribe(audio, provider=FakeSpeechProvider())


# --- input checks before any provider call -------------------------------------------------


def test_a_missing_file_is_refused_before_the_provider_is_called(
    speech_fake: None, tmp_path: Path
) -> None:
    fake = FakeSpeechProvider()
    missing = tmp_path / "learner-name-lecture.wav"
    with pytest.raises(AudioNotReadable) as raised:
        transcribe(missing, provider=fake)
    assert fake.calls == 0
    assert "learner-name" not in str(raised.value)  # the path is never echoed


def test_a_folder_is_not_an_audio_file(speech_fake: None, tmp_path: Path) -> None:
    with pytest.raises(AudioNotReadable):
        transcribe(tmp_path)


@pytest.mark.parametrize("language", ["", "   ", None, 3])
def test_language_must_be_a_non_empty_string(
    speech_fake: None, audio: Path, language: Any
) -> None:
    fake = FakeSpeechProvider()
    with pytest.raises(InvalidInput):
        transcribe(audio, language=language, provider=fake)
    assert fake.calls == 0


# --- validation, one retry, then a clear error (B5.2 "same rules") -------------------------


def broken(change: Any) -> SpeechReply:
    reply = example_reply()
    segments = copy.deepcopy(reply.segments)
    change(segments)
    return SpeechReply(segments, reply.model, reply.duration_s, reply.cost_estimate)


def drop_text(segments: list[dict[str, Any]]) -> None:
    del segments[0]["text"]


def segment_backwards(segments: list[dict[str, Any]]) -> None:
    segments[0]["start"], segments[0]["end"] = 2.4, 0.0


def word_backwards(segments: list[dict[str, Any]]) -> None:
    segments[1]["words"][0]["start"], segments[1]["words"][0]["end"] = 3.4, 2.9


@pytest.mark.parametrize("change", [drop_text, segment_backwards, word_backwards])
def test_one_invalid_answer_is_retried_once(
    speech_fake: None, audio: Path, change: Any
) -> None:
    fake = FakeSpeechProvider(replies=[broken(change), example_reply()])
    transcript = transcribe(audio, provider=fake)
    assert fake.calls == 2
    assert first_problem(b5_validator(), transcript.as_dict()) is None


@pytest.mark.parametrize("change", [drop_text, segment_backwards, word_backwards])
def test_two_invalid_answers_raise_and_return_nothing(
    speech_fake: None, audio: Path, change: Any
) -> None:
    fake = FakeSpeechProvider(replies=[broken(change), broken(change), example_reply()])
    with pytest.raises(InvalidOutput) as raised:
        transcribe(audio, provider=fake)
    assert fake.calls == 2
    assert "Welcome" not in str(raised.value)  # no transcript text in the message


def test_a_provider_failure_is_not_retried(speech_fake: None, audio: Path) -> None:
    fake = FakeSpeechProvider(fail_with=ProviderUnavailable("down"))
    with pytest.raises(ProviderUnavailable):
        transcribe(audio, provider=fake)
    assert fake.calls == 1


# --- what is deliberately NOT a rule (guide, 15 Nov, decision 0001 rows 10 and 11) ----------


def test_segments_out_of_time_order_are_accepted(
    speech_fake: None, audio: Path
) -> None:
    fake = FakeSpeechProvider(replies=[broken(lambda s: s.reverse())])
    transcript = transcribe(audio, provider=fake)
    assert fake.calls == 1
    assert transcript.segments[0]["start"] > transcript.segments[1]["start"]


def test_times_past_duration_are_accepted(speech_fake: None, audio: Path) -> None:
    def past_the_end(segments: list[dict[str, Any]]) -> None:
        segments[-1]["end"] = 999.0
        segments[-1]["words"][-1]["end"] = 999.0

    fake = FakeSpeechProvider(replies=[broken(past_the_end)])
    assert transcribe(audio, provider=fake).segments[-1]["end"] == 999.0


def test_silent_audio_gives_an_empty_transcript(speech_fake: None, audio: Path) -> None:
    fake = FakeSpeechProvider(replies=[SpeechReply([], "fake-speech", 5.0, 0.0)])
    assert transcribe(audio, provider=fake).segments == []
