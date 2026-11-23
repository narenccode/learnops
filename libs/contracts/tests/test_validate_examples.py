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

from contracts.example_check import Problem
from contracts.validate_examples import ExampleReport, discover, main, validate_all

from .example_helpers import (
    GOOD,
    PREFIX,
    SCHEMA,
    THING,
    Files,
    make_tree,
    with_ref,
)

ROOT = Path(__file__).resolve().parents[3]
REAL_CONTRACTS = ROOT / "contracts"
SCRIPT = ROOT / "libs" / "contracts" / "validate_examples.py"


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
EXTENSIONS = {"json", "yaml", "yml"}


def listed_examples(contracts: Path) -> dict[str, list[str]]:
    """Each schema's path -> its examples in both layouts, relative to the contracts' parent.

    Folder: `examples/<stem>/*`. Flat: `examples/<stem>.<one lower-case word>.<ext>`. The
    extension is matched in any case. Written by hand: it must not reuse the code under test."""
    examples = contracts / "examples"
    found: dict[str, list[str]] = {}
    for schema in sorted(contracts.glob("*.schema.json")):
        stem = schema.name.removesuffix(".schema.json")
        in_folder = sorted((examples / stem).glob("*"))
        flat = [
            p
            for p in sorted(examples.glob(f"{stem}.*"))
            if len(word := p.name.removeprefix(f"{stem}.").split(".")) == 2
            and word[0] == word[0].lower()
        ]
        files = [p for p in in_folder + flat if p.suffix.lower()[1:] in EXTENSIONS]
        found[schema.relative_to(contracts.parent).as_posix()] = [
            p.relative_to(contracts.parent).as_posix() for p in files if p.is_file()
        ]
    return found


def test_real_repository_examples_all_pass() -> None:
    expected = listed_examples(REAL_CONTRACTS)
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


# --- schemas and layouts --------------------------------------------------------------------


