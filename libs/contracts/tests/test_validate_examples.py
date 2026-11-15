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


@pytest.mark.parametrize(
    ("name", "content", "expected"),
    [
        ("bad.yaml", "count: 3\n", "required"),
        # PyYAML turns an unquoted date into a date object; it must not be turned back into text.
        ("bad.yaml", "name: x\nstart_date: 2026-01-12\n", "start_date"),
        ("bad.json", '{"name": "x", "start_date": "2026-02-31"}', "[format]"),
    ],
    ids=["yaml-missing-required", "unquoted-yaml-date", "impossible-quoted-date"],
)
def test_invalid_example_is_one_schema_violation(
    tmp_path: Path, name: str, content: str, expected: str
) -> None:
    problem = only(validate_all(make_tree(tmp_path, {name: content})))
    assert problem.code == "schema_violation"
    assert expected in problem.message


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


# --- missing examples -----------------------------------------------------------------------


@pytest.mark.parametrize(
    "layout", ["no-folder", "empty-folder", "only-a-supporting-file"]
)
def test_schema_without_a_top_level_example_is_an_error(
    tmp_path: Path, layout: str
) -> None:
    # Subfolders hold supporting files and are ignored by design, even a .json that breaks the
    # schema: with only those, there is still no example to validate.
    supporting: dict[str, str | bytes] = {
        "weeks/01.md": "# hi\n",
        "weeks/02.json": "{}",
    }
    files = supporting if layout == "only-a-supporting-file" else None
    contracts = make_tree(tmp_path, files)
    if layout == "empty-folder":
        (contracts / "examples" / EXAMPLE_DIR).mkdir()
    problem = only(validate_all(contracts))
    assert problem.code == "missing_example"
    assert problem.schema == "contracts/thing.v1.schema.json"


def test_no_schemas_at_all_is_an_error(tmp_path: Path) -> None:
    contracts = make_tree(tmp_path, schema=None)
    assert codes(validate_all(contracts)) == ["no_schemas"]
    assert main(["--contracts-dir", str(contracts)]) == 1


def test_missing_contracts_folder_exits_two(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["--contracts-dir", str(tmp_path / "nope")]) == 2
    assert "nope" in capsys.readouterr().err


def test_non_schema_files_in_contracts_are_not_applicable(tmp_path: Path) -> None:
    contracts = make_tree(tmp_path, {"a.json": '{"name": "a"}'})
    (contracts / "CLAUDE.md").write_text("# notes\n", encoding="utf-8")
    (contracts / "lti-launch.v1.md").write_text("# B3\n", encoding="utf-8")
    assert validate_all(contracts).ok


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
    assert codes(report) == [schema_code] + ["example_not_validated"] * 2
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


@pytest.mark.parametrize(
    "ref", ["#/$defs/missing", "other.schema.json"], ids=["dangling-local", "external"]
)
def test_unresolvable_reference_makes_the_schema_unusable(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], ref: str
) -> None:
    # The reference is only reached by b.json, after a.json has already passed. a.json must not
    # stay in `passed`, and nothing is reported as failed.
    schema = {**SCHEMA, "properties": {**SCHEMA["properties"], "link": {"$ref": ref}}}
    contracts = make_tree(
        tmp_path,
        {"a.json": '{"name": "a"}', "b.json": '{"name": "b", "link": "x"}'},
        schema=schema,
    )
    report = validate_all(contracts)
    schema_rel = "contracts/thing.v1.schema.json"
    assert codes(report) == ["unresolvable_reference"] + ["example_not_validated"] * 2
    first = report.problems[0]
    assert first.schema == schema_rel
    assert first.example is None
    assert [(p.example, p.schema) for p in report.problems[1:]] == [
        ("contracts/examples/thing.v1/a.json", schema_rel),
        ("contracts/examples/thing.v1/b.json", schema_rel),
    ]
    assert report.example_count == 2
    assert report.passed == ()
    assert report.failed == ()

    assert main(["--contracts-dir", str(contracts)]) == 1
    captured = capsys.readouterr()
    assert "OK " not in captured.out
    assert f"FAIL {schema_rel}" in captured.err
    assert "next:" in captured.err
    assert "2 examples found, 1 schemas: 0 passed, 0 failed, 2 not validated" in (
        captured.out
    )


