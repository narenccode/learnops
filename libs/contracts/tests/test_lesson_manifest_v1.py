"""B6 lesson manifest contract (PRD B6.2, B6.3): the JSON Schema and its example manifests.

AUTOMATED here (structure only, by contracts/lesson-manifest.v1.schema.json):
  * the schema is a valid Draft 2020-12 schema;
  * both example manifests validate (single-track; main, main-low, camera and screen), and so
    does the B6.3 example from the PRD;
  * a single-track lesson stays valid when camera and screen tracks are added (C4.7);
  * the nine required root fields (schema, course_slug, lesson_id, title, duration_s, tracks,
    captions, transcript, chapters), types, exactly one main track, track roles as open
    lowercase names (known: main, main-low, camera, screen; others such as audio accepted),
    slug and timestamp patterns, relative paths only (B6.3, C-08), and that unknown fields are
    accepted (PRD B.0, EXT-02).

NOT automated here, and therefore NOT claimed as enforced (the schema's $comment lists them):
  * that the files the manifest names, and poster.jpg (which has no manifest field), exist in
    the lesson folder;
  * that lesson.json is written last, only when every required file exists (FR-V-08);
  * that course_slug and lesson_id match the folder's place in the B6.1 path template;
  * the contents of the transcript file (B5.4 shape, owned by B5) and of the chapters, slides
    and cues files (B6.2), which have no schema yet.

Each invalid case below must fail at the expected place with the expected schema keyword, so a
case cannot pass for the wrong reason.
"""

from __future__ import annotations

import copy
import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[3]
SCHEMA_PATH = ROOT / "contracts" / "lesson-manifest.v1.schema.json"
EXAMPLES = ROOT / "contracts" / "examples" / "lesson-manifest.v1"
SINGLE_TRACK = EXAMPLES / "single-track" / "lesson.json"
CAMERA_SCREEN = EXAMPLES / "camera-screen" / "lesson.json"

# The example in PRD B6.3, with its "…" timestamp replaced by a real one.
PRD_EXAMPLE: dict[str, Any] = {
    "schema": "learnops.lesson/v1",
    "course_slug": "build-ai-assistant",
    "lesson_id": "01-setup/02-install-python",
    "title": "Install Python",
    "duration_s": 742,
    "tracks": [
        {"role": "main", "file": "720p.mp4", "height": 720},
        {"role": "main-low", "file": "360p.mp4", "height": 360},
    ],
    "captions": [{"lang": "en", "file": "captions.en.vtt"}],
    "transcript": "transcript.en.json",
    "chapters": "chapters.json",
    "slides": "slides.json",
    "cues": "cues.json",
    "summary": "summary.en.md",
    "source": {
        "kind": "upload",
        "uploaded_by": "<lti sub>",
        "original_name": "lecture2.mov",
    },
    "processing": {"pipeline_version": "1.0.0", "completed_at": "2026-01-12T09:30:00Z"},
}

Doc = dict[str, Any]
Loc = tuple[str | int, ...]
Edit = Callable[[Doc], None]

# Places in the single-track example.
MAIN: Loc = ("tracks", 0)
CAPTION: Loc = ("captions", 0)
SOURCE: Loc = ("source",)
PROCESSING: Loc = ("processing",)
COMPLETED_AT: Loc = PROCESSING + ("completed_at",)
NEW_TRACK: Loc = ("tracks", 1)  # appended by add_track()

# Guide decision for B6.3: these root fields are required; every other root field is optional.
REQUIRED_ROOT = (
    "schema",
    "course_slug",
    "lesson_id",
    "title",
    "duration_s",
    "tracks",
    "captions",
    "transcript",
    "chapters",
)


# --- helpers -------------------------------------------------------------------------------


def _parent(doc: Doc, loc: Loc) -> Any:
    node: Any = doc
    for key in loc[:-1]:
        node = node[key]
    return node


def set_at(loc: Loc, value: Any) -> Edit:
    def edit(doc: Doc) -> None:
        _parent(doc, loc)[loc[-1]] = value

    return edit


