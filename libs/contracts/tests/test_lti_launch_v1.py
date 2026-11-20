"""B3 LTI launch contract (PRD B3): the JSON Schema for the normalised launch result.

AUTOMATED here (structure only, by contracts/lti-launch.v1.schema.json):
  * the schema is a valid Draft 2020-12 schema;
  * every file in contracts/examples/lti-launch.v1/ validates, and the folder holds valid
    examples only (invalid cases live in this file, never in that folder);
  * the required fields (at every depth), the message type, the two role values, non-empty
    strings, nullable optionals, that context.id is a positive integer in ASCII digits (contract
    section 3.1), and that unknown fields are accepted (PRD B.0, EXT-02);
  * the optional-claim rules of contract section 3.2, through the shared vectors in
    contracts/test-vectors/lti-launch-optional-claims.v1.json: the vectors cover every row of
    the rule, agree with it (Unicode 15.0.0 White_Space, not Python's str.isspace()), and every
    expected result is schema-valid.

  * the role rules of contract section 5 (OI-22) and the session identity and course-link key
    of sections 6 and 7 (OI-21): each is restated at the end of this file (_resolve_role,
    _session_identity, _course_link_key) and checked against the contract table, the PRD text and
    a list of decided cases. Like _rule_outcome below, this restates the rule to pin the contract
    text. It is not the gateway: libs/lti must enforce the same rules when it exists.

NOT implemented anywhere yet: the normaliser itself. It is to run once, in libs/lti, which does
not exist yet; libs/lti must pass the same vectors when it is added. The rule is restated in this file
(_rule_outcome) only to check the vectors against the contract text.

These are the shared contract tests that cover B3 in Release 0 (PRD B.0 rule 3): a consuming
module adds its own tests when its code that reads the contract exists.

NOT checked by the schema, and not tested as running code here (the schema's $comment lists
them): signature, exp, aud, azp, iss, deployment, nonce and state checks, role-URI mapping and
precedence, session binding and expiry, course isolation. They belong to libs/lti, which does
not exist yet. Role mapping and the identity keys are pinned only as stated rules (see above);
signature, expiry, nonce, state, session expiry and isolation are not covered at all.

Each invalid case must fail at the expected place with the expected schema keyword, so a case
cannot pass for the wrong reason. For a dropped required field a separate test also checks that
the error names that field.
"""

from __future__ import annotations

import copy
import itertools
import json
import re
import unicodedata
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[3]
SCHEMA_PATH = ROOT / "contracts" / "lti-launch.v1.schema.json"
EXAMPLE_DIR = ROOT / "contracts" / "examples" / "lti-launch.v1"

CONTRACT_PATH = ROOT / "contracts" / "lti-launch.v1.md"
CLAIM_VECTORS_PATH = (
    ROOT / "contracts" / "test-vectors" / "lti-launch-optional-claims.v1.json"
)

Doc = dict[str, Any]

# The optional claims of contract section 3.2, as paths in the normalised result.
OPTIONAL_CLAIMS: list[tuple[str, ...]] = [("name",), ("email",), ("context", "title")]

# Unicode 15.0.0 White_Space (PropList.txt): 25 code points. Written out here as well as in the
# vectors file, so that an edit to one of them alone fails a test.
WHITE_SPACE_15_0 = frozenset(
    [*range(0x09, 0x0E), 0x20, 0x85, 0xA0, 0x1680, *range(0x2000, 0x200B)]
    + [0x2028, 0x2029, 0x202F, 0x205F, 0x3000]
)
# str.isspace() is True for these, but they are not White_Space: a string of them is kept.
ISSPACE_BUT_NOT_WHITE_SPACE = frozenset(range(0x1C, 0x20))

# Invisible characters are built with chr() so that they are visible in this file.
NBSP = chr(0xA0)  # no-break space
LINE_SEPARATOR = chr(0x2028)


def _schema() -> dict[str, Any]:
    loaded: dict[str, Any] = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    return loaded


def _validator() -> Draft202012Validator:
    # No format checker: the schema has no "format" keyword, so it would check nothing.
    return Draft202012Validator(_schema())


def _example_files() -> list[Path]:
    return sorted(EXAMPLE_DIR.glob("*.json"))


@pytest.fixture
def mentor_doc() -> Doc:
    """A fresh copy of the Mentor example, safe to edit."""
    loaded: Doc = json.loads(
        (EXAMPLE_DIR / "instructor-mentor.json").read_text("utf-8")
    )
    return copy.deepcopy(loaded)


def test_schema_is_valid_draft_2020_12() -> None:
    schema = _schema()
    Draft202012Validator.check_schema(schema)
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["$id"] == "urn:learnops:contract:lti-launch:v1"


def test_examples_folder_has_the_required_examples() -> None:
    names = {p.name for p in _example_files()}
    assert {"instructor-mentor.json", "institution-administrator.json"} <= names


def test_examples_folder_holds_json_files_only() -> None:
    """CI validates every file there as valid, so nothing else may be in it."""
    assert [p for p in EXAMPLE_DIR.iterdir() if p.suffix != ".json"] == []


@pytest.mark.parametrize("path", _example_files(), ids=lambda p: p.name)
def test_every_example_is_valid(path: Path) -> None:
    errors = list(_validator().iter_errors(json.loads(path.read_text("utf-8"))))
    assert errors == [], [e.message for e in errors]


