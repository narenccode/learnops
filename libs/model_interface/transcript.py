"""Transcript checks that JSON Schema cannot express (PRD B5.4).

JSON Schema cannot compare two fields, so contracts/model-interface.v1.schema.json cannot see a
segment that ends before it starts. Run this after the schema check, on producing and on reading.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Final

END_BEFORE_START: Final = (
    "segments[{index}] ends at {end} s, before it starts at {start} s. Times are seconds from the "
    "start of the original audio; check the chunk offset of the speech result."
)


def segment_time_errors(transcript: Mapping[str, Any]) -> list[str]:
    """One message per segment whose end is before its start; [] when every segment is valid.

    Expects a transcript that already passed the B5 schema. end == start is allowed (B5.4 says
    end >= start).
    """
    return [
        END_BEFORE_START.format(index=index, start=segment["start"], end=segment["end"])
        for index, segment in enumerate(transcript["segments"])
        if segment["end"] < segment["start"]
    ]