def test_several_schemas_are_each_paired_with_their_own_examples(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # The real repository may hold a single contract; this keeps the multi-schema case covered.
    # thing.v10 must not take the examples of thing.v1, in either layout.
    contracts = make_tree(
        tmp_path,
        {"a.json": GOOD, "b.yaml": "name: b\n"},
        raw={
            "thing.v1.x.json": '{"name": "b"}',
            "thing.v10.x.json": '{"other": 1}',
            "thing.v10/a.json": '{"other": 1}',
            "other-thing.v2/c.json": '{"name": "c"}',
        },
    )
    for name, extra in (("other-thing.v2", {}), ("thing.v10", {"required": ["other"]})):
        text = json.dumps({**SCHEMA, **extra})
        (contracts / f"{name}.schema.json").write_text(text, encoding="utf-8")

    pairs = {(c.schema_path.name, c.example_dir.name) for c in discover(contracts)}
    assert pairs == {
        ("other-thing.v2.schema.json", "other-thing.v2"),
        ("thing.v1.schema.json", "thing.v1"),
        ("thing.v10.schema.json", "thing.v10"),
    }
    report = validate_all(contracts)
    assert report.problems == ()
    v10 = "contracts/thing.v10.schema.json"
    assert set(report.passed) == {
        (f"{PREFIX}other-thing.v2/c.json", "contracts/other-thing.v2.schema.json"),
        (f"{PREFIX}thing.v1/a.json", THING),
        (f"{PREFIX}thing.v1/b.yaml", THING),
        (f"{PREFIX}thing.v1.x.json", THING),
        (f"{PREFIX}thing.v10/a.json", v10),
        (f"{PREFIX}thing.v10.x.json", v10),
    }
    assert main(["--contracts-dir", str(contracts)]) == 0
    assert (
        "6 examples found, 3 schemas: 6 passed, 0 failed, 0 not validated"
        in capsys.readouterr().out
    )


@pytest.mark.parametrize(
    ("folder", "flat", "expected"),
    [
        ({"example.json": GOOD}, {}, ["thing.v1/example.json"]),
        (
            {},
            {
                "thing.v1.meta-local.json": GOOD,
                "thing.v1.more.yaml": "name: b\n",
            },
            ["thing.v1.meta-local.json", "thing.v1.more.yaml"],
        ),
        (
            {"A.JSON": GOOD},
            {"thing.v1.x.Yaml": "name: x\n"},
            ["thing.v1/A.JSON", "thing.v1.x.Yaml"],
        ),
        (
            {"z.json": GOOD, "a.json": GOOD},
            {"thing.v1.b.json": GOOD, "thing.v1.a.json": GOOD},
            [
                "thing.v1/a.json",
                "thing.v1/z.json",
                "thing.v1.a.json",
                "thing.v1.b.json",
            ],
        ),
    ],
    ids=["folder-only", "flat-only", "any-case-extension", "both-in-a-fixed-order"],
)
def test_both_example_layouts_work_alone_and_together(
    tmp_path: Path, folder: Files, flat: Files, expected: list[str]
) -> None:
    contracts = make_tree(tmp_path, folder, raw=flat)
    passed = tuple((PREFIX + example, THING) for example in expected)
    # The by-hand listing used by the real-repository tests agrees (#25 and #27 are flat only).
    assert listed_examples(contracts) == {
        THING: [PREFIX + example for example in expected]
    }
    for _ in range(2):  # the same on every run
        report = validate_all(contracts)
        assert report.problems == ()
        assert report.passed == passed


def test_a_link_to_a_file_outside_contracts_is_followed_and_reported_under_the_link(
    tmp_path: Path,
) -> None:
    # Documented (README): links are followed whatever they point at; refusing them is not decided.
    outside = tmp_path / "outside.json"
    outside.write_text('{"count": "two"}', encoding="utf-8")
    contracts = make_tree(tmp_path, {"weeks/x.md": ""})  # creates examples/thing.v1/
    try:
        (contracts / "examples" / "thing.v1" / "link.json").symlink_to(outside)
    except (OSError, NotImplementedError):
        pytest.skip("symbolic links are not available here")
    problems = validate_all(contracts).problems
    assert {p.code for p in problems} == {"schema_violation"}  # the target was read
    assert {p.example for p in problems} == {f"{PREFIX}thing.v1/link.json"}


# --- valid examples -------------------------------------------------------------------------


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
def test_valid_example_passes(tmp_path: Path, name: str, content: str) -> None:
    report = validate_all(make_tree(tmp_path, {name: content}))
    assert report.problems == ()
    assert report.passed == ((f"{PREFIX}thing.v1/{name}", THING),)


# --- invalid examples -----------------------------------------------------------------------


@pytest.mark.parametrize("flat", [False, True], ids=["folder", "flat"])
def test_invalid_example_names_example_schema_place_and_keyword(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], flat: bool
) -> None:
    bad = '{"name": "x", "count": "two"}'
    contracts = make_tree(
        tmp_path,
        None if flat else {"bad.json": bad},
        raw={"thing.v1.bad.json": bad} if flat else None,
    )
    example = PREFIX + ("thing.v1.bad.json" if flat else "thing.v1/bad.json")
    assert main(["--contracts-dir", str(contracts)]) == 1
    err = capsys.readouterr().err
    assert f"FAIL {example} (schema {THING})" in err
    assert "count" in err
    assert "[type]" in err
    problem = only(validate_all(contracts))
    assert problem.code == "schema_violation"
    assert problem.example == example
    assert problem.schema == THING


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
        tmp_path, {"a.json": GOOD, "b.json": '{"count": 1}', "c.yaml": "name: c\n"}
    )
    assert main(["--contracts-dir", str(contracts)]) == 1
    out = capsys.readouterr().out
    assert f"OK {PREFIX}thing.v1/a.json" in out
    assert f"OK {PREFIX}thing.v1/c.yaml" in out
    assert "3 examples found, 1 schemas: 2 passed, 1 failed, 0 not validated" in out