def test_unknown_fields_are_accepted(mentor_doc: Doc) -> None:
    mentor_doc["future_optional_field"] = "ignored by readers"
    mentor_doc["context"]["future_nested_field"] = 1
    assert _validator().is_valid(mentor_doc)


def test_optional_fields_may_be_absent_or_null(mentor_doc: Doc) -> None:
    for key in ("name", "email"):
        mentor_doc[key] = None
    del mentor_doc["context"]["title"]
    assert _validator().is_valid(mentor_doc)
    del mentor_doc["name"]
    del mentor_doc["email"]
    assert _validator().is_valid(mentor_doc)


@pytest.mark.parametrize("key", ["name", "email"])
def test_name_and_email_are_valid_when_null(mentor_doc: Doc, key: str) -> None:
    """The schema accepts null for name and email. When libs/lti produces null is in the
    shared vectors (contract section 3.2), checked further down."""
    mentor_doc[key] = None
    assert _validator().is_valid(mentor_doc)


@pytest.mark.parametrize("key", ["name", "email"])
def test_name_and_email_are_valid_when_absent(mentor_doc: Doc, key: str) -> None:
    del mentor_doc[key]
    assert _validator().is_valid(mentor_doc)


def test_context_title_is_valid_when_omitted(mentor_doc: Doc) -> None:
    """The schema accepts a result without context.title. When libs/lti omits it is in the
    shared vectors (contract section 3.2), checked below."""
    del mentor_doc["context"]["title"]
    assert _validator().is_valid(mentor_doc)


# Contract section 3.2: optional claims, through the shared vectors.

SECTION_3_2_RULES = {
    "absent",
    "null",
    "empty",
    "white-space-only",
    "not-a-string",
    "other-string",
}


def _claim_vectors_file() -> dict[str, Any]:
    loaded: dict[str, Any] = json.loads(CLAIM_VECTORS_PATH.read_text(encoding="utf-8"))
    return loaded


def _claim_vectors() -> list[dict[str, Any]]:
    vectors: list[dict[str, Any]] = _claim_vectors_file()["vectors"]
    return vectors


def _is_white_space_only(text: str) -> bool:
    """Contract section 3.2: no character except Unicode White_Space. Deliberately not
    str.isspace() or str.strip(), which also treat U+001C to U+001F as white space. An empty
    string is handled before this is called."""
    return all(ord(char) in WHITE_SPACE_15_0 for char in text)


def _rule_outcome(claim_input: dict[str, Any]) -> str:
    """The section 3.2 rule restated, to check the vectors against the contract text. It is
    not a normaliser: that runs once, in libs/lti (not yet created)."""
    if claim_input.get("absent") is True:
        return "absent"
    value = claim_input["value"]
    if not isinstance(value, str) or value == "" or _is_white_space_only(value):
        return "absent"
    return "preserved"


def _expected_result(doc: Doc, path: tuple[str, ...], vector: dict[str, Any]) -> Doc:
    """The normalised result that section 3.2 requires for this claim and vector."""
    target = doc
    for key in path[:-1]:
        target = target[key]
    if vector["expected"] == "preserved":
        target[path[-1]] = vector["input"]["value"]
    elif path == ("context", "title"):
        target.pop(path[-1], None)  # omitted, never null
    else:
        target[path[-1]] = None
    return doc


def test_optional_claim_vectors_file_is_ascii() -> None:
    """Keep Unicode test values JSON-escaped so the vectors file itself is ASCII."""
    assert CLAIM_VECTORS_PATH.read_bytes().isascii()


def test_python_unicode_database_is_unicode_15_0() -> None:
    """The White_Space set below is pinned to Unicode 15.0.0, the version CI uses."""
    assert unicodedata.unidata_version == "15.0.0"
    assert _claim_vectors_file()["unicode_version"] == "15.0.0"


def test_vectors_file_lists_exactly_unicode_white_space() -> None:
    listed = [int(code, 16) for code in _claim_vectors_file()["white_space"]]
    assert len(listed) == len(set(listed)) == 25
    assert set(listed) == WHITE_SPACE_15_0


def test_white_space_rule_is_not_python_isspace() -> None:
    """str.isspace() accepts exactly four more code points (U+001C to U+001F) than Unicode
    White_Space. A normaliser built on isspace() or strip() would wrongly drop them."""
    isspace = {cp for cp in range(0x110000) if chr(cp).isspace()}
    assert isspace - WHITE_SPACE_15_0 == ISSPACE_BUT_NOT_WHITE_SPACE
    assert WHITE_SPACE_15_0 - isspace == set()


@pytest.mark.parametrize(
    "code_point", sorted(WHITE_SPACE_15_0), ids=lambda cp: f"U+{cp:04X}"
)
def test_each_white_space_character_alone_is_absent(code_point: int) -> None:
    assert _rule_outcome({"value": chr(code_point)}) == "absent"
    assert _rule_outcome({"value": chr(code_point) * 3}) == "absent"


@pytest.mark.parametrize(
    "code_point", sorted(ISSPACE_BUT_NOT_WHITE_SPACE), ids=lambda cp: f"U+{cp:04X}"
)
def test_isspace_only_character_is_preserved(code_point: int) -> None:
    text = chr(code_point)
    assert text.isspace() and text.strip() == ""  # what Python would wrongly drop
    assert _rule_outcome({"value": text}) == "preserved"
    assert _rule_outcome({"value": " " + text + " "}) == "preserved"


