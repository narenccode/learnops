"""Validators for the lesson files `chapters.json`, `slides.json` and `cues.json` (PRD B6.2).

Each `validate_*` function takes the parsed file (a JSON array), checks it against the JSON Schema
in `contracts/` and then applies the rules a JSON Schema cannot express. It returns the same
`ValidationReport` as the B1 validator: `errors` block, and `not_checked` lists what did not run.

The path rules (slide thumbnails, image refs) come from the schemas, which carry the manifest's
`relative_path` pattern, so there is one implementation of that rule here, not a second one.

Times are compared with `duration_s` of the manifest only by `check_within_duration`. That is a
rule for a consumer that has both files: the JSON Schemas cannot do it.
"""

from __future__ import annotations

import functools
import json
import math
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, cast

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import ValidationError

from . import messages
from .report import Issue, Location, ValidationReport
from .schema import error_order

RULE = "B6.2"
CONTRACTS_DIR = Path(__file__).resolve().parents[2] / "contracts"

CHAPTERS_FILE = "chapters.json"
SLIDES_FILE = "slides.json"
CUES_FILE = "cues.json"

# The cue types this version of the contract defines (PRD B6.2, FR-X-12). The schema accepts any
# type in the slug form of a track role (lowercase ASCII letters and digits, single hyphens), and a
# v1 reader ignores the others.
SUPPORTED_CUE_TYPES = frozenset({"h5p", "image", "url"})


@functools.cache
def _schema(schema_file: str) -> dict[str, Any]:
    return cast(
        "dict[str, Any]",
        json.loads((CONTRACTS_DIR / schema_file).read_text(encoding="utf-8")),
    )


@functools.cache
def _validator(schema_file: str) -> Draft202012Validator:
    return Draft202012Validator(_schema(schema_file), format_checker=FormatChecker())


@functools.cache
def _pattern_texts() -> dict[str, tuple[str, str]]:
    """The message and hint for a `pattern` that fails, keyed by the pattern text, so that the
    report does not show a regular expression of hundreds of characters (UI-05). The patterns
    are read from the schemas, so this stays right when a schema changes. Every other error
    keeps the message of the JSON Schema library, as in the B1 validator."""
    slides, cues = _schema("slides.v1.schema.json"), _schema("cues.v1.schema.json")
    thumb = slides["$defs"]["slide"]["properties"]["thumb"]["allOf"]
    h5p = cues["$defs"]["cue"]["allOf"][0]["then"]["properties"]["ref"]["pattern"]
    return {
        slides["$defs"]["relative_path"]["pattern"]: messages.PATH_NOT_RELATIVE,
        thumb[1]["pattern"]: messages.THUMB_NOT_IN_SLIDES,
        cues["$defs"]["https_url"]["pattern"]: messages.URL_NOT_HTTPS,
        h5p: messages.H5P_REF_NOT_IDNUMBER,
        r"\S": messages.TEXT_IS_BLANK,
    }


def _schema_issues(document: object, filename: str, schema_file: str) -> list[Issue]:
    errors = sorted(_validator(schema_file).iter_errors(document), key=error_order)
    return [_schema_issue(error, filename, schema_file) for error in errors]


def _schema_issue(error: ValidationError, filename: str, schema_file: str) -> Issue:
    location: Location = tuple(error.absolute_path)
    where = messages.lesson_file_where(filename, location)
    pattern = error.validator_value
    texts = (
        _pattern_texts().get(pattern)
        if error.validator == "pattern" and isinstance(pattern, str)
        else None
    )
    if texts is not None:
        message, hint = texts
        return Issue(
            code="schema_pattern",
            rule=RULE,
            message=message.format(where=where, value=error.instance),
            fix_hint=f"{hint} {messages.LESSON_FILE_SEE_SCHEMA.format(schema=schema_file)}",
            location=location,
        )
    return Issue(
        code=f"schema_{error.validator}",
        rule=RULE,
        message=messages.LESSON_FILE_SCHEMA_ERROR.format(
            where=where, detail=error.message
        ),
        fix_hint=messages.LESSON_FILE_SCHEMA_HINT.format(
            filename=filename, schema=schema_file
        ),
        location=location,
    )