# --- missing examples -----------------------------------------------------------------------


@pytest.mark.parametrize(
    ("examples", "flat", "empty_folder"),
    [
        (None, None, False),
        (None, None, True),
        # Subfolders hold supporting files and are ignored by design, even a .json that breaks
        # the schema: with only those, there is still no example to validate.
        ({"weeks/01.md": "# hi\n", "weeks/02.json": "{}"}, None, False),
        # Not examples of thing.v1: another schema's flat file, a name with no suffix, another
        # extension, and flat-named files in a subfolder (of its folder, or of examples/).
        (
            None,
            {
                "other.v1.x.json": "{}",
                "thing.v1.json": "{}",
                "thing.v1.x.txt": "{}",
                "thing.v1/weeks/01.json": "{}",
                "sub/thing.v1.x.json": "{}",
                "thing.v1.X.json": "{}",  # only the extension is case-insensitive
            },
            False,
        ),
    ],
    ids=[
        "no-folder",
        "empty-folder",
        "only-a-supporting-file",
        "no-example-of-this-schema",
    ],
)
def test_schema_without_an_example_in_either_layout_is_an_error(
    tmp_path: Path, examples: Files | None, flat: Files | None, empty_folder: bool
) -> None:
    contracts = make_tree(tmp_path, examples, raw=flat)
    if empty_folder:
        (contracts / "examples" / "thing.v1").mkdir()
    report = validate_all(contracts)
    problem = report.problems[0]
    assert problem.code == "missing_example"
    assert problem.schema == THING
    # Whatever else sits there is reported as well (see the orphan tests); it is never skipped.
    assert {p.code for p in report.problems[1:]} <= {
        "orphan_example",
        "orphan_example_folder",
        "unsupported_file",
    }
    assert listed_examples(contracts) == {THING: []}
    for text in (problem.message, problem.hint):  # every accepted extension is named
        assert all(extension in text for extension in (".json", ".yaml", ".yml"))


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
    contracts = make_tree(tmp_path, {"a.json": GOOD})
    (contracts / "CLAUDE.md").write_text("# notes\n", encoding="utf-8")
    (contracts / "lti-launch.v1.md").write_text("# B3\n", encoding="utf-8")
    assert validate_all(contracts).ok


# --- unreadable files and unusable schemas --------------------------------------------------


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
    assert problem.example == f"{PREFIX}thing.v1/{name}"


@pytest.mark.parametrize(
    ("schema", "schema_code"),
    [
        (
            {"$schema": "https://json-schema.org/draft/2020-12/schema", "type": 5},
            "invalid_schema",
        ),
        ("{not json", "unreadable_schema"),
        (with_ref("#/$defs/missing"), "unresolvable_reference"),
        (with_ref("other.schema.json"), "unresolvable_reference"),
    ],
    ids=["invalid-schema", "unreadable-schema", "dangling-local-ref", "external-ref"],
)
def test_examples_of_an_unusable_schema_are_counted_but_not_validated(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    schema: dict[str, Any] | str,
    schema_code: str,
) -> None:
    # Both examples are valid; they are not validated, so they neither pass nor fail. A reference
    # is only reached by b.json, after a.json has already passed: a.json must not stay in
    # `passed`, and nothing is reported as failed.
    contracts = make_tree(
        tmp_path,
        {"a.json": GOOD, "b.json": '{"name": "b", "link": "x"}'},
        schema=schema,
    )
    report = validate_all(contracts)
    assert codes(report) == [schema_code] + ["example_not_validated"] * 2
    first = report.problems[0]
    assert (first.schema, first.example) == (THING, None)
    assert [(p.example, p.schema) for p in report.problems[1:]] == [
        (f"{PREFIX}thing.v1/a.json", THING),
        (f"{PREFIX}thing.v1/b.json", THING),
    ]
    assert report.example_count == 2
    assert report.passed == ()
    assert report.failed == ()

    assert main(["--contracts-dir", str(contracts)]) == 1
    captured = capsys.readouterr()
    assert "OK " not in captured.out
    assert f"FAIL {THING}" in captured.err
    assert "next:" in captured.err
    assert "2 examples found, 1 schemas: 0 passed, 0 failed, 2 not validated" in (
        captured.out
    )


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
    assert codes(report) == ["misnamed_schema", "orphan_example_folder"]
    assert report.problems[0].schema == f"contracts/{name}"
    assert report.problems[1].example == f"{PREFIX}{folder}"
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