def test_claim_vectors_are_well_formed() -> None:
    vectors = _claim_vectors()
    ids = [v["id"] for v in vectors]
    assert len(ids) == len(set(ids)), "duplicate vector id"
    for vector in vectors:
        assert set(vector) == {"id", "input", "expected", "rule"}, vector["id"]
        assert vector["input"] == {"absent": True} or set(vector["input"]) == {"value"}
        assert vector["expected"] in {"absent", "preserved"}, vector["id"]
        assert vector["rule"] in SECTION_3_2_RULES, vector["id"]


def test_claim_vectors_cover_every_row_of_section_3_2() -> None:
    vectors = _claim_vectors()
    assert {v["rule"] for v in vectors} == SECTION_3_2_RULES
    non_strings = {
        type(v["input"]["value"]).__name__
        for v in vectors
        if v["rule"] == "not-a-string"
    }
    assert non_strings == {"int", "float", "bool", "list", "dict"}
    kept = [v["input"]["value"] for v in vectors if v["expected"] == "preserved"]
    # padding is kept, not trimmed: with White_Space before, after, and both
    assert any(_is_white_space_only(s[0]) and not _is_white_space_only(s) for s in kept)
    assert any(
        _is_white_space_only(s[-1]) and not _is_white_space_only(s) for s in kept
    )
    # strings Python's isspace() would drop, but the rule keeps
    assert {ord(s) for s in kept if len(s) == 1} >= ISSPACE_BUT_NOT_WHITE_SPACE


@pytest.mark.parametrize("vector", _claim_vectors(), ids=lambda v: v["id"])
def test_claim_vector_agrees_with_section_3_2(vector: dict[str, Any]) -> None:
    assert _rule_outcome(vector["input"]) == vector["expected"]
    if vector["rule"] == "absent":
        assert vector["input"] == {"absent": True}
    elif vector["rule"] == "null":
        assert vector["input"]["value"] is None
    elif vector["rule"] == "empty":
        assert vector["input"]["value"] == ""
    elif vector["rule"] == "white-space-only":
        value = vector["input"]["value"]
        assert isinstance(value, str) and value != "" and _is_white_space_only(value)
    elif vector["rule"] == "not-a-string":
        assert not isinstance(vector["input"]["value"], str | None)


@pytest.mark.parametrize("path", OPTIONAL_CLAIMS, ids=lambda path: ".".join(path))
@pytest.mark.parametrize("vector", _claim_vectors(), ids=lambda v: v["id"])
def test_expected_result_for_every_claim_vector_is_schema_valid(
    mentor_doc: Doc, vector: dict[str, Any], path: tuple[str, ...]
) -> None:
    """Every vector, for each of name, email and context.title: the result section 3.2
    requires validates, and a preserved string is the input exactly (no trimming)."""
    result = _expected_result(mentor_doc, path, vector)
    errors = list(_validator().iter_errors(result))
    assert errors == [], [e.message for e in errors]
    target = result
    for key in path[:-1]:
        target = target[key]
    if vector["expected"] == "preserved":
        kept = target[path[-1]]
        original = vector["input"]["value"]
        assert kept.encode("utf-8") == original.encode("utf-8")
    elif path == ("context", "title"):
        assert path[-1] not in target
    else:
        assert target[path[-1]] is None


@pytest.mark.parametrize("path", OPTIONAL_CLAIMS, ids=lambda path: ".".join(path))
@pytest.mark.parametrize(
    "vector",
    [v for v in _claim_vectors() if v["rule"] == "white-space-only"],
    ids=lambda v: v["id"],
)
def test_schema_alone_accepts_a_white_space_only_string(
    mentor_doc: Doc, vector: dict[str, Any], path: tuple[str, ...]
) -> None:
    """Pins the gap stated in section 3.2: the schema does not reject a White_Space-only
    string, so the libs/lti normalisation is the only thing that removes it."""
    _set(path, vector["input"]["value"])(mentor_doc)
    assert _validator().is_valid(mentor_doc)


def test_contract_section_3_2_names_the_vectors_file() -> None:
    text = CONTRACT_PATH.read_text(encoding="utf-8")
    assert "`contracts/test-vectors/lti-launch-optional-claims.v1.json`" in text
    assert "str.isspace()" in text


@pytest.mark.parametrize("context_id", ["1", "42", "1000000", "9" * 40])
def test_positive_integer_context_ids_are_accepted(
    mentor_doc: Doc, context_id: str
) -> None:
    """No upper bound is set on purpose (contract section 3.1)."""
    mentor_doc["context"]["id"] = context_id
    assert _validator().is_valid(mentor_doc)


@pytest.mark.parametrize("role", ["mentor", "administrator"])
def test_both_baseline_roles_are_accepted(mentor_doc: Doc, role: str) -> None:
    mentor_doc["role"] = role
    assert _validator().is_valid(mentor_doc)


def _set(path: tuple[str, ...], value: object) -> Callable[[Doc], None]:
    def apply(doc: Doc) -> None:
        target = doc
        for key in path[:-1]:
            target = target[key]
        target[path[-1]] = value

    return apply


