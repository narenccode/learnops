"""B7 H5P practice output contract (PRD B7): the text, the content-type schema, its example and
the example course package.

AUTOMATED here:
  * the schema is valid and the content-type example validates; the schema allows only the four
    PRD B7 phrases (an enum, so invented names, other capitals and machine names are rejected)
    and each at most once; a test checks that the enum equals the phrases in the PRD B7 text;
  * the schema and example contain no key named version, library, libraries or machine_name, no
    string of the form H5P.<letter>, and no key cue, cues or ref. Other spellings of a version are
    NOT detected; the contract text marks every content type "to verify in the lab", keeps its
    open decisions marked and says it cannot be frozen;
  * `file` is defined in the h5p branch of the B1 schema only (guide's decision, Issue #44);
  * the example package validates against B1; its ordinary practice item is ungraded, names a
    lowercase .h5p path and comes right after the guide Page; the week keeps one Page and one
    Assignment. These are checks on the EXAMPLE, not general enforcement;
  * no .h5p file exists anywhere in the repository (.gitignore does not block it).

NOT automated here, so NOT claimed (contract text, section 8): placement and the one-Page,
one-Assignment week in packages in general (B1.2 rule 1); video checkpoint placement (open); that
the named file exists or uses an allowed type; the lab-only rule for interactive video; CK-11 and
CK-12 (Release 1); mentor approval of AI drafts; cues.json contents (the B6 schema does not exist
yet); library versions and the number of practice items per week.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

import pytest
import yaml
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[3]
CONTRACTS = ROOT / "contracts"
SCHEMA_PATH = CONTRACTS / "h5p-practice.v1.schema.json"
TEXT_PATH = CONTRACTS / "h5p-practice.v1.md"
ALLOW_LIST_PATH = CONTRACTS / "examples" / "h5p-practice.v1.content-types.json"
PACKAGE_DIR = CONTRACTS / "examples" / "h5p-practice.v1"
B1_SCHEMA_PATH = CONTRACTS / "course-package.v1.schema.json"
PRD_PATH = ROOT / "docs" / "PRD.md"

# The content types of PRD B7, as it writes them. The second is one phrase because whether it is
# one type or a choice is an open decision.
CONTENT_TYPES = {
    "question set",
    "drag-the-words or drag-and-drop / ordering",
    "branching scenario",
    "interactive video",
}
SKIPPED = {".git", ".mypy_cache", ".pytest_cache", ".ruff_cache", ".venv", "venv"}
SKIPPED |= {"node_modules", "__pycache__"}
MACHINE_NAME = re.compile(r"H5P\.[A-Za-z]")
FORBIDDEN_KEYS = {"version", "library", "libraries", "machine_name"}

Doc = dict[str, Any]


def _json(path: Path) -> Doc:
    loaded: Doc = json.loads(path.read_text(encoding="utf-8"))
    return loaded


def _prd_b7_text() -> str:
    prd = PRD_PATH.read_text(encoding="utf-8")
    match = re.search(r"^## B7\..*?(?=^## B8\.)", prd, flags=re.DOTALL | re.MULTILINE)
    assert match, "PRD section B7 was not found"
    return match.group(0).lower()


def _walk(node: Any) -> list[str]:
    """Every object key and every string value at any depth."""
    if isinstance(node, dict):
        return [s for k, v in node.items() for s in [k, *_walk(v)]]
    if isinstance(node, list):
        return [s for item in node for s in _walk(item)]
    return [node] if isinstance(node, str) else []


@pytest.fixture(scope="module")
def schema() -> Doc:
    return _json(SCHEMA_PATH)


@pytest.fixture(scope="module")
def validator(schema: Doc) -> Draft202012Validator:
    return Draft202012Validator(schema, format_checker=FormatChecker())


@pytest.fixture(scope="module")
def allow_list() -> Doc:
    return _json(ALLOW_LIST_PATH)


@pytest.fixture(scope="module")
def text() -> str:
    return TEXT_PATH.read_text(encoding="utf-8").replace("**", "")


@pytest.fixture(scope="module")
def package() -> Doc:
    loaded: Doc = yaml.safe_load((PACKAGE_DIR / "course.yaml").read_text("utf-8"))
    return loaded


# --- the schema and the content-type example -----------------------------------------------


def test_schema_is_valid_and_example_validates(
    schema: Doc, validator: Draft202012Validator, allow_list: Doc
) -> None:
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    Draft202012Validator.check_schema(schema)
    assert [e.message for e in validator.iter_errors(allow_list)] == []


def test_schema_enum_and_example_hold_exactly_the_prd_phrases(
    schema: Doc, allow_list: Doc, text: str
) -> None:
    enum = schema["$defs"]["content_type"]["properties"]["name"]["enum"]
    assert len(enum) == len(set(enum)) and set(enum) == CONTENT_TYPES
    prd = _prd_b7_text()
    assert all(name in prd for name in enum), "a phrase is not written as in PRD B7"
    names = [item["name"] for item in allow_list["content_types"]]
    assert sorted(names) == sorted(CONTENT_TYPES)
    # Lab-only status is a rule of the text, not a schema field (design question for reviewers).
    assert "interactive video only in lab demonstrations" in prd
    row = [r for r in text.splitlines() if r.startswith("| interactive video |")]
    assert len(row) == 1 and "Lab demonstrations only" in row[0]


CONTENT_TYPES_LIST = sorted(CONTENT_TYPES)
CASES: list[tuple[str, Any, str]] = [
    ("wrong schema name", {"schema": "learnops.h5p-practice/v2"}, "const"),
    ("no content types", {"content_types": []}, "minItems"),
    ("content types is not a list", {"content_types": {}}, "type"),
    ("entry without a name", {"content_types": [{}]}, "required"),
    ("entry with an empty name", {"content_types": [{"name": ""}]}, "enum"),
    ("entry with a numeric name", {"content_types": [{"name": 5}]}, "enum"),
    ("invented name", {"content_types": [{"name": "flashcards"}]}, "enum"),
    ("wrong capitals", {"content_types": [{"name": "Question Set"}]}, "enum"),
    ("machine name", {"content_types": [{"name": "H5P.QuestionSet"}]}, "enum"),
    ("half of the drag phrase", {"content_types": [{"name": "drag-the-words"}]}, "enum"),
    ("name listed twice", {"content_types": [{"name": "question set"}] * 2}, "maxContains"),
    ("drag phrase twice", {"content_types": [{"name": CONTENT_TYPES_LIST[1]}] * 2}, "maxContains"),
]  # fmt: skip


@pytest.mark.parametrize(
    ("change", "keyword"), [pytest.param(c, k, id=n) for n, c, k in CASES]
)
def test_invalid_content_type_list_is_rejected(
    validator: Draft202012Validator, allow_list: Doc, change: Doc, keyword: str
) -> None:
    broken = {**allow_list, **change}
    assert keyword in {e.validator for e in validator.iter_errors(broken)}


@pytest.mark.parametrize("field", ["schema", "content_types"])
def test_missing_root_field_is_rejected(
    validator: Draft202012Validator, allow_list: Doc, field: str
) -> None:
    broken = {k: v for k, v in allow_list.items() if k != field}
    assert "required" in {e.validator for e in validator.iter_errors(broken)}


def test_unknown_fields_are_accepted(
    validator: Draft202012Validator, allow_list: Doc
) -> None:
    extended = {**allow_list, "future": 1}
    extended["content_types"] = [{**allow_list["content_types"][0], "future": 1}]
    assert [e.message for e in validator.iter_errors(extended)] == []


# --- nothing is invented -------------------------------------------------------------------


def test_no_listed_machine_name_version_or_cue_key_is_defined(
    schema: Doc, allow_list: Doc, text: str
) -> None:
    for document in (schema, allow_list):
        words = _walk(document)
        assert not {w for w in words if w in FORBIDDEN_KEYS}
        assert not [w for w in words if MACHINE_NAME.search(w)]
        assert not {w for w in words if w.lower() in {"cue", "cues", "ref"}}
    assert not MACHINE_NAME.search(text)
    assert "defines no second format" in text  # cues.json is B6's


def test_text_marks_versions_open_decisions_and_the_draft_rules(text: str) -> None:
    rows = [line for line in text.splitlines() if line.startswith("| ")]
    for name in CONTENT_TYPES:
        row = [r for r in rows if r.startswith(f"| {name} |")]
        assert len(row) == 1 and "to verify in the lab" in row[0], name
    for phrase in (
        "cannot be frozen",
        "OPEN DECISION: library versions",
        "OPEN DECISION: the `ref` kinds",
        "OPEN DECISION: several practice items",
        "OPEN DECISION: video checkpoint placement",
        "Practice is optional",
        "never graded",
    ):
        assert phrase in text, phrase


# --- the B1 side and the example package ---------------------------------------------------


def test_file_is_defined_in_the_h5p_branch_only() -> None:
    activity = _json(B1_SCHEMA_PATH)["$defs"]["activity"]
    assert "file" not in activity["properties"]
    [branch] = [
        b["then"]
        for b in activity["allOf"]
        if b["if"]["properties"]["type"]["const"] == "h5p"
    ]
    assert {"file", "graded"} <= set(branch["required"])
    assert "file" in branch["properties"]


def test_example_package_validates_against_b1(package: Doc) -> None:
    b1 = Draft202012Validator(_json(B1_SCHEMA_PATH), format_checker=FormatChecker())
    assert [e.message for e in b1.iter_errors(package)] == []


def test_example_week_is_standard_with_an_optional_practice_item(package: Doc) -> None:
    # The example has no video lesson, so this says nothing about video checkpoint placement.
    practice = 0
    for section in package["sections"]:
        acts = section["activities"]
        kinds = [a["type"] for a in acts]
        assert kinds.count("page") == 1 and kinds.count("assignment") == 1
        for index, act in enumerate(acts):
            if act["type"] != "h5p":
                continue
            practice += 1
            # Ordinary practice: right after the guide Page, by list order (no ordering field).
            assert index > 0 and kinds[index - 1] == "page"
            assert act["graded"] is False and "points" not in act
            assert act["file"].endswith(".h5p")
            assert not (PACKAGE_DIR / act["file"]).exists()
        assert all((PACKAGE_DIR / a["body"]).is_file() for a in acts if "body" in a)
    assert practice >= 1


def test_no_h5p_file_is_kept_in_the_repository() -> None:
    found: list[str] = []
    for folder, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIPPED]
        found += [
            str(Path(folder, f).relative_to(ROOT))
            for f in files
            if f.lower().endswith(".h5p")
        ]
    assert found == [], f"remove these .h5p files (B7 rule R5): {found}"
