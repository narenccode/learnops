"""Repository-wide contract-example validator (PRD B.0 rule 1, E1 "Contract" level).

Each test builds a small `contracts/` tree in a temporary folder, except the tests that check the
real repository. Every failure case asserts the problem code, so a case cannot pass for the wrong
reason, and checks that the message names the example and the schema involved.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from contracts.validate_examples import (
    ExampleReport,
    Problem,
    discover,
    main,
    validate_all,
)

ROOT = Path(__file__).resolve().parents[3]
REAL_CONTRACTS = ROOT / "contracts"
SCRIPT = ROOT / "libs" / "contracts" / "validate_examples.py"

# A small schema with a required string, an integer and an ISO date, like B1's start_date.
SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "required": ["name"],
    "properties": {
        "name": {"type": "string"},
        "count": {"type": "integer"},
        "start_date": {"type": ["string", "null"], "format": "date"},
        "items": {"type": "array", "items": {"type": "string"}},
    },
}
SCHEMA_FILE = "thing.v1.schema.json"
EXAMPLE_DIR = "thing.v1"


def make_tree(
    tmp_path: Path,
    examples: dict[str, str | bytes] | None = None,
    *,
    schema: dict[str, Any] | str | None = SCHEMA,
    schema_file: str = SCHEMA_FILE,
    example_dir: str = EXAMPLE_DIR,
) -> Path:
    """A contracts folder with one schema and the given example files (path -> content)."""
    contracts = tmp_path / "contracts"
    (contracts / "examples").mkdir(parents=True)
    if schema is not None:
        text = schema if isinstance(schema, str) else json.dumps(schema)
        (contracts / schema_file).write_text(text, encoding="utf-8")
    for rel, content in (examples or {}).items():
        target = contracts / "examples" / example_dir / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            target.write_bytes(content)
        else:
            target.write_text(content, encoding="utf-8")
    return contracts


def codes(report: ExampleReport) -> list[str]:
    return [p.code for p in report.problems]


def only(report: ExampleReport) -> Problem:
    assert len(report.problems) == 1, [(p.code, p.message) for p in report.problems]
    return report.problems[0]


# --- the real repository --------------------------------------------------------------------
#
# Other contracts land on their own branches, so these tests read what is checked out instead of
# naming every contract. The listing is done here, by hand, so it does not reuse the code under
# test. B1 is on main and must always be found.

B1_EXAMPLE = "contracts/examples/course-package.v1/course.yaml"


def real_schemas() -> dict[str, list[str]]:
    """Each real schema's path -> its top-level JSON/YAML examples, all repository-relative."""
    found: dict[str, list[str]] = {}
    for schema in sorted(REAL_CONTRACTS.glob("*.schema.json")):
        folder = REAL_CONTRACTS / "examples" / schema.name.removesuffix(".schema.json")
        examples = sorted(
            p.relative_to(ROOT).as_posix()
            for p in folder.glob("*")
            if p.is_file() and p.suffix.lower() in {".json", ".yaml", ".yml"}
        )
        found[schema.relative_to(ROOT).as_posix()] = examples
    return found


def test_real_repository_examples_all_pass() -> None:
    expected = real_schemas()
    report = validate_all(REAL_CONTRACTS)
    assert report.problems == ()
    assert report.ok
    assert set(report.passed) == {
        (example, schema)
        for schema, examples in expected.items()
        for example in examples
    }
    assert B1_EXAMPLE in {example for example, _ in report.passed}
    assert all(expected.values()), expected  # every schema has at least one example


def test_real_repository_reports_b1_body_files_as_supporting() -> None:
    report = validate_all(REAL_CONTRACTS)
    assert "contracts/examples/course-package.v1/weeks/01-guide.md" in report.supporting
    assert all("/weeks/" in path for path in report.supporting)