def _held(*rules: tuple[str, str, str]) -> tuple[Issue, ...]:
    return tuple(
        Issue(code=code, rule=rule, message=text, fix_hint=messages.NOT_CHECKED_HINT)
        for code, rule, text in rules
    )


def _non_finite_times(
    document: Sequence[Mapping[str, Any]], filename: str, fields: tuple[str, ...]
) -> list[Issue]:
    """Times that are NaN or infinite. Python's JSON reader accepts them, JSON does not, and the
    schema's `minimum` does not stop NaN, so the validator does. Only a float can be NaN or
    infinite: an int is always finite, and `math.isfinite` raises OverflowError for an int too
    large for a float (for example 10**400)."""
    issues = []
    for index, entry in enumerate(document):
        for field in fields:
            value = entry[field]
            if isinstance(value, float) and not math.isfinite(value):
                location: Location = (index, field)
                issues.append(
                    Issue(
                        code="time_not_finite",
                        rule=RULE,
                        message=messages.TIME_NOT_FINITE.format(
                            where=messages.lesson_file_where(filename, location),
                            value=value,
                        ),
                        fix_hint=messages.TIME_NOT_FINITE_HINT,
                        location=location,
                    )
                )
    return issues


def _chapter_order_issues(chapters: Sequence[Mapping[str, Any]]) -> list[Issue]:
    issues: list[Issue] = []

    def add(code: str, message: str, hint: str, location: Location) -> None:
        issues.append(
            Issue(
                code=code, rule=RULE, message=message, fix_hint=hint, location=location
            )
        )

    latest_end = 0.0  # the largest `end` among the chapters before this one
    for index, chapter in enumerate(chapters):
        start, end = chapter["start"], chapter["end"]
        where = messages.lesson_file_where(CHAPTERS_FILE, (index,))
        if end <= start:
            add(
                "chapter_end_not_after_start",
                messages.CHAPTER_END_NOT_AFTER_START.format(
                    where=where, start=start, end=end
                ),
                messages.CHAPTER_END_NOT_AFTER_START_HINT,
                (index, "end"),
            )
        if index == 0:
            latest_end = end
            continue
        previous = chapters[index - 1]
        earlier_end, latest_end = latest_end, max(latest_end, end)
        if start < previous["start"]:
            add(
                "chapters_not_in_order",
                messages.CHAPTER_NOT_IN_ORDER.format(
                    where=where, start=start, previous=previous["start"]
                ),
                messages.CHAPTER_NOT_IN_ORDER_HINT,
                (index, "start"),
            )
        elif start < earlier_end:
            # Compared with the latest end of ALL earlier chapters, not only the previous one,
            # so a chapter inside an earlier, longer one is reported too. Only for chapters that
            # are in order, so one mistake is reported once. A chapter that starts exactly where
            # an earlier one ends is not an overlap.
            add(
                "chapters_overlap",
                messages.CHAPTER_OVERLAP.format(
                    where=where, start=start, previous_end=earlier_end
                ),
                messages.CHAPTER_OVERLAP_HINT,
                (index, "start"),
            )
    return issues


def validate_chapters(document: object) -> ValidationReport:
    """`chapters.json`: `[{start, end, title}]`. Besides the schema: end after start, ascending
    order of start, no overlap. Gaps between chapters are allowed."""
    held = _held(messages.LESSON_FILE_HELD_DURATION, messages.LESSON_FILE_HELD_FILES)
    errors = _schema_issues(document, CHAPTERS_FILE, "chapters.v1.schema.json")
    if errors:
        return ValidationReport(errors=tuple(errors), not_checked=held)
    chapters = cast("list[Mapping[str, Any]]", document)
    errors = _non_finite_times(chapters, CHAPTERS_FILE, ("start", "end"))
    if not errors:
        errors = _chapter_order_issues(chapters)
    return ValidationReport(errors=tuple(errors), not_checked=held)


