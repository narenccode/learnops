"""Segment time rule (PRD B5.4): a segment ends at or after its start.

The B5 schema cannot compare two fields (libs/contracts/tests/test_model_interface_v1.py shows it
accepts end < start), so segment_time_errors is where the rule is enforced.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest

from model_interface.transcript import segment_time_errors

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