def drop_at(loc: Loc) -> Edit:
    def edit(doc: Doc) -> None:
        del _parent(doc, loc)[loc[-1]]

    return edit


def keep_only(*keys: str) -> Edit:
    def edit(doc: Doc) -> None:
        for key in set(doc) - set(keys):
            del doc[key]

    return edit


def add_track(**fields: Any) -> Edit:
    def edit(doc: Doc) -> None:
        doc["tracks"].append(fields)

    return edit


def error_keys(validator: Draft202012Validator, instance: Any) -> set[tuple[Loc, str]]:
    """(where, which schema keyword) for every error, so a test can name the exact failure."""
    return {
        (tuple(e.absolute_path), str(e.validator))
        for e in validator.iter_errors(instance)
    }


def messages(validator: Draft202012Validator, instance: Any) -> list[str]:
    return [e.message for e in validator.iter_errors(instance)]


@dataclass(frozen=True)
class Case:
    name: str
    edit: Edit
    at: Loc
    keyword: str


def bad(name: str, loc: Loc, value: Any, keyword: str) -> Case:
    """Replace the value at loc; the schema must reject it at loc with keyword."""
    return Case(name, set_at(loc, value), loc, keyword)


def missing(name: str, loc: Loc) -> Case:
    """Remove the field at loc; the schema must report it as required on its parent."""
    return Case(name, drop_at(loc), loc[:-1], "required")


def params(cases: list[Case]) -> list[Any]:
    return [pytest.param(c, id=c.name) for c in cases]


def load(path: Path) -> Doc:
    loaded: Doc = json.loads(path.read_text(encoding="utf-8"))
    return loaded


# --- fixtures ------------------------------------------------------------------------------


@pytest.fixture(scope="module")
def schema() -> dict[str, Any]:
    return load(SCHEMA_PATH)


@pytest.fixture(scope="module")
def validator(schema: dict[str, Any]) -> Draft202012Validator:
    # Same set-up as the B1 tests. "date-time" is checked only if rfc3339-validator is installed.
    return Draft202012Validator(schema, format_checker=FormatChecker())


@pytest.fixture
def doc() -> Doc:
    return load(SINGLE_TRACK)


# --- the schema and the examples -----------------------------------------------------------


def test_schema_is_a_valid_draft_2020_12_schema(schema: dict[str, Any]) -> None:
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    Draft202012Validator.check_schema(schema)


@pytest.mark.parametrize(
    "path", [SINGLE_TRACK, CAMERA_SCREEN], ids=["single-track", "camera-screen"]
)
def test_example_manifest_is_valid(validator: Draft202012Validator, path: Path) -> None:
    assert messages(validator, load(path)) == []


def test_prd_example_is_valid(validator: Draft202012Validator) -> None:
    assert messages(validator, copy.deepcopy(PRD_EXAMPLE)) == []


KNOWN_ROLES = {"main", "main-low", "camera", "screen"}


def test_examples_use_every_known_track_role() -> None:
    # The role list is open, so this checks the examples cover the roles B6.2/B6.3 name.
    used = {t["role"] for p in (SINGLE_TRACK, CAMERA_SCREEN) for t in load(p)["tracks"]}
    assert used == KNOWN_ROLES


@pytest.mark.parametrize("role", sorted(KNOWN_ROLES - {"main"}) + ["audio", "camera2"])
def test_added_track_with_known_or_new_lowercase_role_is_accepted(
    validator: Draft202012Validator, doc: Doc, role: str
) -> None:
    add_track(role=role, file=f"{role}.mp4")(doc)
    assert messages(validator, doc) == []


def test_single_track_lesson_stays_valid_with_camera_and_screen_added(
    validator: Draft202012Validator, doc: Doc
) -> None:
    # PRD C4.7: existing single-track lessons remain valid when camera/screen are added later.
    assert [t["role"] for t in doc["tracks"]] == ["main"]
    doc["tracks"] += [
        {"role": "camera", "file": "camera.mp4"},
        {"role": "screen", "file": "screen.mp4"},
    ]
    assert messages(validator, doc) == []