# --- examples that no schema takes, and files that are not examples ---------------------------


@pytest.mark.parametrize(
    "name",
    [
        "thing.v1.json",  # no word between the stem and the extension
        "thing.v1.a.b.json",  # two words
        "thing.v10.x.json",  # the stem of a version that has no schema
        "other.v1.x.json",  # a schema that does not exist
        "thing.v1.X.json",  # only the extension is case-insensitive
        "notes.yaml",
    ],
)
def test_a_flat_file_that_no_schema_takes_is_an_orphan(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], name: str
) -> None:
    contracts = make_tree(tmp_path, {"a.json": GOOD}, raw={name: GOOD})
    problem = only(validate_all(contracts))
    assert problem.code == "orphan_example"
    assert problem.example == f"{PREFIX}{name}"
    assert problem.schema is None
    assert "No schema matches" in problem.message
    assert "contract-change" in problem.hint
    assert main(["--contracts-dir", str(contracts)]) == 1
    err = capsys.readouterr().err
    assert f"FAIL {PREFIX}{name}:" in err
    assert "next: " in err


def test_an_example_folder_with_no_schema_is_an_orphan(tmp_path: Path) -> None:
    contracts = make_tree(tmp_path, {"a.json": GOOD}, raw={"other.v1/a.json": GOOD})
    report = validate_all(contracts)
    problem = only(report)
    assert problem.code == "orphan_example_folder"
    assert problem.example == f"{PREFIX}other.v1"
    assert "contracts/other.v1.schema.json does not exist" in problem.message
    assert report.example_count == 1  # its examples are not counted as checked
    assert main(["--contracts-dir", str(contracts)]) == 1


@pytest.mark.parametrize(
    ("where", "name", "schema"),
    [
        ("folder", "readme.txt", THING),
        ("folder", "A.JSOM", THING),
        ("examples", "README.md", None),
        ("examples", "thing.v1.x.txt", None),
    ],
)
def test_a_file_that_is_not_json_or_yaml_is_reported(
    tmp_path: Path, where: str, name: str, schema: str | None
) -> None:
    raw: Files = {name: "x"} if where == "examples" else {f"thing.v1/{name}": "x"}
    contracts = make_tree(tmp_path, {"a.json": GOOD}, raw=raw)
    problem = only(validate_all(contracts))
    assert problem.code == "unsupported_file"
    assert problem.schema == schema
    assert problem.example == (
        f"{PREFIX}{name}" if where == "examples" else f"{PREFIX}thing.v1/{name}"
    )
    assert all(word in problem.hint for word in (".json", ".yaml", ".yml", "subfolder"))
    assert main(["--contracts-dir", str(contracts)]) == 1


def test_supporting_files_in_a_subfolder_and_hidden_files_are_not_reported(
    tmp_path: Path,
) -> None:
    contracts = make_tree(
        tmp_path,
        {"a.json": GOOD, "weeks/01.md": "# hi\n", ".gitkeep": ""},
        raw={".gitkeep": ""},
    )
    report = validate_all(contracts)
    assert report.problems == ()
    assert report.example_count == 1


# --- strict parsing: a repeated key, NaN and Infinity ---------------------------------------