def _drop(path: tuple[str, ...]) -> Callable[[Doc], None]:
    def apply(doc: Doc) -> None:
        target = doc
        for key in path[:-1]:
            target = target[key]
        del target[path[-1]]

    return apply


# (case id, edit, JSON-pointer-like place of the error, schema keyword that must fail)
INVALID_CASES: list[tuple[str, Callable[[Doc], None], tuple[str, ...], str]] = [
    # role: learner is not a v1 value (Learner-only launches are refused before a baseline
    # session exists, PRD B3 and EXT-07; admitting it is open item OI-25 in ADR 0011)
    ("role-learner", _set(("role",), "learner"), ("role",), "enum"),
    ("role-unsupported", _set(("role",), "teacher"), ("role",), "enum"),
    ("role-wrong-case", _set(("role",), "Mentor"), ("role",), "enum"),
    ("role-not-a-string", _set(("role",), ["mentor"]), ("role",), "enum"),
    # required fields
    ("missing-iss", _drop(("iss",)), (), "required"),
    ("missing-sub", _drop(("sub",)), (), "required"),
    ("missing-deployment-id", _drop(("deployment_id",)), (), "required"),
    ("missing-message-type", _drop(("message_type",)), (), "required"),
    ("missing-role", _drop(("role",)), (), "required"),
    ("missing-context", _drop(("context",)), (), "required"),
    ("missing-context-id", _drop(("context", "id")), ("context",), "required"),
    ("missing-resource-link", _drop(("resource_link",)), (), "required"),
    (
        "missing-resource-link-id",
        _drop(("resource_link", "id")),
        ("resource_link",),
        "required",
    ),
    # message type: only LtiResourceLinkRequest in v1
    (
        "wrong-message-type",
        _set(("message_type",), "LtiDeepLinkingRequest"),
        ("message_type",),
        "const",
    ),
    # empty required strings
    ("empty-iss", _set(("iss",), ""), ("iss",), "minLength"),
    ("empty-sub", _set(("sub",), ""), ("sub",), "minLength"),
    (
        "empty-deployment-id",
        _set(("deployment_id",), ""),
        ("deployment_id",),
        "minLength",
    ),
    # context.id is a positive integer in ASCII digits (contract section 3.1). The pattern
    # also rules out the empty string, so that case fails on "pattern", not "minLength".
    ("empty-context-id", _set(("context", "id"), ""), ("context", "id"), "pattern"),
    (
        "empty-resource-link-id",
        _set(("resource_link", "id"), ""),
        ("resource_link", "id"),
        "minLength",
    ),
    # empty optional strings (null is the "absent" value, an empty string is not)
    ("empty-name", _set(("name",), ""), ("name",), "minLength"),
    ("empty-email", _set(("email",), ""), ("email",), "minLength"),
    (
        "empty-context-title",
        _set(("context", "title"), ""),
        ("context", "title"),
        "minLength",
    ),
    # context.id format: not a positive integer
    ("context-id-zero", _set(("context", "id"), "0"), ("context", "id"), "pattern"),
    (
        "context-id-negative",
        _set(("context", "id"), "-5"),
        ("context", "id"),
        "pattern",
    ),
    (
        "context-id-plus-sign",
        _set(("context", "id"), "+5"),
        ("context", "id"),
        "pattern",
    ),
    (
        "context-id-non-numeric",
        _set(("context", "id"), "abc"),
        ("context", "id"),
        "pattern",
    ),
    (
        "context-id-decimal",
        _set(("context", "id"), "4.2"),
        ("context", "id"),
        "pattern",
    ),
    (
        "context-id-exponent",
        _set(("context", "id"), "1e3"),
        ("context", "id"),
        "pattern",
    ),
    ("context-id-hex", _set(("context", "id"), "0x1F"), ("context", "id"), "pattern"),
    (
        "context-id-underscore",
        _set(("context", "id"), "4_2"),
        ("context", "id"),
        "pattern",
    ),
    (
        "context-id-leading-zero",
        _set(("context", "id"), "007"),
        ("context", "id"),
        "pattern",
    ),
    (
        "context-id-leading-space",
        _set(("context", "id"), " 42"),
        ("context", "id"),
        "pattern",
    ),
    (
        "context-id-trailing-space",
        _set(("context", "id"), "42 "),
        ("context", "id"),
        "pattern",
    ),
    (
        "context-id-leading-tab",
        _set(("context", "id"), "\t42"),
        ("context", "id"),
        "pattern",
    ),
    # leading zero, internal whitespace or newline, and padding with a no-break space
    (
        "context-id-leading-zero-1",
        _set(("context", "id"), "01"),
        ("context", "id"),
        "pattern",
    ),
    (
        "context-id-internal-space",
        _set(("context", "id"), "4 2"),
        ("context", "id"),
        "pattern",
    ),
    (
        "context-id-internal-tab",
        _set(("context", "id"), "4\t2"),
        ("context", "id"),
        "pattern",
    ),
    (
        "context-id-internal-newline",
        _set(("context", "id"), "4\n2"),
        ("context", "id"),
        "pattern",
    ),
    (
        "context-id-leading-nbsp",
        _set(("context", "id"), NBSP + "42"),
        ("context", "id"),
        "pattern",
    ),
    (
        "context-id-trailing-nbsp",
        _set(("context", "id"), "42" + NBSP),
        ("context", "id"),
        "pattern",
    ),
    # a trailing newline is the case a plain "$" would let through in Python's re
    (
        "context-id-trailing-newline",
        _set(("context", "id"), "42\n"),
        ("context", "id"),
        "pattern",
    ),
    (
        "context-id-leading-newline",
        _set(("context", "id"), "\n42"),
        ("context", "id"),
        "pattern",
    ),
    (
        "context-id-trailing-cr",
        _set(("context", "id"), "42\r"),
        ("context", "id"),
        "pattern",
    ),
    (
        "context-id-trailing-crlf",
        _set(("context", "id"), "42\r\n"),
        ("context", "id"),
        "pattern",
    ),
    (
        "context-id-line-separator",
        _set(("context", "id"), "42" + LINE_SEPARATOR),
        ("context", "id"),
        "pattern",
    ),
    (
        "context-id-arabic-indic-digits",
        _set(("context", "id"), "٤٢"),
        ("context", "id"),
        "pattern",
    ),
    (
        "context-id-fullwidth-digits",
        _set(("context", "id"), "４２"),
        ("context", "id"),
        "pattern",
    ),
    # types
    ("numeric-sub", _set(("sub",), 1001), ("sub",), "type"),
    ("null-iss", _set(("iss",), None), ("iss",), "type"),
    # message_type is a constant, so a null fails on "const", not "type"
    ("null-message-type", _set(("message_type",), None), ("message_type",), "const"),
    # name, email and context.title: contract section 3.2 says libs/lti treats a value that is
    # not a string as absent, so a result never carries one. The schema rejects it.
    ("numeric-name", _set(("name",), 123), ("name",), "type"),
    ("object-name", _set(("name",), {}), ("name",), "type"),
    ("boolean-email", _set(("email",), True), ("email",), "type"),
    ("list-email", _set(("email",), ["a@example.org"]), ("email",), "type"),
    ("boolean-name", _set(("name",), False), ("name",), "type"),
    ("numeric-email", _set(("email",), 0), ("email",), "type"),
    (
        "list-context-title",
        _set(("context", "title"), ["Week 1"]),
        ("context", "title"),
        "type",
    ),
    (
        "numeric-context-title",
        _set(("context", "title"), 5),
        ("context", "title"),
        "type",
    ),
    # context.title is omitted when empty, never null (contract section 3.2)
    (
        "null-context-title",
        _set(("context", "title"), None),
        ("context", "title"),
        "type",
    ),
    ("numeric-context-id", _set(("context", "id"), 42), ("context", "id"), "type"),
    ("context-not-an-object", _set(("context",), "42"), ("context",), "type"),
    (
        "resource-link-not-an-object",
        _set(("resource_link",), "link-7"),
        ("resource_link",),
        "type",
    ),
]


