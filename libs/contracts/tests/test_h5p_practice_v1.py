"""B7 H5P practice output contract (PRD B7): the text, the content-type schema, its example and
the example course package.

AUTOMATED here:
  * the schema is valid and the content-type example validates; the schema allows only the five
    content types below, each at most once, and pins each to its H5P library (machine_name) and
    exact version as reported by the guide's lab check of 2026-11-11 (PRD App-C item 5). A wrong
    name, machine name or version, and a swapped pair, are rejected. The pins are written out in
    this file (PINNED) and the schema, the example, the contract text and the decision record
    must each agree with them;
  * the schema and example define no cue key (cues.json belongs to B6), and the contract text keeps
    its other open decisions marked and no longer lists the two the lab check settled;
  * `file` is defined in the h5p branch of the B1 schema only (guide's decision, Issue #44);
  * the example package validates against B1; its ordinary practice item is ungraded, names a
    lowercase .h5p path and comes right after the guide Page; the week keeps one Page and one
    Assignment. These are checks on the EXAMPLE, not general enforcement;
  * no .h5p file exists anywhere in the repository (.gitignore does not block it).

NOT automated here, so NOT claimed (contract text, section 8): placement and the one-Page,
one-Assignment week in packages in general (B1.2 rule 1); video checkpoint placement (open); that
the named file exists or really uses a pinned library and version; the lab-only rule for
interactive video; CK-11 and CK-12 (Release 1); mentor approval of AI drafts; cues.json contents
(the B6 schema does not exist yet); the number of practice items per week; and the lab check
itself, which the guide did and this repository holds no evidence of beyond the decision record.
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
DECISIONS_DIR = ROOT / "docs" / "decisions"
TRACEABILITY_PATH = ROOT / "docs" / "traceability.md"

# The five content types of B7 with their H5P library (machine name) and exact version, as the
# guide reported the lab check of 2026-11-11 on both lab sites (Moodle 4.5 and 5.3): PR #54,
# comment of 2026-11-11 09:19 UTC, PRD App-C item 5. Written out here on purpose, so that the
# schema, the example, the contract text and the decision record must each agree with it.
# Drag and Drop is H5P.DragQuestion 1.15.37 and Drag the Words is H5P.DragText 1.10.50: do not
# swap their versions. The names are the words PRD B7 uses ("drag-the-words or drag-and-drop /
# ordering" is two types, the guide's decision of 2026-11-11).
PINNED: dict[str, tuple[str, str]] = {
    "question set": ("H5P.QuestionSet", "1.21.14"),
    "drag-the-words": ("H5P.DragText", "1.10.50"),
    "drag-and-drop": ("H5P.DragQuestion", "1.15.37"),
    "branching scenario": ("H5P.BranchingScenario", "1.11.2"),
    "interactive video": ("H5P.InteractiveVideo", "1.28.37"),
}
SKIPPED = {".git", ".mypy_cache", ".pytest_cache", ".ruff_cache", ".venv", "venv"}
SKIPPED |= {"node_modules", "__pycache__"}

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


def _cells(row: str) -> list[str]:
    """The cells of a Markdown table row, without the backticks around a code span."""
    return [cell.strip().strip("`") for cell in row.strip().strip("|").split("|")]


def _entry(name: str) -> Doc:
    machine_name, version = PINNED[name]
    return {"name": name, "machine_name": machine_name, "version": version}


def _without(entry: Doc, key: str) -> Doc:
    return {k: v for k, v in entry.items() if k != key}


def _doc(*entries: Doc) -> Doc:
    return {"schema": "learnops.h5p-practice/v1", "content_types": list(entries)}


def _schema_pins(schema: Doc) -> dict[str, tuple[str, str]]:
    """name -> (machine_name, version) as the schema pins them, one if/then branch each."""
    pins: dict[str, tuple[str, str]] = {}
    for branch in schema["$defs"]["content_type"]["allOf"]:
        name = branch["if"]["properties"]["name"]["const"]
        then = branch["then"]["properties"]
        pins[name] = (then["machine_name"]["const"], then["version"]["const"])
    return pins


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


@pytest.fixture(scope="module")
def record_path() -> Path:
    found = sorted(DECISIONS_DIR.glob("*-h5p-content-types.md"))
    assert len(found) == 1, f"expected one H5P decision record, found {found}"
    return found[0]


# --- the schema and the content-type example -----------------------------------------------


def test_schema_is_valid_and_example_validates(
    schema: Doc, validator: Draft202012Validator, allow_list: Doc
) -> None:
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    Draft202012Validator.check_schema(schema)
    assert [e.message for e in validator.iter_errors(allow_list)] == []


def test_schema_pins_exactly_the_guides_table(schema: Doc, text: str) -> None:
    definition = schema["$defs"]["content_type"]
    enum = definition["properties"]["name"]["enum"]
    assert len(enum) == len(set(enum)) and set(enum) == set(PINNED)
    assert set(definition["required"]) == {"name", "machine_name", "version"}
    assert _schema_pins(schema) == PINNED
    prd = _prd_b7_text()
    assert all(name in prd for name in enum), "a name is not written as in PRD B7"
    # Lab-only status is a rule of the text, not a schema field (design question for reviewers).
    assert "interactive video only in lab demonstrations" in prd
    row = [r for r in text.splitlines() if r.startswith("| interactive video |")]
    assert len(row) == 1 and "Lab demonstrations only" in row[0]


def test_example_lists_exactly_the_pinned_entries(allow_list: Doc) -> None:
    assert allow_list["content_types"] == [_entry(name) for name in PINNED]


def test_contract_text_and_decision_record_agree_with_the_pins(
    text: str, record_path: Path
) -> None:
    record = record_path.read_text(encoding="utf-8")
    for name, (machine_name, version) in PINNED.items():
        [row] = [r for r in text.splitlines() if r.startswith(f"| {name} |")]
        assert _cells(row)[1:3] == [machine_name, version], name
        rows = [r for r in record.splitlines() if r.startswith("| ")]
        [recorded] = [r for r in rows if f"`{machine_name}`" in r]
        assert version in _cells(recorded), name


def test_text_schema_and_traceability_point_to_the_decision_record(
    schema: Doc, text: str, record_path: Path
) -> None:
    path = f"docs/decisions/{record_path.name}"
    assert path in " ".join(text.split())
    assert path in schema["$comment"]
    assert path in TRACEABILITY_PATH.read_text(encoding="utf-8")


Q, TW, DD = _entry("question set"), _entry("drag-the-words"), _entry("drag-and-drop")
CASES: list[tuple[str, Doc, str]] = [
    ("wrong schema name", {**_doc(Q), "schema": "learnops.h5p-practice/v2"}, "const"),
    ("no content types", _doc(), "minItems"),
    ("content types is not a list", {**_doc(Q), "content_types": {}}, "type"),
    ("entry without a name", _doc(_without(Q, "name")), "required"),
    ("entry without a machine_name", _doc(_without(Q, "machine_name")), "required"),
    ("entry without a version", _doc(_without(Q, "version")), "required"),
    ("entry with an empty name", _doc({**Q, "name": ""}), "enum"),
    ("entry with a numeric name", _doc({**Q, "name": 5}), "enum"),
    ("invented name", _doc({**Q, "name": "flashcards"}), "enum"),
    ("wrong capitals", _doc({**Q, "name": "Question Set"}), "enum"),
    ("the old PRD phrase as a name", _doc({**TW, "name": "drag-the-words or drag-and-drop / ordering"}), "enum"),
    ("a machine name as the name", _doc({**Q, "name": "H5P.QuestionSet"}), "enum"),
    ("question set listed twice", _doc(Q, Q), "maxContains"),
    ("drag-the-words listed twice", _doc(TW, TW), "maxContains"),
    ("machine name of another type", _doc({**Q, "machine_name": "H5P.DragText"}), "const"),
    ("machine name in lower case", _doc({**Q, "machine_name": "h5p.questionset"}), "const"),
    ("wrong version", _doc({**Q, "version": "1.21.15"}), "const"),
    ("version with a v prefix", _doc({**Q, "version": "v1.21.14"}), "const"),
    ("version is a number", _doc({**Q, "version": 1.21}), "const"),
    ("drag-the-words with the drag-and-drop version", _doc({**TW, "version": DD["version"]}), "const"),
    ("drag-and-drop with the drag-the-words version", _doc({**DD, "version": TW["version"]}), "const"),
    ("drag-the-words with the drag-and-drop library", _doc({**TW, "machine_name": DD["machine_name"]}), "const"),
]  # fmt: skip


@pytest.mark.parametrize(
    ("document", "keyword"), [pytest.param(d, k, id=n) for n, d, k in CASES]
)
def test_invalid_content_type_list_is_rejected(
    validator: Draft202012Validator, document: Doc, keyword: str
) -> None:
    assert keyword in {e.validator for e in validator.iter_errors(document)}


@pytest.mark.parametrize("field", ["schema", "content_types"])
def test_missing_root_field_is_rejected(
    validator: Draft202012Validator, allow_list: Doc, field: str
) -> None:
    broken = {k: v for k, v in allow_list.items() if k != field}
    assert "required" in {e.validator for e in validator.iter_errors(broken)}


@pytest.mark.parametrize("name", list(PINNED))
def test_a_list_with_one_pinned_type_is_valid(
    validator: Draft202012Validator, name: str
) -> None:
    # The list need not hold all five types.
    assert [e.message for e in validator.iter_errors(_doc(_entry(name)))] == []


def test_unknown_fields_are_accepted(
    validator: Draft202012Validator, allow_list: Doc
) -> None:
    extended = {**allow_list, "future": 1}
    extended["content_types"] = [{**_entry("question set"), "future": 1}]
    assert [e.message for e in validator.iter_errors(extended)] == []


# --- cues are B6's, and the text keeps what is still open ----------------------------------


def test_no_cue_key_is_defined_and_cues_are_left_to_b6(
    schema: Doc, allow_list: Doc, text: str
) -> None:
    for document in (schema, allow_list):
        words = _walk(document)
        assert not {w for w in words if w.lower() in {"cue", "cues", "ref"}}
    assert "defines no second format" in text  # cues.json is B6's


def test_text_pins_the_types_and_keeps_only_the_open_decisions_still_open(
    text: str,
) -> None:
    prose = " ".join(text.split())  # line wrapping in the Markdown must not matter
    rows = [line for line in text.splitlines() if line.startswith("| ")]
    for name in PINNED:
        row = [r for r in rows if r.startswith(f"| {name} |")]
        assert len(row) == 1 and "to verify in the lab" not in row[0], name
    for phrase in (
        "OPEN DECISION: the `ref` kinds",
        "OPEN DECISION: several practice items",
        "OPEN DECISION: video checkpoint placement",
        "Practice is optional",
        "never graded",
        "h5p_files_not_checked",
        "Each practice item uses one of them",
        "Ordering is not a separate content type",
        "optional entry",
        "/contract-change",
    ):
        assert phrase in prose, phrase
    # The lab check settled these two (guide, 2026-11-11), and the text no longer lists them.
    for phrase in (
        "OPEN DECISION: library versions",
        "OPEN DECISION: the second row",
        "cannot be frozen",
    ):
        assert phrase not in prose, phrase


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