@pytest.mark.parametrize(
    ("name", "content", "key"),
    [
        ("a.json", '{"name": "a", "name": "b"}', "name"),
        ("a.json", '{"name": "a", "items": [{"x": 1, "x": 2}]}', "x"),
        ("a.json", '{"name": "a", "meta": {"k": 1, "k": 1}}', "k"),
        ("a.yaml", "name: a\nname: b\n", "name"),
        ("a.yml", "name: a\nitems:\n  - {x: 1, x: 2}\n", "x"),
    ],
    ids=["json", "json-in-array", "json-same-value", "yaml", "yaml-in-array"],
)
def test_a_key_repeated_in_one_object_is_reported(
    tmp_path: Path, name: str, content: str, key: str
) -> None:
    contracts = make_tree(tmp_path, {name: content})
    problem = only(validate_all(contracts))
    assert problem.code == "unreadable_example"
    assert problem.example == f"{PREFIX}thing.v1/{name}"
    assert problem.schema == THING
    assert (
        f"the key '{key}' appears more than once in the same object" in problem.message
    )
    if name.endswith((".yaml", ".yml")):
        assert "line " in problem.message and "<unicode string>" not in problem.message
    assert main(["--contracts-dir", str(contracts)]) == 1


@pytest.mark.parametrize(
    ("name", "content"),
    [
        ("a.json", '{"name": "a", "meta": [{"x": 1}, {"x": 2}]}'),  # other objects
        ("a.json", '{"name": "a", "p": {"x": 1}, "q": {"x": 2}}'),
        ("a.yaml", "name: a\np: {x: 1}\nq: {x: 2}\n"),
        # A merge key is not a repeated key: the explicit value wins.
        ("a.yaml", "base: &b {y: 1}\nname: a\nitem:\n  <<: *b\n  y: 2\n"),
    ],
    ids=["json-in-array", "json-siblings", "yaml-siblings", "yaml-merge-override"],
)
def test_the_same_key_in_different_objects_is_fine(
    tmp_path: Path, name: str, content: str
) -> None:
    assert validate_all(make_tree(tmp_path, {name: content})).problems == ()


@pytest.mark.parametrize("value", ["NaN", "Infinity", "-Infinity"])
def test_json_that_python_accepts_but_json_does_not_is_reported(
    tmp_path: Path, value: str
) -> None:
    contracts = make_tree(tmp_path, {"a.json": f'{{"name": "a", "count": {value}}}'})
    problem = only(validate_all(contracts))
    assert problem.code == "unreadable_example"
    assert f"{value} is not valid JSON" in problem.message
    assert main(["--contracts-dir", str(contracts)]) == 1


@pytest.mark.parametrize(
    "number", ["0", "-1", "1e5", "2.5E-3", "123456789012345678901"]
)
def test_ordinary_json_numbers_still_pass(tmp_path: Path, number: str) -> None:
    schema = {
        **SCHEMA,
        "properties": {**SCHEMA["properties"], "count": {"type": "number"}},
    }
    contracts = make_tree(
        tmp_path, {"a.json": f'{{"name": "a", "count": {number}}}'}, schema=schema
    )
    assert validate_all(contracts).problems == ()


# --- CLI ------------------------------------------------------------------------------------


@pytest.mark.parametrize("flag", ["--check", "--dry-run"])
def test_check_and_dry_run_give_the_same_result(tmp_path: Path, flag: str) -> None:
    good = make_tree(tmp_path / "good", {"a.json": GOOD})
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
        assert f"{PREFIX}thing.v1/a.json" in result.stderr
        return
    # Without --contracts-dir the script checks the repository's own contracts, as CI does.
    expected = listed_examples(REAL_CONTRACTS)
    count = sum(len(examples) for examples in expected.values())
    for schema, examples in expected.items():
        for example in examples:
            assert f"OK {example} (schema {schema})" in result.stdout
    assert f"OK {B1_EXAMPLE}" in result.stdout
    assert (
        f"{count} examples found, {len(expected)} schemas: "
        f"{count} passed, 0 failed, 0 not validated" in result.stdout
    )