@pytest.mark.parametrize(
    ("edit", "place", "keyword"),
    [pytest.param(e, p, k, id=i) for i, e, p, k in INVALID_CASES],
)
def test_invalid_launch_result_is_rejected_at_the_right_place(
    mentor_doc: Doc, edit: Callable[[Doc], None], place: tuple[str, ...], keyword: str
) -> None:
    edit(mentor_doc)
    errors = list(_validator().iter_errors(mentor_doc))
    assert errors, "the invalid document was accepted"
    assert [(tuple(map(str, e.absolute_path)), e.validator) for e in errors] == [
        (place, keyword)
    ]


def _required_paths(
    schema: dict[str, Any], prefix: tuple[str, ...] = ()
) -> list[tuple[str, ...]]:
    """Every required field at every depth, as a path such as ("context", "id")."""
    found = [prefix + (name,) for name in schema.get("required", [])]
    for name, child in schema.get("properties", {}).items():
        found += _required_paths(child, prefix + (name,))
    return found


@pytest.mark.parametrize(
    "path", _required_paths(_schema()), ids=lambda path: ".".join(path)
)
def test_dropping_a_required_field_reports_exactly_that_field(
    mentor_doc: Doc, path: tuple[str, ...]
) -> None:
    """The generic "required" keyword is not enough: the one error must name the field that
    was dropped, so a case that drops the wrong field cannot pass."""
    _drop(path)(mentor_doc)
    errors = list(_validator().iter_errors(mentor_doc))
    assert len(errors) == 1, [e.message for e in errors]
    error = errors[0]
    assert error.validator == "required"
    assert tuple(map(str, error.absolute_path)) == path[:-1]
    assert set(error.validator_value) - set(error.instance) == {path[-1]}


def test_contract_markdown_quotes_the_schema_context_id_pattern() -> None:
    """Drift guard: contract section 3.1 states the pattern; it must be the schema's."""
    pattern = _schema()["properties"]["context"]["properties"]["id"]["pattern"]
    assert f"`{pattern}`" in CONTRACT_PATH.read_text(encoding="utf-8")


def test_every_required_field_has_a_missing_case() -> None:
    """If the schema gains a required field, at any depth, this fails until a negative case
    is added. The case id is "missing-" plus the path, for example "missing-context-id"."""
    covered = {i for i, _, _, _ in INVALID_CASES}
    paths = _required_paths(_schema())
    assert ("context", "id") in paths and ("resource_link", "id") in paths
    for path in paths:
        case_id = "missing-" + "-".join(path).replace("_", "-")
        assert case_id in covered, case_id


