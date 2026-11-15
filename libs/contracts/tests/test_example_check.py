"""The example engine (PRD B.0 rule 1, E1 "Contract" level), tested on its own.

Each test builds a small `contracts/` tree in a temporary folder and calls
`check_schema_examples` directly. The repository-wide tool that uses the engine has its own
end-to-end tests in `test_validate_examples.py`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from contracts.example_check import SchemaCheck, check_schema_examples

from .example_helpers import (
    GOOD,
    PREFIX,
    SCHEMA,
    THING,
    Files,
    make_tree,
    with_ref,
)


def rel(name: str) -> str:
    return f"{PREFIX}thing.v1/{name}"


def check(
    tmp_path: Path, examples: Files, schema: dict[str, Any] | str = SCHEMA
) -> SchemaCheck:
    contracts = make_tree(tmp_path, examples, schema=schema)
    folder = contracts / "examples" / "thing.v1"
    pairs = [(folder / name, rel(name)) for name in examples]
    return check_schema_examples(contracts / "thing.v1.schema.json", THING, pairs)


@pytest.mark.parametrize(
    ("name", "content"),
    [
        ("a.json", '{"name": "x", "count": 2, "start_date": "2026-01-12"}'),
        ("b.yaml", "name: x\ncount: 2\nstart_date: '2026-01-12'\n"),
        ("c.yml", "name: x\nitems: [a, b]\n"),
        (
            "d.json",
            '{"name": "x", "extra": 1}',
        ),  # unknown fields: the schema allows them
    ],
)
def test_check_valid_example_passes(tmp_path: Path, name: str, content: str) -> None:
    assert check(tmp_path, {name: content}) == SchemaCheck(passed=(rel(name),))


@pytest.mark.parametrize(
    ("name", "content", "needles"),
    [
        ("bad.json", '{"name": "x", "count": "two"}', ["count", "[type]"]),
        ("bad.yaml", "count: 3\n", ["(document)", "[required]"]),
        # PyYAML turns an unquoted date into a date object; it must not be turned back into text.
        ("bad.yaml", "name: x\nstart_date: 2026-01-12\n", ["start_date"]),
        ("bad.json", '{"name": "x", "start_date": "2026-02-31"}', ["[format]"]),
    ],
    ids=["wrong-type", "missing-required", "unquoted-yaml-date", "impossible-date"],
)
def test_check_invalid_example_is_one_violation_with_its_place_and_keyword(
    tmp_path: Path, name: str, content: str, needles: list[str]
) -> None:
    result = check(tmp_path, {name: content})
    (problem,) = result.problems
    assert problem.code == "schema_violation"
    assert (problem.example, problem.schema) == (rel(name), THING)
    assert problem.hint
    for needle in needles:
        assert needle in problem.message
    assert (result.passed, result.failed) == ((), (rel(name),))


@pytest.mark.parametrize(
    ("document", "places"),
    [
        (
            '{"count": "two", "items": ["a", 1, "b", 2]}',
            ["(document)", "count", "items[1]", "items[3]"],
        ),
        # List positions compare as numbers: items[2] comes before items[10].
        (
            '{"name": "x", "items": ["a", "b", 1, "c", "d", "e", "f", "g", "h", "i", 2]}',
            ["items[2]", "items[10]"],
        ),
    ],
    ids=["by-place", "by-number"],
)
def test_check_reports_every_error_in_a_fixed_order(
    tmp_path: Path, document: str, places: list[str]
) -> None:
    result = check(tmp_path, {"bad.json": document})
    assert {p.code for p in result.problems} == {"schema_violation"}
    assert [p.message.split(":")[0] for p in result.problems] == places


def test_check_one_failure_among_passing_examples(tmp_path: Path) -> None:
    result = check(
        tmp_path, {"a.json": GOOD, "b.json": '{"count": 1}', "c.yaml": "name: c\n"}
    )
    assert result.passed == (rel("a.json"), rel("c.yaml"))
    assert result.failed == (rel("b.json"),)


@pytest.mark.parametrize(
    ("name", "content"),
    [
        ("a.json", '{"name": '),
        ("a.yaml", "name: [x\n"),
        ("a.yaml", "name: x\n---\nname: y\n"),
        ("a.json", b'{"name": "\xff"}'),
        ("a.yaml", "name: x\nstart_date: 2026-02-31\n"),
    ],
    ids=["bad-json", "bad-yaml", "two-yaml-documents", "not-utf8", "impossible-date"],
)
def test_check_unreadable_example_is_an_error(
    tmp_path: Path, name: str, content: str | bytes
) -> None:
    result = check(tmp_path, {name: content})
    (problem,) = result.problems
    assert (problem.code, problem.example, problem.schema) == (
        "unreadable_example",
        rel(name),
        THING,
    )
    assert (result.passed, result.failed) == ((), (rel(name),))


@pytest.mark.parametrize(
    ("schema", "schema_code", "reason"),
    [
        (
            {"$schema": "https://json-schema.org/draft/2020-12/schema", "type": 5},
            "invalid_schema",
            "",
        ),
        ("{not json", "unreadable_schema", ""),
        (with_ref("#/$defs/missing"), "unresolvable_reference", "missing"),
        (with_ref("other.schema.json"), "unresolvable_reference", "other.schema.json"),
    ],
    ids=["invalid-schema", "unreadable-schema", "dangling-local-ref", "external-ref"],
)
def test_check_examples_of_an_unusable_schema_are_not_validated(
    tmp_path: Path, schema: dict[str, Any] | str, schema_code: str, reason: str
) -> None:
    # Both examples are valid. A reference is only reached by b.json, after a.json has already
    # passed: a.json must not stay in `passed`, and nothing is reported as failed.
    result = check(
        tmp_path, {"a.json": GOOD, "b.json": '{"name": "b", "link": "x"}'}, schema
    )
    assert [p.code for p in result.problems] == [schema_code] + [
        "example_not_validated"
    ] * 2
    first = result.problems[0]
    assert (first.schema, first.example) == (THING, None)
    assert reason in first.message
    assert all(p.message and p.hint for p in result.problems)
    assert [(p.example, p.schema) for p in result.problems[1:]] == [
        (rel("a.json"), THING),
        (rel("b.json"), THING),
    ]
    assert (result.passed, result.failed) == ((), ())


def test_check_broken_schema_without_examples_reports_only_the_schema(
    tmp_path: Path,
) -> None:
    result = check(tmp_path, {}, "{not json")
    assert [p.code for p in result.problems] == ["unreadable_schema"]
    assert (result.passed, result.failed) == ((), ())