def test_discover_pairs_each_real_schema_with_its_example_folder() -> None:
    cases = discover(REAL_CONTRACTS)
    pairs = {(c.schema_path.name, c.example_dir.name) for c in cases}
    expected = {
        (Path(schema).name, Path(schema).name.removesuffix(".schema.json"))
        for schema in real_schemas()
    }
    assert pairs == expected
    assert ("course-package.v1.schema.json", "course-package.v1") in pairs
    assert all(
        c.example_dir == REAL_CONTRACTS / "examples" / c.example_dir.name for c in cases
    )


def test_main_on_real_repository_exits_zero(capsys: pytest.CaptureFixture[str]) -> None:
    expected = real_schemas()
    count = sum(len(examples) for examples in expected.values())
    assert main([]) == 0
    out = capsys.readouterr().out
    for schema, examples in expected.items():
        for example in examples:
            assert f"OK {example} (schema {schema})" in out
    assert f"OK {B1_EXAMPLE}" in out
    assert (
        f"{count} examples found, {len(expected)} schemas: "
        f"{count} passed, 0 failed, 0 not validated" in out
    )


# --- several schemas ------------------------------------------------------------------------


def test_several_schemas_are_each_paired_and_validated(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # The real repository may hold a single contract; this keeps the multi-schema case covered.
    contracts = make_tree(tmp_path, {"a.json": '{"name": "a"}', "b.yaml": "name: b\n"})
    (contracts / "other-thing.v2.schema.json").write_text(
        json.dumps(SCHEMA), encoding="utf-8"
    )
    other = contracts / "examples" / "other-thing.v2"
    other.mkdir()
    (other / "c.json").write_text('{"name": "c"}', encoding="utf-8")

    pairs = {(c.schema_path.name, c.example_dir.name) for c in discover(contracts)}
    assert pairs == {
        ("other-thing.v2.schema.json", "other-thing.v2"),
        ("thing.v1.schema.json", "thing.v1"),
    }
    report = validate_all(contracts)
    assert report.problems == ()
    assert set(report.passed) == {
        (
            "contracts/examples/other-thing.v2/c.json",
            "contracts/other-thing.v2.schema.json",
        ),
        ("contracts/examples/thing.v1/a.json", "contracts/thing.v1.schema.json"),
        ("contracts/examples/thing.v1/b.yaml", "contracts/thing.v1.schema.json"),
    }
    assert main(["--contracts-dir", str(contracts)]) == 0
    assert (
        "3 examples found, 2 schemas: 3 passed, 0 failed, 0 not validated"
        in capsys.readouterr().out
    )


# --- valid examples -------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("name", "content"),
    [
        ("a.json", '{"name": "x", "count": 2, "start_date": "2026-01-12"}'),
        ("b.yaml", "name: x\ncount: 2\nstart_date: '2026-01-12'\n"),
        ("c.yml", "name: x\nitems: [a, b]\n"),
    ],
)
def test_valid_example_passes(tmp_path: Path, name: str, content: str) -> None:
    report = validate_all(make_tree(tmp_path, {name: content}))
    assert report.problems == ()
    assert report.passed == (
        (f"contracts/examples/thing.v1/{name}", "contracts/thing.v1.schema.json"),
    )


def test_unknown_fields_are_accepted_when_schema_allows(tmp_path: Path) -> None:
    report = validate_all(make_tree(tmp_path, {"a.json": '{"name": "x", "extra": 1}'}))
    assert report.ok


# --- invalid examples -----------------------------------------------------------------------