# Contract section 5: role mapping and precedence (OI-22, decided by the guide).

PRD_PATH = ROOT / "docs" / "PRD.md"
# The LTI 1.3 version claim, named by its full URI (it is validation-only, never in the result).
LTI_VERSION_CLAIM = "https://purl.imsglobal.org/spec/lti/claim/version"

INSTRUCTOR = "http://purl.imsglobal.org/vocab/lis/v2/membership#Instructor"
LEARNER = "http://purl.imsglobal.org/vocab/lis/v2/membership#Learner"
INSTITUTION_ADMIN = (
    "http://purl.imsglobal.org/vocab/lis/v2/institution/person#Administrator"
)
SYSTEM_ADMIN = "http://purl.imsglobal.org/vocab/lis/v2/system/person#Administrator"
UNLISTED = (
    "http://purl.imsglobal.org/vocab/lis/v2/membership#Mentor"  # not a B3 role URI
)
# Matching is exact on the listed URIs (guide decision): no short names, no sub-roles, no
# aliases and no prefix, case or scheme matching. Each of these is therefore an unlisted URI.
SHORT_INSTRUCTOR = "Instructor"
TEACHING_ASSISTANT = (
    "http://purl.imsglobal.org/vocab/lis/v2/membership/Instructor#TeachingAssistant"
)
INSTRUCTOR_LOOKALIKES = {
    "short-name": SHORT_INSTRUCTOR,
    "teaching-assistant-sub-role": TEACHING_ASSISTANT,
    "lower-case-fragment": INSTRUCTOR.replace("#Instructor", "#instructor"),
    "https-scheme": INSTRUCTOR.replace("http://", "https://"),
    "trailing-space": INSTRUCTOR + " ",
    "lti-1.1-urn": "urn:lti:role:ims/lis/Instructor",
}

REFUSED_NO_ROLE = "refused: no recognised role"
REFUSED_LEARNER_ONLY = "refused: learner is the only recognised role"


def _flat(text: str) -> str:
    """Collapse line breaks and runs of spaces, so a sentence wrapped in Markdown still matches."""
    return " ".join(text.split())


def _resolve_role(role_uris: list[str]) -> str:
    """Contract section 5 restated: unlisted URIs are ignored, Administrator beats Instructor,
    Learner counts only when it is the only recognised role. It is not the gateway."""
    recognised = {INSTRUCTOR, INSTITUTION_ADMIN, LEARNER} & set(role_uris)
    if INSTITUTION_ADMIN in recognised:
        return "administrator"
    if INSTRUCTOR in recognised:
        return "mentor"
    if LEARNER in recognised:
        return REFUSED_LEARNER_ONLY
    return REFUSED_NO_ROLE


# (case id, incoming role URIs, normalised role or the refusal). The source of each case is
# ADR 0011 section 10.3 (OI-22 and the guide's rules 1 to 6) or the contract section 5 rules.
ROLE_CASES: list[tuple[str, list[str], str]] = [
    ("instructor", [INSTRUCTOR], "mentor"),
    ("institution-administrator", [INSTITUTION_ADMIN], "administrator"),
    ("learner-only", [LEARNER], REFUSED_LEARNER_ONLY),
    ("no-roles", [], REFUSED_NO_ROLE),
    ("unlisted-only", [UNLISTED], REFUSED_NO_ROLE),
    ("system-administrator-only", [SYSTEM_ADMIN], REFUSED_NO_ROLE),
    # OI-22: an unlisted role is ignored, never a reason to refuse a recognised role
    ("instructor-plus-unlisted", [INSTRUCTOR, UNLISTED], "mentor"),
    (
        "institution-and-system-administrator",
        [INSTITUTION_ADMIN, SYSTEM_ADMIN],
        "administrator",
    ),
    (
        "moodle-site-administrator",
        [INSTRUCTOR, INSTITUTION_ADMIN, SYSTEM_ADMIN],
        "administrator",
    ),
    # rule 1: Administrator takes precedence
    (
        "administrator-beats-instructor",
        [INSTRUCTOR, INSTITUTION_ADMIN],
        "administrator",
    ),
    # rules 2 and 3: Learner counts only when it is the only recognised role
    ("instructor-plus-learner", [INSTRUCTOR, LEARNER], "mentor"),
    ("administrator-plus-learner", [INSTITUTION_ADMIN, LEARNER], "administrator"),
    ("learner-plus-unlisted", [LEARNER, UNLISTED], REFUSED_LEARNER_ONLY),
    (
        "learner-plus-system-administrator",
        [LEARNER, SYSTEM_ADMIN],
        REFUSED_LEARNER_ONLY,
    ),
    ("duplicate-instructor", [INSTRUCTOR, INSTRUCTOR], "mentor"),
    (
        "every-role-at-once",
        [LEARNER, UNLISTED, SYSTEM_ADMIN, INSTRUCTOR, INSTITUTION_ADMIN],
        "administrator",
    ),
    # exact matching: a look-alike of Instructor is unlisted, so it is ignored
    *[
        (f"{name}-only", [uri], REFUSED_NO_ROLE)
        for name, uri in INSTRUCTOR_LOOKALIKES.items()
    ],
    *[
        (f"{name}-plus-learner", [uri, LEARNER], REFUSED_LEARNER_ONLY)
        for name, uri in INSTRUCTOR_LOOKALIKES.items()
    ],
    ("teaching-assistant-plus-instructor", [TEACHING_ASSISTANT, INSTRUCTOR], "mentor"),
    (
        "teaching-assistant-plus-institution-administrator",
        [TEACHING_ASSISTANT, INSTITUTION_ADMIN],
        "administrator",
    ),
    ("short-instructor-plus-instructor", [SHORT_INSTRUCTOR, INSTRUCTOR], "mentor"),
]