# --- invalid: required fields --------------------------------------------------------------


def test_schema_requires_exactly_the_nine_root_fields(schema: dict[str, Any]) -> None:
    assert sorted(schema["required"]) == sorted(REQUIRED_ROOT)


MISSING = [
    missing("root without schema", ("schema",)),
    missing("root without course_slug", ("course_slug",)),
    missing("root without lesson_id", ("lesson_id",)),
    missing("root without title", ("title",)),
    missing("root without duration_s", ("duration_s",)),
    missing("root without tracks", ("tracks",)),
    missing("root without captions", ("captions",)),
    missing("root without transcript", ("transcript",)),
    missing("root without chapters", ("chapters",)),
    missing("track without role", MAIN + ("role",)),
    missing("track without file", MAIN + ("file",)),
    missing("caption without lang", CAPTION + ("lang",)),
    missing("caption without file", CAPTION + ("file",)),
    missing("source without kind", SOURCE + ("kind",)),
]


@pytest.mark.parametrize("case", params(MISSING))
def test_missing_required_field_is_rejected(
    validator: Draft202012Validator, doc: Doc, case: Case
) -> None:
    case.edit(doc)
    assert (case.at, case.keyword) in error_keys(validator, doc)


# --- invalid: tracks -----------------------------------------------------------------------

TRACK_CASES = [
    bad("no tracks", ("tracks",), [], "minItems"),
    bad(
        "only a camera and a screen track",
        ("tracks",),
        [
            {"role": "camera", "file": "camera.mp4"},
            {"role": "screen", "file": "screen.mp4"},
        ],
        "contains",
    ),
    bad(
        "only a main-low track",
        ("tracks",),
        [{"role": "main-low", "file": "360p.mp4", "height": 360}],
        "contains",
    ),
    Case(
        "two main tracks",
        add_track(role="main", file="b.mp4"),
        ("tracks",),
        "maxContains",
    ),
    bad("main role has wrong case", MAIN + ("role",), "Main", "pattern"),
    *[
        Case(
            f"added track role {role!r}",
            add_track(role=role, file="x.mp4"),
            NEW_TRACK + ("role",),
            keyword,
        )
        for role, keyword in [
            ("Audio", "pattern"),
            ("main_low", "pattern"),
            ("camera-", "pattern"),
            ("", "pattern"),
            ("audio\n", "pattern"),
            (1, "type"),
        ]
    ],
    bad("height is a string", MAIN + ("height",), "720", "type"),
    bad("height is fractional", MAIN + ("height",), 720.5, "type"),
    bad("height is boolean", MAIN + ("height",), True, "type"),
    bad("height is zero", MAIN + ("height",), 0, "minimum"),
    bad("track is a string", MAIN, "720p.mp4", "type"),
    bad("tracks is an object", ("tracks",), {}, "type"),
]


@pytest.mark.parametrize("case", params(TRACK_CASES))
def test_invalid_track_is_rejected(
    validator: Draft202012Validator, doc: Doc, case: Case
) -> None:
    case.edit(doc)
    assert (case.at, case.keyword) in error_keys(validator, doc)


# --- invalid: paths (relative to the lesson folder only, PRD B6.3, C-08) -------------------

BAD_PATHS = [
    "../720p.mp4",
    "slides/../../x.jpg",
    "..",
    "/media/courses/x/720p.mp4",
    "https://media.example.org/courses/x/720p.mp4",
    "http://example.org/720p.mp4",
    "s3://bucket/720p.mp4",
    "file:///720p.mp4",
    "C:\\media\\720p.mp4",
    "slides\\001.jpg",
    "",
    "720p.mp4\n",
    "720p\n.mp4",
]
PATH_FIELDS: list[tuple[str, Loc]] = [
    ("track file", MAIN + ("file",)),
    ("caption file", CAPTION + ("file",)),
    ("transcript", ("transcript",)),
    ("chapters", ("chapters",)),
    ("slides", ("slides",)),
    ("cues", ("cues",)),
    ("summary", ("summary",)),
]
PATH_CASES = [
    bad(f"{label} {value!r}", loc, value, "pattern")
    for label, loc in PATH_FIELDS
    for value in BAD_PATHS
]
PATH_CASES += [
    bad(f"{label} is a number", loc, 5, "type") for label, loc in PATH_FIELDS
]