# --- example layouts ------------------------------------------------------------------------
#
# Folder: contracts/examples/<stem>/*.json. Flat: contracts/examples/<stem>.<suffix>.json.

PREFIX = "contracts/examples/"
THING = "contracts/thing.v1.schema.json"


def add_flat(contracts: Path, name: str, content: str) -> None:
    (contracts / "examples" / name).write_text(content, encoding="utf-8")


def test_folder_only_layout(tmp_path: Path) -> None:
    report = validate_all(make_tree(tmp_path, {"example.json": '{"name": "a"}'}))
    assert report.problems == ()
    assert report.passed == ((f"{PREFIX}thing.v1/example.json", THING),)


def test_flat_only_layout(tmp_path: Path) -> None:
    contracts = make_tree(tmp_path)
    add_flat(contracts, "thing.v1.meta-local.json", '{"name": "a"}')
    add_flat(contracts, "thing.v1.more.yaml", "name: b\n")
    report = validate_all(contracts)
    assert report.problems == ()
    assert report.passed == (
        (f"{PREFIX}thing.v1.meta-local.json", THING),
        (f"{PREFIX}thing.v1.more.yaml", THING),
    )


def test_both_layouts_together_in_a_fixed_order(tmp_path: Path) -> None:
    contracts = make_tree(
        tmp_path, {"z.json": '{"name": "z"}', "a.json": '{"name": "a"}'}
    )
    add_flat(contracts, "thing.v1.b.json", '{"name": "b"}')
    add_flat(contracts, "thing.v1.a.json", '{"name": "c"}')
    expected = (
        (f"{PREFIX}thing.v1/a.json", THING),
        (f"{PREFIX}thing.v1/z.json", THING),
        (f"{PREFIX}thing.v1.a.json", THING),
        (f"{PREFIX}thing.v1.b.json", THING),
    )
    assert validate_all(contracts).passed == expected
    assert validate_all(contracts).passed == expected  # the same on every run


def test_invalid_flat_example_names_its_path_and_schema(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    contracts = make_tree(tmp_path)
    add_flat(contracts, "thing.v1.bad.json", '{"count": "two"}')
    problems = validate_all(contracts).problems
    assert {p.code for p in problems} == {"schema_violation"}
    assert {(p.example, p.schema) for p in problems} == {
        (f"{PREFIX}thing.v1.bad.json", THING)
    }
    assert main(["--contracts-dir", str(contracts)]) == 1
    assert f"FAIL {PREFIX}thing.v1.bad.json (schema {THING})" in capsys.readouterr().err


def test_no_example_in_either_layout_is_a_missing_example(tmp_path: Path) -> None:
    contracts = make_tree(tmp_path)
    # Not examples of thing.v1: a different schema's flat file, a name with no suffix, a file of
    # another extension, a file in a subfolder of its folder, and a flat-named file in a subfolder
    # of contracts/examples (supporting files are ignored by design).
    add_flat(contracts, "other.v1.x.json", "{}")
    add_flat(contracts, "thing.v1.json", "{}")
    add_flat(contracts, "thing.v1.x.txt", "{}")
    (contracts / "examples" / "thing.v1" / "weeks").mkdir(parents=True)
    (contracts / "examples" / "thing.v1" / "weeks" / "01.json").write_text("{}")
    (contracts / "examples" / "sub").mkdir()
    (contracts / "examples" / "sub" / "thing.v1.x.json").write_text("{}")
    problem = only(validate_all(contracts))
    assert problem.code == "missing_example"
    assert problem.schema == THING


def test_a_version_does_not_consume_the_examples_of_another(tmp_path: Path) -> None:
    contracts = make_tree(tmp_path, {"a.json": '{"name": "a"}'})
    (contracts / "thing.v10.schema.json").write_text(
        json.dumps({**SCHEMA, "required": ["other"]}), encoding="utf-8"
    )
    add_flat(contracts, "thing.v10.x.json", '{"other": 1}')
    add_flat(contracts, "thing.v1.x.json", '{"name": "b"}')
    other = contracts / "examples" / "thing.v10"
    other.mkdir()
    (other / "a.json").write_text('{"other": 1}', encoding="utf-8")
    report = validate_all(contracts)
    assert report.problems == ()
    assert set(report.passed) == {
        (f"{PREFIX}thing.v1/a.json", THING),
        (f"{PREFIX}thing.v1.x.json", THING),
        (f"{PREFIX}thing.v10.x.json", "contracts/thing.v10.schema.json"),
        (f"{PREFIX}thing.v10/a.json", "contracts/thing.v10.schema.json"),
    }


# --- misnamed schemas -----------------------------------------------------------------------


@pytest.mark.parametrize(
    "name", ["thing.schema.json", "thing.v0.schema.json", "Thing.v1.schema.json"]
)
def test_misnamed_schema_is_reported_with_its_path(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], name: str
) -> None:
    contracts = make_tree(tmp_path, {"a.json": '{"name": "a"}'})
    (contracts / name).write_text(json.dumps(SCHEMA), encoding="utf-8")
    problem = only(validate_all(contracts))
    assert problem.code == "misnamed_schema"
    assert problem.schema == f"contracts/{name}"
    assert main(["--contracts-dir", str(contracts)]) == 1
    err = capsys.readouterr().err
    assert f"contracts/{name}" in err
    assert "next: Rename it to <name>.v<N>.schema.json" in err