def _section_5_table() -> dict[str, str]:
    """Contract section 5 table: role URI -> text of the second column."""
    body = CONTRACT_PATH.read_text(encoding="utf-8")
    body = body.split("## 5. Role mapping and precedence", 1)[1].split("\n## ", 1)[0]
    rows: dict[str, str] = {}
    for line in body.splitlines():
        if not line.startswith(("| `http", "| Any other URI")):
            continue
        first, second = (cell.strip() for cell in line.strip().strip("|").split("|"))
        found = re.findall(r"`(http[^`]+)`", first)
        assert len(found) == 1, line
        rows[found[0]] = second
    return rows


def test_contract_section_5_table_matches_the_agreed_role_uris() -> None:
    table = _section_5_table()
    assert set(table) == {INSTRUCTOR, INSTITUTION_ADMIN, LEARNER, SYSTEM_ADMIN}
    assert table[INSTRUCTOR] == "`mentor`"
    assert table[INSTITUTION_ADMIN] == "`administrator`"
    assert table[LEARNER].startswith("Learner: refused by baseline tools")
    assert table[SYSTEM_ADMIN] == "Ignored"


@pytest.mark.parametrize(
    ("roles", "expected"),
    [pytest.param(r, e, id=i) for i, r, e in ROLE_CASES],
)
def test_role_resolution_follows_oi_22_in_any_order(
    roles: list[str], expected: str
) -> None:
    for ordering in itertools.permutations(roles):
        assert _resolve_role(list(ordering)) == expected


def test_role_cases_cover_every_oi_22_row_and_every_pair_of_recognised_roles() -> None:
    covered = {frozenset(roles) for _, roles, _ in ROLE_CASES}
    recognised = [INSTRUCTOR, INSTITUTION_ADMIN, LEARNER]
    for size in (1, 2, 3):
        for combo in itertools.combinations(recognised, size):
            assert any(set(combo) <= c for c in covered), combo
    # the three OI-22 rows: unknown only, Instructor + unknown, institution + system administrator
    assert frozenset([UNLISTED]) in covered
    assert frozenset([INSTRUCTOR, UNLISTED]) in covered
    assert frozenset([INSTITUTION_ADMIN, SYSTEM_ADMIN]) in covered


def test_instructor_lookalikes_are_unlisted_and_named_nowhere_in_section_5() -> None:
    """Exact matching (guide decision): none of these is a listed URI, so the contract table
    must not name it, and each one alone resolves to no recognised role."""
    table = _section_5_table()
    for name, uri in INSTRUCTOR_LOOKALIKES.items():
        assert uri != INSTRUCTOR and uri not in table, name
        assert _resolve_role([uri]) == REFUSED_NO_ROLE, name
    covered = {frozenset(roles) for _, roles, _ in ROLE_CASES}
    for uri in INSTRUCTOR_LOOKALIKES.values():
        assert frozenset([uri]) in covered and frozenset([uri, LEARNER]) in covered


def test_resolved_roles_are_schema_values_and_refusals_never_are() -> None:
    allowed = set(_schema()["properties"]["role"]["enum"])
    assert allowed == {"mentor", "administrator"}
    for _, _, outcome in ROLE_CASES:
        if outcome in (REFUSED_NO_ROLE, REFUSED_LEARNER_ONLY):
            assert outcome not in allowed
        else:
            assert outcome in allowed


def test_contract_and_prd_state_the_oi_22_rule() -> None:
    contract = _flat(CONTRACT_PATH.read_text(encoding="utf-8"))
    prd = _flat(PRD_PATH.read_text(encoding="utf-8"))
    assert (
        "An unlisted role never causes a refusal when a recognised role is also present."
        in contract
    )
    assert (
        "Administrator takes precedence if both administrator and instructor are present."
        in contract
    )
    assert (
        "Instructor plus Learner resolves to `mentor` for baseline tools." in contract
    )
    assert "role URIs not listed in §B3 are ignored" in prd
    assert "only if no recognised role remains" in prd
    # the superseded wording must not come back
    assert "a launch with any role not listed is refused" not in prd.lower()


def test_contract_and_prd_document_lti_version_as_validation_only() -> None:
    """The LTI version claim is named by its full URI, must be exactly "1.3.0", and is only
    checked: it never reaches the normalised result."""
    contract = _flat(CONTRACT_PATH.read_text(encoding="utf-8"))
    prd = _flat(PRD_PATH.read_text(encoding="utf-8"))
    claim = f"`{LTI_VERSION_CLAIM}`"

    # Both documents name the claim by its full URI, never by a bare `version`.
    assert claim in contract and claim in prd
    assert "| `version` |" not in contract and "`azp`, `version`," not in prd

    # Contract section 3: required, exactly "1.3.0", validation only.
    assert (
        f'| {claim} | Yes; must equal `"1.3.0"` exactly | Checked only; never passed on |'
        in contract
    )
    # Contract section 8: a missing or incorrect version refuses the launch.
    assert f'{claim} (missing, or not exactly `"1.3.0"`)' in contract

    # The PRD lists it among the inspected claims and states the same rule.
    assert (
        'The version claim must equal `"1.3.0"`; it, `aud`, `azp`, `exp` and `nonce` are '
        "used only to validate the launch" in prd
    )

    # Contract section 4: version is validation material, not part of the normalised result.
    normalised_section = contract.split("## 4. Normalised launch result", 1)[1].split(
        "## 5.", 1
    )[0]
    assert LTI_VERSION_CLAIM not in normalised_section
    assert "`version`" not in normalised_section