@pytest.mark.parametrize("case", params(PATH_CASES))
def test_path_that_is_not_relative_is_rejected(
    validator: Draft202012Validator, doc: Doc, case: Case
) -> None:
    case.edit(doc)
    assert (case.at, case.keyword) in error_keys(validator, doc)


# --- invalid: course_slug ------------------------------------------------------------------

BAD_SLUGS = [
    "Build-AI",
    "build_ai",
    "build ai",
    "build--ai",
    "-build",
    "build-",
    "é",
    "",
]
BAD_SLUGS += ["build-ai\n"]
SLUG_CASES = [
    bad(f"course_slug {v!r}", ("course_slug",), v, "pattern") for v in BAD_SLUGS
]


@pytest.mark.parametrize("case", params(SLUG_CASES))
def test_invalid_course_slug_is_rejected(
    validator: Draft202012Validator, doc: Doc, case: Case
) -> None:
    case.edit(doc)
    assert (case.at, case.keyword) in error_keys(validator, doc)


# --- invalid: processing.completed_at ------------------------------------------------------

# Calendar validity (for example 2026-02-31) is not tested here: jsonschema checks
# "date-time" only when rfc3339-validator is installed, and CI does not install it.
TIMESTAMP_CASES = [
    bad("month 13", COMPLETED_AT, "2026-13-01T10:00:00Z", "pattern"),
    bad("day 32", COMPLETED_AT, "2026-01-32T10:00:00Z", "pattern"),
    bad("hour 25", COMPLETED_AT, "2026-01-12T25:00:00Z", "pattern"),
    bad("minute 61", COMPLETED_AT, "2026-01-12T10:61:00Z", "pattern"),
    bad("no time zone", COMPLETED_AT, "2026-01-12T10:00:00", "pattern"),
    bad("date only", COMPLETED_AT, "2026-01-12", "pattern"),
    bad("space instead of T", COMPLETED_AT, "2026-01-12 10:00:00Z", "pattern"),
    bad("placeholder from the PRD", COMPLETED_AT, "…", "pattern"),
    bad("trailing newline", COMPLETED_AT, "2026-01-12T10:00:00Z\n", "pattern"),
    bad("empty string", COMPLETED_AT, "", "pattern"),
    bad("number", COMPLETED_AT, 1768210200, "type"),
]


@pytest.mark.parametrize("case", params(TIMESTAMP_CASES))
def test_invalid_completed_at_is_rejected(
    validator: Draft202012Validator, doc: Doc, case: Case
) -> None:
    case.edit(doc)
    assert (case.at, case.keyword) in error_keys(validator, doc)


# --- invalid: wrong types, values, sizes ---------------------------------------------------

TYPE_CASES = [
    bad("schema is another version", ("schema",), "learnops.lesson/v2", "const"),
    bad("schema is the course contract", ("schema",), "learnops.course/v1", "const"),
    bad("schema has trailing space", ("schema",), "learnops.lesson/v1 ", "const"),
    bad("schema is a number", ("schema",), 1, "const"),
    bad("lesson_id is empty", ("lesson_id",), "", "minLength"),
    bad("lesson_id is a number", ("lesson_id",), 2, "type"),
    bad("title is empty", ("title",), "", "minLength"),
    bad("title is a number", ("title",), 5, "type"),
    bad("duration_s is a string", ("duration_s",), "742", "type"),
    bad("duration_s is boolean", ("duration_s",), True, "type"),
    bad("duration_s is negative", ("duration_s",), -1, "minimum"),
    bad("captions is empty", ("captions",), [], "minItems"),
    bad("captions is a string", ("captions",), "captions.en.vtt", "type"),
    bad("caption lang is empty", CAPTION + ("lang",), "", "minLength"),
    bad("caption lang is a number", CAPTION + ("lang",), 1, "type"),
    bad("source is a string", SOURCE, "upload", "type"),
    bad("source kind is empty", SOURCE + ("kind",), "", "minLength"),
    bad("source kind is a number", SOURCE + ("kind",), 1, "type"),
    bad("uploaded_by is empty", SOURCE + ("uploaded_by",), "", "minLength"),
    bad("uploaded_by is a number", SOURCE + ("uploaded_by",), 1, "type"),
    bad("original_name is empty", SOURCE + ("original_name",), "", "minLength"),
    bad("processing is a list", PROCESSING, [], "type"),
    bad(
        "pipeline_version is empty",
        PROCESSING + ("pipeline_version",),
        "",
        "minLength",
    ),
    bad(
        "pipeline_version is a number",
        PROCESSING + ("pipeline_version",),
        1.0,
        "type",
    ),
]