def test_invalid_json_example_names_example_schema_place_and_keyword(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    contracts = make_tree(tmp_path, {"bad.json": '{"name": "x", "count": "two"}'})
    assert main(["--contracts-dir", str(contracts)]) == 1
    err = capsys.readouterr().err
    assert "contracts/examples/thing.v1/bad.json" in err
    assert "contracts/thing.v1.schema.json" in err
    assert "count" in err
    assert "[type]" in err
    problem = only(validate_all(contracts))
    assert problem.code == "schema_violation"
    assert problem.example == "contracts/examples/thing.v1/bad.json"
    assert problem.schema == "contracts/thing.v1.schema.json"


def test_invalid_yaml_example_fails(tmp_path: Path) -> None:
    report = validate_all(make_tree(tmp_path, {"bad.yaml": "count: 3\n"}))
    problem = only(report)
    assert problem.code == "schema_violation"
    assert "required" in problem.message


def test_unquoted_yaml_date_is_rejected_as_parsed(tmp_path: Path) -> None:
    # PyYAML turns an unquoted date into a date object; it must not be turned back into text.
    report = validate_all(
        make_tree(tmp_path, {"bad.yaml": "name: x\nstart_date: 2026-01-12\n"})
    )
    problem = only(report)
    assert problem.code == "schema_violation"
    assert "start_date" in problem.message


def test_impossible_quoted_date_is_rejected_by_format(tmp_path: Path) -> None:
    report = validate_all(
        make_tree(tmp_path, {"bad.json": '{"name": "x", "start_date": "2026-02-31"}'})
    )
    problem = only(report)
    assert problem.code == "schema_violation"
    assert "[format]" in problem.message


def test_every_error_in_one_example_is_reported_in_order(tmp_path: Path) -> None:
    doc = '{"count": "two", "items": ["a", 1, "b", 2]}'
    report = validate_all(make_tree(tmp_path, {"bad.json": doc}))
    assert codes(report) == ["schema_violation"] * 4
    places = [p.message.split(":")[0] for p in report.problems]
    assert places == ["(document)", "count", "items[1]", "items[3]"]


def test_one_failure_among_passing_examples_still_fails(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    contracts = make_tree(
        tmp_path,
        {"a.json": '{"name": "a"}', "b.json": '{"count": 1}', "c.yaml": "name: c\n"},
    )
    assert main(["--contracts-dir", str(contracts)]) == 1
    out = capsys.readouterr().out
    assert "OK contracts/examples/thing.v1/a.json" in out
    assert "OK contracts/examples/thing.v1/c.yaml" in out
    assert "3 examples found, 1 schemas: 2 passed, 1 failed, 0 not validated" in out


# --- missing and orphan examples ------------------------------------------------------------


def test_schema_without_example_folder_is_an_error(tmp_path: Path) -> None:
    problem = only(validate_all(make_tree(tmp_path)))
    assert problem.code == "missing_example"
    assert problem.schema == "contracts/thing.v1.schema.json"


def test_example_folder_without_top_level_example_is_an_error(tmp_path: Path) -> None:
    # Only a supporting file in a subfolder: there is still no example to validate.
    report = validate_all(make_tree(tmp_path, {"weeks/01.md": "# hi\n"}))
    assert codes(report) == ["missing_example"]


def test_empty_example_folder_is_an_error(tmp_path: Path) -> None:
    contracts = make_tree(tmp_path)
    (contracts / "examples" / EXAMPLE_DIR).mkdir()
    assert codes(validate_all(contracts)) == ["missing_example"]


def test_example_folder_without_schema_is_an_orphan(tmp_path: Path) -> None:
    contracts = make_tree(tmp_path, {"a.json": '{"name": "a"}'})
    orphan = contracts / "examples" / "other.v1"
    orphan.mkdir()
    (orphan / "x.json").write_text("{}", encoding="utf-8")
    problem = only(validate_all(contracts))
    assert problem.code == "orphan_example"
    assert problem.example == "contracts/examples/other.v1"


def test_stray_file_in_examples_folder_is_an_orphan(tmp_path: Path) -> None:
    contracts = make_tree(tmp_path, {"a.json": '{"name": "a"}'})
    (contracts / "examples" / "loose.json").write_text("{}", encoding="utf-8")
    assert codes(validate_all(contracts)) == ["orphan_example"]


def test_examples_in_an_orphan_folder_are_counted_but_not_classified(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    contracts = make_tree(tmp_path, {"a.json": '{"name": "a"}'})
    orphan = contracts / "examples" / "other.v1"
    (orphan / "weeks").mkdir(parents=True)
    (orphan / "x.json").write_text('{"name": "x"}', encoding="utf-8")
    (orphan / "y.yaml").write_text("name: y\n", encoding="utf-8")
    # A file in a subfolder is a supporting file, even with an example suffix: not counted.
    (orphan / "weeks" / "z.json").write_text("{}", encoding="utf-8")

    report = validate_all(contracts)
    assert report.example_count == 3
    problem = only(report)
    assert problem.code == "orphan_example"
    assert problem.example == "contracts/examples/other.v1"
    assert report.passed == (
        ("contracts/examples/thing.v1/a.json", "contracts/thing.v1.schema.json"),
    )
    assert report.failed == ()
    assert main(["--contracts-dir", str(contracts)]) == 1
    out = capsys.readouterr().out
    assert "3 examples found, 1 schemas: 1 passed, 0 failed, 2 not validated" in out


def test_loose_example_files_are_counted_but_not_classified(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    contracts = make_tree(tmp_path, {"a.json": '{"name": "a"}'})
    examples = contracts / "examples"
    (examples / "b-loose.json").write_text('{"name": "b"}', encoding="utf-8")
    (examples / "c-loose.yaml").write_text("name: c\n", encoding="utf-8")
    # Not an example type: still an orphan, but not counted as an example.
    (examples / "d-notes.txt").write_text("hi\n", encoding="utf-8")

    report = validate_all(contracts)
    assert report.example_count == 3
    assert codes(report) == ["orphan_example"] * 3
    assert [p.example for p in report.problems] == [
        "contracts/examples/b-loose.json",
        "contracts/examples/c-loose.yaml",
        "contracts/examples/d-notes.txt",
    ]
    assert report.passed == (
        ("contracts/examples/thing.v1/a.json", "contracts/thing.v1.schema.json"),
    )
    assert report.failed == ()
    assert main(["--contracts-dir", str(contracts)]) == 1
    out = capsys.readouterr().out
    assert "3 examples found, 1 schemas: 1 passed, 0 failed, 2 not validated" in out


def test_no_schemas_at_all_is_an_error(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    contracts = make_tree(tmp_path, schema=None)
    assert codes(validate_all(contracts)) == ["no_schemas"]
    assert main(["--contracts-dir", str(contracts)]) == 1


def test_missing_contracts_folder_exits_two(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["--contracts-dir", str(tmp_path / "nope")]) == 2
    assert "nope" in capsys.readouterr().err


# --- names and file types -------------------------------------------------------------------


@pytest.mark.parametrize(
    "name", ["thing.schema.json", "Thing.v1.schema.json", "thing.v0.schema.json"]
)
def test_unversioned_or_badly_named_schema_is_an_error(
    tmp_path: Path, name: str
) -> None:
    contracts = make_tree(tmp_path, schema_file=name)
    assert codes(validate_all(contracts)) == ["unversioned_schema"]


def test_non_schema_files_in_contracts_are_not_applicable(tmp_path: Path) -> None:
    contracts = make_tree(tmp_path, {"a.json": '{"name": "a"}'})
    (contracts / "CLAUDE.md").write_text("# notes\n", encoding="utf-8")
    (contracts / "lti-launch.v1.md").write_text("# B3\n", encoding="utf-8")
    assert validate_all(contracts).ok


def test_unsupported_top_level_example_type_is_an_error(tmp_path: Path) -> None:
    report = validate_all(
        make_tree(tmp_path, {"a.json": '{"name": "a"}', "notes.txt": "hi\n"})
    )
    problem = only(report)
    assert problem.code == "unsupported_example"
    assert problem.example == "contracts/examples/thing.v1/notes.txt"


# --- unreadable files -----------------------------------------------------------------------


@pytest.mark.parametrize(
    ("name", "content"),
    [
        ("a.json", '{"name": '),
        ("a.yaml", "name: [x\n"),
        ("a.yaml", "name: x\n---\nname: y\n"),
        ("a.json", b'{"name": "\xff"}'),
        ("a.yaml", "name: x\nstart_date: 2026-02-31\n"),
    ],
    ids=[
        "bad-json",
        "bad-yaml",
        "two-yaml-documents",
        "not-utf8",
        "impossible-yaml-date",
    ],
)
def test_unreadable_example_is_an_error(
    tmp_path: Path, name: str, content: str | bytes
) -> None:
    problem = only(validate_all(make_tree(tmp_path, {name: content})))
    assert problem.code == "unreadable_example"
    assert problem.example == f"contracts/examples/thing.v1/{name}"


@pytest.mark.parametrize(
    ("name", "content"),
    [
        ("a.json", '{"name": "x", "name": "y"}'),
        ("a.yaml", "name: x\nname: y\n"),
    ],
)
def test_duplicate_keys_are_an_error(tmp_path: Path, name: str, content: str) -> None:
    problem = only(validate_all(make_tree(tmp_path, {name: content})))
    assert problem.code == "unreadable_example"
    assert "name" in problem.message


@pytest.mark.parametrize("constant", ["NaN", "Infinity", "-Infinity"])
def test_non_standard_json_constants_are_an_error(
    tmp_path: Path, constant: str
) -> None:
    # Python's json module accepts these by default; they are not JSON.
    doc = f'{{"name": "x", "count": {constant}}}'
    problem = only(validate_all(make_tree(tmp_path, {"a.json": doc})))
    assert problem.code == "unreadable_example"
    assert problem.example == "contracts/examples/thing.v1/a.json"
    assert f"non-standard JSON constant '{constant}'" in problem.message


def test_schema_that_is_not_json_is_an_error(tmp_path: Path) -> None:
    report = validate_all(make_tree(tmp_path, {"a.json": "{}"}, schema="{not json"))
    assert codes(report) == ["unreadable_schema", "example_not_validated"]


def test_schema_that_is_not_a_valid_schema_is_an_error(tmp_path: Path) -> None:
    broken = {"$schema": "https://json-schema.org/draft/2020-12/schema", "type": 5}
    report = validate_all(make_tree(tmp_path, {"a.json": "{}"}, schema=broken))
    assert codes(report) == ["invalid_schema", "example_not_validated"]


@pytest.mark.parametrize(
    ("schema", "schema_code"),
    [
        (
            {"$schema": "https://json-schema.org/draft/2020-12/schema", "type": 5},
            "invalid_schema",
        ),
        ("{not json", "unreadable_schema"),
    ],
    ids=["invalid-schema", "unreadable-schema"],
)
def test_examples_of_a_broken_schema_are_counted_but_not_validated(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    schema: dict[str, Any] | str,
    schema_code: str,
) -> None:
    # Both examples are valid; they are not validated, so they neither pass nor fail.
    contracts = make_tree(
        tmp_path, {"a.json": '{"name": "a"}', "b.yaml": "name: b\n"}, schema=schema
    )
    report = validate_all(contracts)
    assert codes(report) == [
        schema_code,
        "example_not_validated",
        "example_not_validated",
    ]
    assert [p.example for p in report.problems[1:]] == [
        "contracts/examples/thing.v1/a.json",
        "contracts/examples/thing.v1/b.yaml",
    ]
    assert report.example_count == 2
    assert report.passed == ()
    assert report.failed == ()
    assert main(["--contracts-dir", str(contracts)]) == 1
    out = capsys.readouterr().out
    assert "2 examples found, 1 schemas: 0 passed, 0 failed, 2 not validated" in out


# --- CLI ------------------------------------------------------------------------------------


@pytest.mark.parametrize("flag", ["--check", "--dry-run"])
def test_check_and_dry_run_give_the_same_result(
    tmp_path: Path, flag: str, capsys: pytest.CaptureFixture[str]
) -> None:
    good = make_tree(tmp_path / "good", {"a.json": '{"name": "a"}'})
    bad = make_tree(tmp_path / "bad", {"a.json": "{}"})
    assert main([flag, "--contracts-dir", str(good)]) == 0
    assert main([flag, "--contracts-dir", str(bad)]) == 1


def test_script_runs_as_ci_runs_it() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_script_exits_one_on_a_broken_tree(tmp_path: Path) -> None:
    contracts = make_tree(tmp_path, {"a.json": "{}"})
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--contracts-dir", str(contracts)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1, result.stdout + result.stderr
    assert "contracts/examples/thing.v1/a.json" in result.stderr
