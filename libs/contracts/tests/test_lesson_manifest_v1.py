"""B6 lesson manifest contract (PRD B6.2, B6.3): the JSON Schema and its example manifests.

AUTOMATED here (structure only, by contracts/lesson-manifest.v1.schema.json):
  * the schema is a valid Draft 2020-12 schema;
  * both example manifests validate (single-track; main, main-low, camera and screen), and so
    does the B6.3 example from the PRD;
  * a single-track lesson stays valid when camera and screen tracks are added (C4.7);
  * the nine required root fields (schema, course_slug, lesson_id, title, duration_s, tracks,
    captions, transcript, chapters), types, exactly one main track, at least one English
    caption (lang en, since B6.2 requires captions.en.vtt), track roles as open
    lowercase names (known: main, main-low, camera, screen; others such as audio accepted),
    slug and timestamp patterns, relative paths only (B6.3, C-08) on every path field, using
    the shared vectors in contracts/test-vectors/relative-path.v1.json, and that unknown fields
    are accepted (PRD B.0, EXT-02);
  * no Unicode control or format character in a path (guide decision): the complete
    Unicode 15.0.0 categories Cc and Cf, checked for every code point, at the edges and
    inside every range, next to every range, and on all eight path fields; private-use,
    surrogate and unassigned code points stay accepted. The expected sets come from Python's
    Unicode database, and a test fails if that is not version 15.0.0;
  * no percent sign (%) anywhere in a path (guide decision), so no percent-encoded form
    (%2e, %252e, %25%32%65 and so on), on all eight path fields; paths are never decoded.

NOT automated here, and therefore NOT claimed as enforced (the schema's $comment lists them):
  * that the files the manifest names, and poster.jpg (which has no manifest field), exist in
    the lesson folder;
  * that lesson.json is written last, only when every required file exists (FR-V-08);
  * that course_slug and lesson_id match the folder's place in the B6.1 path template;
  * the contents of the transcript file (B5.4 shape, owned by B5) and of the chapters, slides
    and cues files (B6.2), which have no schema yet;
  * that the pattern behaves the same in an ECMA-262 (JavaScript) validator: no JavaScript
    validator is part of the stack. The schema description says why it needs the u flag;
  * Windows reserved names and Unicode normalization: considered and not enforced in v1
    (guide decision), so there is nothing to test;
  * a maximum path length: none is specified in v1 (guide decision), because paths are built
    from bounded slugs and the store enforces its own limits;
  * that libs/media_paths uses the same Cc/Cf table: that library is not on main yet, and the
    comparison test belongs to it.

Each invalid case below must fail at the expected place with the expected schema keyword, so a
case cannot pass for the wrong reason.
"""

from __future__ import annotations

import copy
import json
import re
import unicodedata
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[3]
SCHEMA_PATH = ROOT / "contracts" / "lesson-manifest.v1.schema.json"
EXAMPLES = ROOT / "contracts" / "examples" / "lesson-manifest.v1"
# One top-level JSON file per example (guide decision); supporting files, if any, go in
# subfolders.
SINGLE_TRACK = EXAMPLES / "single-track.json"
CAMERA_SCREEN = EXAMPLES / "camera-screen.json"
PATH_VECTORS_PATH = ROOT / "contracts" / "test-vectors" / "relative-path.v1.json"

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


# --- paths (relative to the lesson folder only, PRD B6.3, C-08) ----------------------------

# One list of valid and invalid paths, shared with libs/media_paths so both enforce one rule.
PATH_VECTORS = load(PATH_VECTORS_PATH)
VALID_PATHS: list[str] = [v["path"] for v in PATH_VECTORS["valid"]]
BAD_PATHS: list[str] = [v["path"] for v in PATH_VECTORS["invalid"]]

# Guide decision for B6.3: the rules every relative path must follow.
PATH_RULES = {
    "empty",
    "backslash",
    "whitespace",
    "question-mark",
    "hash",
    "url-scheme",
    "drive-letter",
    "absolute",
    "empty-segment",
    "dot-segment",
    "dot-dot-segment",
    "control-character",
    "format-character",
    "percent-sign",
}

