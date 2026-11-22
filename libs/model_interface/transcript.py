"""Transcript checks that JSON Schema cannot express (PRD B5.4).

JSON Schema cannot compare two fields, so contracts/model-interface.v1.schema.json cannot see a
segment or a word that ends before it starts. Run these after the schema check, on producing and
on reading.

Deliberately not checked, by the guide's decision (docs/decisions/0001, rows 10 and 11): time
order, and times past duration_s. A consumer sorts by start, and a reader must not fail on a
time a little past the audio end.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Final

END_BEFORE_START: Final = (
    "{where} ends at {end} s, before it starts at {start} s. Times are seconds from the "
    "start of the original audio; check the chunk offset of the speech result."
)


def _ends_before_start(where: str, item: Mapping[str, Any]) -> str | None:
    if item["end"] < item["start"]:
        return END_BEFORE_START.format(
            where=where, start=item["start"], end=item["end"]
        )
    return None


def segment_time_errors(transcript: Mapping[str, Any]) -> list[str]:
    """One message per segment whose end is before its start; [] when every segment is valid.

    Expects a transcript that already passed the B5 schema. end == start is allowed (B5.4 says
    end >= start).
    """
    checked = (
        _ends_before_start(f"segments[{index}]", segment)
        for index, segment in enumerate(transcript["segments"])
    )
    return [message for message in checked if message is not None]


def word_time_errors(transcript: Mapping[str, Any]) -> list[str]:
    """One message per word whose end is before its start, the same rule as a segment.

    A segment with `words: []` has nothing to check (B5.4 allows it).
    """
    checked = (
        _ends_before_start(f"segments[{s}].words[{w}]", word)
        for s, segment in enumerate(transcript["segments"])
        for w, word in enumerate(segment["words"])
    )
    return [message for message in checked if message is not None]


def time_errors(transcript: Mapping[str, Any]) -> list[str]:
    """Every segment error, then every word error; [] when the transcript's times are valid."""
    return segment_time_errors(transcript) + word_time_errors(transcript)