@pytest.mark.parametrize("case", params(TYPE_CASES))
def test_wrong_type_or_value_is_rejected(
    validator: Draft202012Validator, doc: Doc, case: Case
) -> None:
    case.edit(doc)
    assert (case.at, case.keyword) in error_keys(validator, doc)


@pytest.mark.parametrize("value", [[], "learnops.lesson/v1", None, 1], ids=repr)
def test_document_that_is_not_an_object_is_rejected(
    validator: Draft202012Validator, value: Any
) -> None:
    assert ((), "type") in error_keys(validator, value)


# --- valid variations: the schema must NOT reject these ------------------------------------


@dataclass(frozen=True)
class Accepted:
    name: str
    edit: Edit


ACCEPTED = [
    Accepted("unknown field at root", set_at(("future_root",), 1)),
    Accepted("unknown field in track", set_at(MAIN + ("future",), {"a": 1})),
    Accepted("unknown field in caption", set_at(CAPTION + ("future",), [1])),
    Accepted("unknown field in source", set_at(SOURCE + ("future",), "x")),
    Accepted("unknown field in processing", set_at(PROCESSING + ("future",), True)),
    Accepted("no source", drop_at(SOURCE)),
    Accepted("no processing", drop_at(PROCESSING)),
    Accepted("empty processing", set_at(PROCESSING, {})),
    Accepted("source with kind only", set_at(SOURCE, {"kind": "upload"})),
    # FR-V-09 intake is a second source; the PRD does not name its kind value.
    Accepted("source kind other than upload", set_at(SOURCE + ("kind",), "bbb")),
    Accepted("track without height", drop_at(MAIN + ("height",))),
    Accepted("fractional duration_s", set_at(("duration_s",), 742.25)),
    Accepted("zero duration_s", set_at(("duration_s",), 0)),
    Accepted(
        "main-low track added", add_track(role="main-low", file="360p.mp4", height=360)
    ),
    Accepted(
        "main track not listed first",
        lambda d: d["tracks"].insert(0, {"role": "main-low", "file": "360p.mp4"}),
    ),
    Accepted("only the nine required fields", keep_only(*REQUIRED_ROOT)),
    Accepted(
        "second caption language",
        lambda d: d["captions"].append({"lang": "hi", "file": "captions.hi.vtt"}),
    ),
    Accepted(
        "live-class lesson_id", set_at(("lesson_id",), "live-2026a/03-rag-basics")
    ),
    Accepted("path in a subfolder", set_at(("slides",), "slides/index.json")),
    Accepted("path with '..' inside a name", set_at(("chapters",), "a/..b/c.json")),
    Accepted("timestamp with fraction", set_at(COMPLETED_AT, "2026-01-12T10:00:00.5Z")),
    Accepted(
        "timestamp with offset", set_at(COMPLETED_AT, "2026-01-12T10:00:00-03:00")
    ),
    Accepted("non-ASCII title", set_at(("title",), "Python installieren — é")),
]


@pytest.mark.parametrize("case", [pytest.param(a, id=a.name) for a in ACCEPTED])
def test_valid_variation_is_accepted(
    validator: Draft202012Validator, doc: Doc, case: Accepted
) -> None:
    case.edit(doc)
    assert messages(validator, doc) == []