def validate_slides(document: object) -> ValidationReport:
    """`slides.json`: `[{t, thumb, text?}]`. The thumbnail path rules are in the schema."""
    held = _held(messages.LESSON_FILE_HELD_DURATION, messages.LESSON_FILE_HELD_FILES)
    errors = _schema_issues(document, SLIDES_FILE, "slides.v1.schema.json")
    if not errors:
        slides = cast("list[Mapping[str, Any]]", document)
        errors = _non_finite_times(slides, SLIDES_FILE, ("t",))
    return ValidationReport(errors=tuple(errors), not_checked=held)


def validate_cues(document: object) -> ValidationReport:
    """`cues.json`: `[{t, type, ref, label, required?}]`. The form of `ref` for the types h5p,
    image and url is in the schema. An empty array is valid. A cue with another type in the slug form
    (for example `quiz-2`) is valid too: a v1 reader ignores it (`readable_cues`). A type with an
    underscore, a dot, a space or an uppercase letter is an error."""
    held = _held(
        messages.LESSON_FILE_HELD_DURATION,
        messages.LESSON_FILE_HELD_FILES,
        messages.LESSON_FILE_HELD_H5P,
        messages.LESSON_FILE_HELD_URL,
    )
    errors = _schema_issues(document, CUES_FILE, "cues.v1.schema.json")
    if not errors:
        cues = cast("list[Mapping[str, Any]]", document)
        errors = _non_finite_times(cues, CUES_FILE, ("t",))
    return ValidationReport(errors=tuple(errors), not_checked=held)


def readable_cues(
    document: Sequence[Mapping[str, Any]] | None,
) -> list[Mapping[str, Any]]:
    """What a v1 reader acts on: the cues whose type it knows. Others are ignored, not errors.

    `document` must already be valid (`validate_cues`), or `None` when the lesson has no
    `cues.json`. A missing file and an empty array both mean no cues.
    """
    if document is None:
        return []
    return [cue for cue in document if cue["type"] in SUPPORTED_CUE_TYPES]


def cue_is_required(cue: Mapping[str, Any]) -> bool:
    """True when the learner cannot skip the cue. A missing `required` means false."""
    return cue.get("required", False) is True


def check_within_duration(
    duration_s: float,
    *,
    chapters: Sequence[Mapping[str, Any]] = (),
    slides: Sequence[Mapping[str, Any]] = (),
    cues: Sequence[Mapping[str, Any]] = (),
) -> ValidationReport:
    """Consumer-level rule: every time is at most `duration_s` of the manifest (lesson.json).

    `duration_s` is used exactly as the manifest gives it: it is not rounded and there is no
    tolerance (guide decision), so a chapter that ends 0.001 s after it is an error. Every chapter
    `start` and `end` and every cue `t` is checked (and every slide `t`).

    The three documents must already be valid. A JSON Schema cannot do this check, because the
    two values are in different files. Pass only the files the lesson has. Raises `ValueError`
    when `duration_s` is not a finite number of at least 0 (the manifest schema guarantees it).
    """
    if (
        isinstance(duration_s, bool)
        or not isinstance(duration_s, (int, float))
        or (isinstance(duration_s, float) and not math.isfinite(duration_s))
        or duration_s < 0
    ):
        raise ValueError("duration_s must be a finite number of seconds, at least 0")
    errors: list[Issue] = []
    for filename, entries, fields in (
        (CHAPTERS_FILE, chapters, ("start", "end")),
        (SLIDES_FILE, slides, ("t",)),
        (CUES_FILE, cues, ("t",)),
    ):
        for index, entry in enumerate(entries):
            for field in fields:
                value = entry[field]
                if value > duration_s:
                    location: Location = (index, field)
                    errors.append(
                        Issue(
                            code="time_beyond_duration",
                            rule=RULE,
                            message=messages.TIME_BEYOND_DURATION.format(
                                where=messages.lesson_file_where(filename, location),
                                value=value,
                                duration=duration_s,
                            ),
                            fix_hint=messages.TIME_BEYOND_DURATION_HINT,
                            location=location,
                        )
                    )
    return ValidationReport(errors=tuple(errors))
