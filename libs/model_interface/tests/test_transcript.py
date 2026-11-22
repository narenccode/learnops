"""Time rules (PRD B5.4): a segment, and a word, ends at or after its start.

The B5 schema cannot compare two fields (libs/contracts/tests/test_model_interface_v1.py shows it
accepts end < start), so segment_time_errors and word_time_errors are where the rules are enforced.
Time order and times past duration_s have no rule (guide, decision 0001, rows 10 and 11).
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest

from model_interface.transcript import (
    segment_time_errors,
    time_errors,
    word_time_errors,
)

EXAMPLES = Path(__file__).resolve().parents[3] / "contracts" / "examples"
TRANSCRIPTS = sorted(EXAMPLES.glob("model-interface.v1.transcript*.json"))


def load(path: Path) -> dict[str, Any]:
    loaded: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return loaded


def transcript() -> dict[str, Any]:
    return copy.deepcopy(load(EXAMPLES / "model-interface.v1.transcript.json"))


def test_there_are_transcript_examples() -> None:
    assert len(TRANSCRIPTS) >= 6


@pytest.mark.parametrize("path", TRANSCRIPTS, ids=lambda p: p.name)
def test_every_transcript_example_has_valid_segment_times(path: Path) -> None:
    assert segment_time_errors(load(path)) == []


def test_silent_audio_has_no_errors() -> None:
    assert segment_time_errors({"segments": [], "meta": {}}) == []


def test_zero_length_segment_is_valid() -> None:
    doc = transcript()
    doc["segments"][0]["end"] = doc["segments"][0]["start"]
    assert segment_time_errors(doc) == []


def test_segment_ending_before_it_starts_is_rejected() -> None:
    doc = transcript()
    doc["segments"][1]["start"], doc["segments"][1]["end"] = 5.6, 2.9
    errors = segment_time_errors(doc)
    assert len(errors) == 1
    assert errors[0].startswith("segments[1] ends at 2.9 s, before it starts at 5.6 s.")


def test_every_bad_segment_is_reported() -> None:
    doc = transcript()
    for segment in doc["segments"]:
        segment["end"] = segment["start"] - 0.1
    assert [e.split(" ")[0] for e in segment_time_errors(doc)] == [
        "segments[0]",
        "segments[1]",
    ]


def test_end_left_relative_to_its_chunk_is_rejected() -> None:
    """A segment whose start got the 1800 s chunk offset but whose end did not."""
    doc = load(EXAMPLES / "model-interface.v1.transcript-chunked.json")
    doc["segments"][1]["end"] = 3.1
    assert len(segment_time_errors(doc)) == 1


# --- words (guide's decision 9: the same rule as a segment) ----------------------------------


@pytest.mark.parametrize("path", TRANSCRIPTS, ids=lambda p: p.name)
def test_every_transcript_example_has_valid_word_times(path: Path) -> None:
    assert word_time_errors(load(path)) == []


def test_a_segment_without_words_has_no_word_errors() -> None:
    doc = transcript()
    doc["segments"][0]["words"] = []
    assert word_time_errors(doc) == []


def test_zero_length_word_is_valid() -> None:
    doc = transcript()
    word = doc["segments"][0]["words"][0]
    word["end"] = word["start"]
    assert word_time_errors(doc) == []


def test_word_ending_before_it_starts_is_rejected() -> None:
    doc = transcript()
    word = doc["segments"][1]["words"][2]
    word["start"], word["end"] = 4.1, 3.6
    errors = word_time_errors(doc)
    assert len(errors) == 1
    assert errors[0].startswith(
        "segments[1].words[2] ends at 3.6 s, before it starts at 4.1 s."
    )


def test_every_bad_word_is_reported() -> None:
    doc = transcript()
    for index in (0, 3):
        doc["segments"][0]["words"][index]["end"] = (
            doc["segments"][0]["words"][index]["start"] - 0.1
        )
    assert [e.split(" ")[0] for e in word_time_errors(doc)] == [
        "segments[0].words[0]",
        "segments[0].words[3]",
    ]


def test_time_errors_reports_segments_then_words() -> None:
    doc = transcript()
    doc["segments"][1]["start"], doc["segments"][1]["end"] = 5.6, 2.9
    doc["segments"][0]["words"][1]["end"] = 0.1
    assert [e.split(" ")[0] for e in time_errors(doc)] == [
        "segments[1]",
        "segments[0].words[1]",
    ]


def test_time_order_and_times_past_duration_have_no_rule() -> None:
    """Guide's decisions 10 and 11: a consumer sorts; a reader must not fail past duration_s."""
    doc = transcript()
    doc["segments"].reverse()
    doc["segments"][0]["end"] = doc["meta"]["duration_s"] + 100
    doc["segments"][0]["words"][-1]["end"] = doc["meta"]["duration_s"] + 100
    assert time_errors(doc) == []