# Contract sections 6 and 7: session identity and course link (OI-21), issuer separation.


def _session_identity(doc: Doc) -> tuple[str, str, str]:
    """Contract section 6: the session is bound to (iss, sub, context id)."""
    return (doc["iss"], doc["sub"], doc["context"]["id"])


def _course_link_key(doc: Doc) -> tuple[str, str]:
    """Contract section 7: shared.course_link is keyed by iss plus context id."""
    return (doc["iss"], doc["context"]["id"])


def _with_issuer(doc: Doc, iss: str) -> Doc:
    other = copy.deepcopy(doc)
    other["iss"] = iss
    return other


def test_two_platforms_with_the_same_user_and_course_numbers_do_not_collide(
    mentor_doc: Doc,
) -> None:
    """Moodle's sub and course ids repeat across sites (ADR 0011 OI-21), so the same pair can
    come from two issuers. Without iss they would be one identity."""
    other = _with_issuer(mentor_doc, "https://moodle.other.example.org")
    assert _validator().is_valid(mentor_doc) and _validator().is_valid(other)
    assert (mentor_doc["sub"], mentor_doc["context"]["id"]) == (
        other["sub"],
        other["context"]["id"],
    )
    assert _session_identity(mentor_doc) != _session_identity(other)
    assert _course_link_key(mentor_doc) != _course_link_key(other)


@pytest.mark.parametrize(
    "iss",
    ["https://moodle.example.org/", "HTTPS://MOODLE.EXAMPLE.ORG"],
    ids=["trailing-slash", "upper-case"],
)
def test_issuer_is_compared_as_received_not_normalised(
    mentor_doc: Doc, iss: str
) -> None:
    """Contract section 7.1: no case folding and no trailing-slash normalisation. The schema
    accepts both strings and nothing merges them, so they stay distinct identities (whether such
    an issuer is registered is the gateway's check)."""
    other = _with_issuer(mentor_doc, iss)
    assert _validator().is_valid(other)
    assert _session_identity(mentor_doc) != _session_identity(other)
    assert _course_link_key(mentor_doc) != _course_link_key(other)


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("iss",), "https://moodle.other.example.org"),
        (("sub",), "user-2000"),
        (("context", "id"), "99"),
    ],
    ids=["iss", "sub", "context-id"],
)
def test_session_identity_changes_with_each_of_iss_sub_and_context_id(
    mentor_doc: Doc, path: tuple[str, ...], value: str
) -> None:
    other = copy.deepcopy(mentor_doc)
    _set(path, value)(other)
    assert _session_identity(other) != _session_identity(mentor_doc)


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("role",), "administrator"),
        (("deployment_id",), "deployment-2"),
        (("resource_link", "id"), "link-99"),
        (("name",), "Someone Else"),
        (("email",), None),
        (("context", "title"), "Another title"),
    ],
    ids=["role", "deployment-id", "resource-link-id", "name", "email", "context-title"],
)
def test_other_fields_are_not_part_of_the_identity_or_course_link(
    mentor_doc: Doc, path: tuple[str, ...], value: object
) -> None:
    other = copy.deepcopy(mentor_doc)
    _set(path, value)(other)
    assert _session_identity(other) == _session_identity(mentor_doc)
    assert _course_link_key(other) == _course_link_key(mentor_doc)


def test_course_link_key_has_no_user_part(mentor_doc: Doc) -> None:
    """Two users of one course on one platform share the course link."""
    colleague = copy.deepcopy(mentor_doc)
    colleague["sub"] = "user-2000"
    assert _course_link_key(colleague) == _course_link_key(mentor_doc)
    assert _session_identity(colleague) != _session_identity(mentor_doc)


def test_contract_prd_and_adr_state_the_decided_identity_and_course_link_key() -> None:
    contract = _flat(CONTRACT_PATH.read_text(encoding="utf-8"))
    prd = _flat(PRD_PATH.read_text(encoding="utf-8"))
    adr = _flat(
        (ROOT / "docs" / "decisions" / "0011-lti-library.md").read_text("utf-8")
    )
    identity = "(`iss`, `sub`, context id)"
    assert identity in contract and identity in prd
    assert "(iss, sub, context id)" in adr  # the ADR writes the tuple as one code span
    assert "keyed by **`iss` plus context id**" in contract
    assert "keyed by `iss` plus context id" in prd
    # the superseded identity must not be the stated one
    assert "(`sub`, context id)" not in contract
    assert "(`sub`, context id)" not in prd
    # contract 7.1: exact issuer matching, no fallback to another platform
    assert (
        "no trimming, no case folding and no trailing-slash or other normalisation"
        in contract
    )
    assert "never a fallback" in contract