PATH_FIELDS: list[tuple[str, Loc]] = [
    ("track file", MAIN + ("file",)),
    ("caption file", CAPTION + ("file",)),
    ("transcript", ("transcript",)),
    ("chapters", ("chapters",)),
    ("slides", ("slides",)),
    ("cues", ("cues",)),
    ("summary", ("summary",)),
    # Not a file, but readers build the lesson folder's path from it (C-08).
    ("lesson_id", ("lesson_id",)),
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


@pytest.mark.parametrize(
    ("loc", "value"),
    [
        pytest.param(loc, value, id=f"{label} {value!r}")
        for label, loc in PATH_FIELDS
        for value in VALID_PATHS
    ],
)
def test_valid_relative_path_is_accepted(
    validator: Draft202012Validator, doc: Doc, loc: Loc, value: str
) -> None:
    set_at(loc, value)(doc)
    assert messages(validator, doc) == []


def _relative_path_refs(node: Any, at: tuple[str, ...] = ()) -> set[tuple[str, ...]]:
    """Schema locations whose value is {"$ref": "#/$defs/relative_path"}."""
    found: set[tuple[str, ...]] = set()
    if isinstance(node, dict):
        if node.get("$ref") == "#/$defs/relative_path":
            found.add(at)
        for key, child in node.items():
            found |= _relative_path_refs(child, at + (key,))
    return found


def _schema_location(schema: dict[str, Any], loc: Loc) -> tuple[str, ...]:
    """The schema location that describes the document value at loc, following local $refs."""
    at: tuple[str, ...] = ()
    node: Any = schema
    for key in loc:
        if "$ref" in node:
            name = node["$ref"].removeprefix("#/$defs/")
            at, node = ("$defs", name), schema["$defs"][name]
        if isinstance(key, int):
            at, node = at + ("items",), node["items"]
        else:
            at, node = at + ("properties", key), node["properties"][key]
    return at


def test_every_path_field_in_the_schema_is_tested(schema: dict[str, Any]) -> None:
    # A path field added to the schema later must also be added to PATH_FIELDS, and every
    # PATH_FIELDS entry must point at a real path field, so the two lists cannot drift apart.
    expected = {
        ("properties", "transcript"),
        ("properties", "chapters"),
        ("properties", "slides"),
        ("properties", "cues"),
        ("properties", "summary"),
        ("properties", "lesson_id"),
        ("$defs", "track", "properties", "file"),
        ("$defs", "caption", "properties", "file"),
    }
    tested = [_schema_location(schema, loc) for _, loc in PATH_FIELDS]
    assert _relative_path_refs(schema) == expected
    assert set(tested) == expected
    assert len(tested) == len(set(tested))  # no field listed twice


# lesson_id: the cases from the PR #32 review, plus the lesson_id forms B6.1 and B6.3 use.
@pytest.mark.parametrize(
    "value",
    [
        "../../etc",
        "../../etc/passwd",
        "/abs/x",
        "https://evil/x",
        "https://evil.example/x",
    ],
    ids=repr,
)
def test_lesson_id_that_is_not_a_relative_path_is_rejected(
    validator: Draft202012Validator, doc: Doc, value: str
) -> None:
    set_at(("lesson_id",), value)(doc)
    assert (("lesson_id",), "pattern") in error_keys(validator, doc)


@pytest.mark.parametrize(
    "value",
    [
        "01-setup/02-install-python",
        "02-first-assistant/01-call-a-model",
        "live-2026a/03-rag-basics",
        "01-intro",
    ],
    ids=repr,
)
def test_lesson_id_that_is_a_lesson_slug_path_is_accepted(
    validator: Draft202012Validator, doc: Doc, value: str
) -> None:
    set_at(("lesson_id",), value)(doc)
    assert messages(validator, doc) == []


def test_path_vectors_cover_every_rule() -> None:
    used = {rule for v in PATH_VECTORS["invalid"] for rule in v["rules"]}
    assert used == PATH_RULES
    assert all(v["rules"] for v in PATH_VECTORS["invalid"])


# Guide decision: no '%' anywhere in a path. The 'none' signer (B6.4) appends the path to a
# base URL and layers may decode it once or more, so any encoded form could become a dot
# or separator. The path itself is never decoded.
PERCENT_FORMS = [
    *("%", "%%", "%2e", "%2E", "%2f", "%2F", "%5c", "%5C"),
    *("%252e", "%25252e", "%25%32%65", "%20", "%25", "%41", "100%"),
]
PERCENT_PLACES = [
    "{}",
    "{}.mp4",
    "a{}b.mp4",
    "{}/720p.mp4",
    "a/{}/b.mp4",
    "a/b/{}",
    "a/b{}",
]


@pytest.mark.parametrize(
    "value", [place.format(f) for f in PERCENT_FORMS for place in PERCENT_PLACES]
)
def test_percent_sign_is_rejected_in_every_segment(
    validator: Draft202012Validator, doc: Doc, value: str
) -> None:
    for _label, loc in PATH_FIELDS:
        attempt = copy.deepcopy(doc)
        set_at(loc, value)(attempt)
        assert (loc, "pattern") in error_keys(validator, attempt), (loc, value)


def test_every_path_vector_with_a_percent_sign_is_invalid() -> None:
    assert not [p for p in VALID_PATHS if "%" in p]
    assert all(
        "percent-sign" in v["rules"]
        for v in PATH_VECTORS["invalid"]
        if "%" in v["path"]
    )


def test_path_vectors_have_no_duplicates() -> None:
    every = VALID_PATHS + BAD_PATHS
    assert len(every) == len(set(every))


# --- paths: Unicode Cc and Cf (guide decision, PRD B6.3) -----------------------------------
#
# The schema rejects the complete Unicode 15.0.0 categories Cc and Cf. The expected sets
# are taken from Python's Unicode database, which is 15.0.0 in Python 3.12; the first test
# fails if it is not, because the schema's list is pinned and must not follow Python.

UNICODE_VERSION = "15.0.0"
CONTROL_AND_FORMAT = ("Cc", "Cf")


def _code_points_in(categories: tuple[str, ...]) -> list[int]:
    return [p for p in range(0x110000) if unicodedata.category(chr(p)) in categories]


def _ranges(code_points: list[int]) -> list[tuple[int, int]]:
    ranges: list[tuple[int, int]] = []
    for p in code_points:
        if ranges and ranges[-1][1] == p - 1:
            ranges[-1] = (ranges[-1][0], p)
        else:
            ranges.append((p, p))
    return ranges


FORBIDDEN = set(_code_points_in(CONTROL_AND_FORMAT))
FORBIDDEN_RANGES = _ranges(sorted(FORBIDDEN))


def _name(code_point: int) -> str:
    return f"U+{code_point:04X}"


@pytest.fixture(scope="module")
def path_validator(schema: dict[str, Any]) -> Draft202012Validator:
    """A validator for $defs/relative_path alone, the definition all eight fields share."""
    return Draft202012Validator(schema["$defs"]["relative_path"])


def test_python_unicode_database_is_the_pinned_version() -> None:
    assert unicodedata.unidata_version == UNICODE_VERSION, (
        f"This Python uses Unicode {unicodedata.unidata_version}; the B6.3 relative-path "
        f"rule is pinned to Unicode {UNICODE_VERSION}. A new Unicode version needs a "
        "reviewed contract decision (PRD B.0) for the schema and libs/media_paths together."
    )


def test_unicode_15_0_has_2_cc_and_21_cf_ranges() -> None:
    # UCD 15.0.0 DerivedGeneralCategory.txt: Cc 65 code points, Cf 170.
    cc, cf = (_code_points_in((c,)) for c in CONTROL_AND_FORMAT)
    assert (len(_ranges(cc)), len(cc), len(_ranges(cf)), len(cf)) == (2, 65, 21, 170)


def test_schema_rejects_exactly_cc_and_cf_among_all_code_points(
    schema: dict[str, Any],
) -> None:
    # Every code point, inside a name, through the schema's own pattern (jsonschema checks
    # "pattern" with re.search, as here). Whitespace and the ASCII rules reject a few
    # more; nothing else may differ.
    pattern = re.compile(schema["$defs"]["relative_path"]["pattern"])
    whitespace = {p for p in range(0x110000) if re.fullmatch(r"\s", chr(p))}
    rejected = FORBIDDEN | whitespace | {ord(c) for c in ":\\?#%"}
    wrong = [
        _name(p)
        for p in range(0x110000)
        if (pattern.search(f"a{chr(p)}.mp4") is None) != (p in rejected)
    ]
    assert wrong == []


# First, middle and last code point of every range.
INSIDE = sorted(
    {p for start, end in FORBIDDEN_RANGES for p in (start, (start + end) // 2, end)}
)
# Just before and just after every range, unless whitespace (for example U+0020 after
# the C0 controls), which the whitespace rule rejects.
OUTSIDE = sorted(
    {
        p
        for start, end in FORBIDDEN_RANGES
        for p in (start - 1, end + 1)
        if p >= 0 and p not in FORBIDDEN and not re.fullmatch(r"\s", chr(p))
    }
)


@pytest.mark.parametrize("code_point", INSIDE, ids=_name)
def test_every_cc_and_cf_range_is_rejected_at_its_edges_and_inside(
    path_validator: Draft202012Validator, code_point: int
) -> None:
    for path in (
        f"a{chr(code_point)}.mp4",
        f"{chr(code_point)}a/b",
        f"a/b{chr(code_point)}",
    ):
        assert ((), "pattern") in error_keys(path_validator, path)


@pytest.mark.parametrize("code_point", OUTSIDE, ids=_name)
def test_code_point_next_to_a_cc_or_cf_range_is_accepted(
    path_validator: Draft202012Validator, code_point: int
) -> None:
    assert messages(path_validator, f"a{chr(code_point)}.mp4") == []


@pytest.mark.parametrize(
    "path",
    [
        "a\ue000.mp4",  # Co: private use
        "a\U000f0000.mp4",  # Co: supplementary private use
        "a\ud800.mp4",  # Cs: lone high surrogate
        "a\udfff.mp4",  # Cs: lone low surrogate
        "a\uffff.mp4",  # Cn: a noncharacter
        "a\u2065.mp4",  # Cn: unassigned, between two Cf ranges
        "a\U0001f600.mp4",  # So: an emoji outside the BMP
        "a\U00011083.mp4",  # Lo: Kaithi letter, same high surrogate as U+110BD
    ],
    ids=repr,
)
def test_private_use_surrogate_and_unassigned_are_not_rejected_by_category(
    path_validator: Draft202012Validator, path: str
) -> None:
    # Guide decision: only Cc and Cf are rejected as categories.
    assert messages(path_validator, path) == []


@pytest.mark.parametrize(
    "char",
    [
        "\x00",
        "\x7f",
        "\x9f",
        "\u00ad",
        "\u061c",
        "\u202e",
        "\u2066",
        "\ufeff",
        "\U000e0001",
    ],
    ids=lambda c: _name(ord(c)),
)
@pytest.mark.parametrize(("label", "loc"), PATH_FIELDS, ids=[f for f, _ in PATH_FIELDS])
def test_every_path_field_rejects_control_and_format_characters(
    validator: Draft202012Validator, doc: Doc, label: str, loc: Loc, char: str
) -> None:
    set_at(loc, f"720p{char}.mp4" if label != "lesson_id" else f"01-setup{char}")(doc)
    assert (loc, "pattern") in error_keys(validator, doc)


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


# --- English caption: B6.2 requires captions.en.vtt, so v1 needs one caption with lang en ---


HINDI_CAPTION = {"lang": "hi", "file": "captions.hi.vtt"}
ENGLISH_CAPTION = {"lang": "en", "file": "captions.en.vtt"}


# lang must be exactly "en": other spellings and region tags do not count as the English caption.
@pytest.mark.parametrize("lang", ["hi", "EN", "en-US"], ids=repr)
def test_captions_without_english_are_rejected(
    validator: Draft202012Validator, doc: Doc, lang: str
) -> None:
    doc["captions"] = [{"lang": lang, "file": f"captions.{lang}.vtt"}]
    assert (("captions",), "contains") in error_keys(validator, doc)


@pytest.mark.parametrize(
    "captions",
    [
        pytest.param([ENGLISH_CAPTION], id="english only"),
        pytest.param([HINDI_CAPTION, ENGLISH_CAPTION], id="hindi then english"),
    ],
)
def test_captions_with_english_are_accepted(
    validator: Draft202012Validator, doc: Doc, captions: list[dict[str, str]]
) -> None:
    doc["captions"] = copy.deepcopy(captions)
    assert messages(validator, doc) == []


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