@pytest.mark.parametrize(
    ("name", "folder"),
    [
        ("thing.schema.json", "thing"),
        ("thing.v1.extra.schema.json", "thing.v1.extra"),
        ("thing.v1.0.schema.json", "thing.v1.0"),
    ],
)
def test_misnamed_schema_is_not_treated_as_valid_because_a_folder_matches(
    tmp_path: Path, name: str, folder: str
) -> None:
    # The misnamed schema has an examples folder named after its stem, and the example in it
    # breaks the schema. It must not be validated, or counted, as if the schema were valid.
    contracts = make_tree(tmp_path, {"a.json": '{"name": "a"}'})
    (contracts / name).write_text(json.dumps(SCHEMA), encoding="utf-8")
    (contracts / "examples" / folder).mkdir()
    (contracts / "examples" / folder / "bad.json").write_text("{}", encoding="utf-8")
    report = validate_all(contracts)
    assert codes(report) == ["misnamed_schema"]
    assert report.problems[0].schema == f"contracts/{name}"
    assert report.schema_count == 1  # only thing.v1
    assert report.example_count == 1
    assert report.passed == ((f"{PREFIX}thing.v1/a.json", THING),)
    assert report.failed == ()


def test_only_misnamed_schemas_never_succeed(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    contracts = make_tree(tmp_path, schema=SCHEMA, schema_file="thing.schema.json")
    report = validate_all(contracts)
    # "no schema files" and "misnamed schema files" stay different problems.
    assert codes(report) == ["misnamed_schema"]
    assert report.schema_count == 0
    assert main(["--contracts-dir", str(contracts)]) == 1
    assert "0 examples found, 0 schemas" in capsys.readouterr().out


# --- CLI ------------------------------------------------------------------------------------


@pytest.mark.parametrize("flag", ["--check", "--dry-run"])
def test_check_and_dry_run_give_the_same_result(tmp_path: Path, flag: str) -> None:
    good = make_tree(tmp_path / "good", {"a.json": '{"name": "a"}'})
    bad = make_tree(tmp_path / "bad", {"a.json": "{}"})
    assert main([flag, "--contracts-dir", str(good)]) == 0
    assert main([flag, "--contracts-dir", str(bad)]) == 1


@pytest.mark.parametrize(
    "broken", [False, True], ids=["real-repository", "broken-tree"]
)
def test_script_runs_as_ci_runs_it(tmp_path: Path, broken: bool) -> None:
    command = [sys.executable, str(SCRIPT)]
    if broken:
        command += ["--contracts-dir", str(make_tree(tmp_path, {"a.json": "{}"}))]
    result = subprocess.run(
        command, cwd=ROOT, capture_output=True, text=True, check=False
    )
    assert result.returncode == (1 if broken else 0), result.stdout + result.stderr
    if broken:
        assert "contracts/examples/thing.v1/a.json" in result.stderr
        return
    # Without --contracts-dir the script checks the repository's own contracts, as CI does.
    expected = real_schemas()
    count = sum(len(examples) for examples in expected.values())
    for schema, examples in expected.items():
        for example in examples:
            assert f"OK {example} (schema {schema})" in result.stdout
    assert f"OK {B1_EXAMPLE}" in result.stdout
    assert (
        f"{count} examples found, {len(expected)} schemas: "
        f"{count} passed, 0 failed, 0 not validated" in result.stdout
    )
