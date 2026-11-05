"""Validating a package folder: reading course.yaml and checking that body files exist (B1.1).

The body check looks at the file system only to see whether a file is there; it never reads a body.
Three tests make symbolic links. They are skipped where the system does not allow links (Windows
without developer mode) and must run on the Linux CI.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from contracts import (
    ConfigError,
    DirectorySource,
    FileState,
    ValidationConfig,
    validate_package,
)

from .helpers import (
    HELD_RULE_CODES,
    PACKAGE_HELD_RULE_CODES,
    WEEK1_GUIDE,
    WEEK2_GUIDE,
    Doc,
    error_codes,
    link_or_skip,
    not_checked_codes,
    only,
    write_course,
)

BODY = ("body",)

# --- DirectorySource ------------------------------------------------------------------------


def test_source_reads_an_existing_file(package_dir: Path) -> None:
    source = DirectorySource(package_dir)
    assert source.file_state("weeks/01-guide.md") is FileState.OK
    assert source.read_text("weeks/01-guide.md").startswith("# Week 1")


@pytest.mark.parametrize(
    ("rel", "state"),
    [("weeks/nope.md", FileState.MISSING), ("weeks", FileState.NOT_A_FILE)],
)
def test_source_tells_a_missing_file_from_a_folder(
    package_dir: Path, rel: str, state: FileState
) -> None:
    assert DirectorySource(package_dir).file_state(rel) is state


def test_source_refuses_paths_that_leave_the_package(package_dir: Path) -> None:
    outside = package_dir.parent / "outside.md"
    outside.write_text("secret", encoding="utf-8")
    source = DirectorySource(package_dir)
    for rel in ("../outside.md", "weeks/../../outside.md", str(outside)):
        assert source.file_state(rel) is FileState.OUTSIDE_PACKAGE, rel
        with pytest.raises(FileNotFoundError):  # and a refused file is never read
            source.read_text(rel)


def test_source_refuses_a_link_that_leaves_the_package(package_dir: Path) -> None:
    outside = package_dir.parent / "outside.md"
    outside.write_text("secret", encoding="utf-8")
    link_or_skip(package_dir / "weeks" / "link.md", outside)
    state = DirectorySource(package_dir).file_state("weeks/link.md")
    assert state is FileState.OUTSIDE_PACKAGE


def test_source_follows_a_link_that_stays_inside_the_package(
    package_dir: Path,
) -> None:
    link_or_skip(
        package_dir / "weeks" / "link.md", package_dir / "weeks" / "01-guide.md"
    )
    assert DirectorySource(package_dir).file_state("weeks/link.md") is FileState.OK


# --- the example package, and reading course.yaml -------------------------------------------


def test_example_package_has_no_errors(package_dir: Path) -> None:
    report = validate_package(DirectorySource(package_dir))
    assert report.errors == ()
    assert not_checked_codes(report) == PACKAGE_HELD_RULE_CODES


def test_missing_course_yaml_is_an_error(package_dir: Path) -> None:
    (package_dir / "course.yaml").unlink()
    report = validate_package(DirectorySource(package_dir))
    issue = only(report.errors)
    assert issue.code == "course_yaml_missing" and issue.rule == "B1.1"
    assert "course.yaml" in issue.message and issue.fix_hint
    assert not_checked_codes(report) == HELD_RULE_CODES | {"cross_rules_not_checked"}


@pytest.mark.parametrize(
    "content",
    [b"sections: [unclosed\n", b"title: \xff\xfe\n", b"a: 1\n---\nb: 2\n"],
    ids=["bad yaml", "not utf-8", "two documents"],
)
def test_course_yaml_that_cannot_be_read_is_an_error(
    package_dir: Path, content: bytes
) -> None:
    (package_dir / "course.yaml").write_bytes(content)
    issue = only(validate_package(DirectorySource(package_dir)).errors)
    assert issue.code == "course_yaml_unreadable" and issue.fix_hint


@pytest.mark.parametrize(
    ("date", "code"),
    [
        ("2026-02-09", "schema_type"),  # a real date is read as a date, not as text
        (
            "2026-02-31",
            "course_yaml_unreadable",
        ),  # PyYAML raises ValueError for this one
    ],
)
def test_an_unquoted_yaml_date_is_an_error(
    package_dir: Path, date: str, code: str
) -> None:
    path = package_dir / "course.yaml"
    text = path.read_text(encoding="utf-8")
    assert 'start_date: "2026-02-09"' in text
    path.write_text(text.replace('"2026-02-09"', date), encoding="utf-8")
    assert error_codes(validate_package(DirectorySource(package_dir))) == [code]


@pytest.mark.parametrize("content", ["- a\n- b\n", ""], ids=["a list", "empty"])
def test_course_yaml_that_is_not_an_object_fails_the_schema(
    package_dir: Path, content: str
) -> None:
    (package_dir / "course.yaml").write_text(content, encoding="utf-8")
    issue = only(validate_package(DirectorySource(package_dir)).errors)
    assert issue.code == "schema_type" and issue.location == ()


def test_the_other_course_rules_and_the_settings_also_apply_to_a_package(
    package_dir: Path, example_doc: Doc
) -> None:
    example_doc["sections"][1]["activities"][0]["idnumber"] = "wk-01-guide"
    example_doc["sections"][1]["activities"][1]["idnumber"] = "capstone-gate"
    write_course(package_dir, example_doc)
    source = DirectorySource(package_dir)
    assert error_codes(validate_package(source)) == ["duplicate_idnumber"]
    config = ValidationConfig(protected_idnumbers=frozenset({"capstone-gate"}))
    report = validate_package(source, config=config)
    assert error_codes(report) == ["duplicate_idnumber", "protected_idnumber"]


# --- body files exist (B1.1) ----------------------------------------------------------------


@pytest.mark.parametrize("mode", ["full", "sections-only"])
def test_missing_body_file_is_an_error_at_the_activity(
    package_dir: Path, example_doc: Doc, mode: str
) -> None:
    example_doc["course"]["mode"] = mode
    write_course(package_dir, example_doc)
    (package_dir / "weeks" / "02-guide.md").unlink()
    issue = only(validate_package(DirectorySource(package_dir)).errors)
    assert issue.code == "body_file_missing" and issue.rule == "B1.1"
    assert issue.location == WEEK2_GUIDE + BODY
    assert issue.idnumber == "wk-02-guide"
    assert "sections[1].activities[0].body" in issue.message
    assert "weeks/02-guide.md" in issue.message and issue.fix_hint


def test_every_missing_body_file_is_reported_in_document_order(
    package_dir: Path,
) -> None:
    for name in ("02-task.md", "01-guide.md"):
        (package_dir / "weeks" / name).unlink()
    report = validate_package(DirectorySource(package_dir))
    assert [i.idnumber for i in report.errors] == ["wk-01-guide", "wk-02-task"]


def test_body_that_is_a_folder_is_an_error(package_dir: Path) -> None:
    (package_dir / "weeks" / "01-guide.md").unlink()
    (package_dir / "weeks" / "01-guide.md").mkdir()
    issue = only(validate_package(DirectorySource(package_dir)).errors)
    assert issue.code == "body_not_a_file" and issue.location == WEEK1_GUIDE + BODY


def test_body_that_is_a_link_leaving_the_package_is_an_error(
    package_dir: Path,
) -> None:
    outside = package_dir.parent / "outside.md"
    outside.write_text("secret", encoding="utf-8")
    (package_dir / "weeks" / "01-guide.md").unlink()
    link_or_skip(package_dir / "weeks" / "01-guide.md", outside)
    issue = only(validate_package(DirectorySource(package_dir)).errors)
    assert issue.code == "body_outside_package" and issue.location == WEEK1_GUIDE + BODY


def test_a_body_file_may_be_shared_and_an_activity_may_have_no_body(
    package_dir: Path, example_doc: Doc
) -> None:
    # Nothing in the PRD forbids either, so neither is an error.
    example_doc["sections"][1]["activities"][0]["body"] = "weeks/01-guide.md"
    example_doc["sections"][0]["activities"].append(
        {"type": "url", "idnumber": "wk-01-link", "title": "Link"}
    )
    write_course(package_dir, example_doc)
    assert validate_package(DirectorySource(package_dir)).errors == ()


def test_duplicate_idnumbers_are_reported_before_missing_body_files(
    package_dir: Path, example_doc: Doc
) -> None:
    example_doc["sections"][1]["idnumber"] = "wk-01"
    write_course(package_dir, example_doc)
    (package_dir / "weeks" / "01-guide.md").unlink()
    report = validate_package(DirectorySource(package_dir))
    assert error_codes(report) == ["duplicate_idnumber", "body_file_missing"]


# --- body files are listed as not checked unless they were checked --------------------------


def test_body_files_are_not_checked_while_the_structure_is_invalid(
    package_dir: Path, example_doc: Doc
) -> None:
    del example_doc["sections"][0]["title"]
    write_course(package_dir, example_doc)
    (package_dir / "weeks" / "02-guide.md").unlink()
    report = validate_package(DirectorySource(package_dir))
    assert error_codes(report) == ["schema_required"]
    assert not_checked_codes(report) == HELD_RULE_CODES | {"cross_rules_not_checked"}
    notice = {i.code: i for i in report.not_checked}["body_files_not_checked"]
    assert (
        "once course.yaml is valid" in notice.message
    )  # not "needs the package folder"


# --- any other source, and the settings -----------------------------------------------------


class MemorySource:
    """A package kept in a dictionary; it records what was read."""

    def __init__(self, files: dict[str, str]) -> None:
        self.files = files
        self.reads: list[str] = []

    def file_state(self, rel: str) -> FileState:
        return FileState.OK if rel in self.files else FileState.MISSING

    def read_text(self, rel: str) -> str:
        self.reads.append(rel)
        if rel not in self.files:
            raise FileNotFoundError(rel)
        return self.files[rel]


def test_any_package_source_works_and_only_course_yaml_is_read(
    package_dir: Path,
) -> None:
    course = (package_dir / "course.yaml").read_text(encoding="utf-8")
    bodies = {
        f"weeks/{n}.md": "" for n in ("01-guide", "01-task", "02-guide", "02-task")
    }
    source = MemorySource({"course.yaml": course, **bodies})
    assert validate_package(source).errors == ()
    assert source.reads == ["course.yaml"]  # body files are looked for, never read
    del source.files["weeks/01-task.md"]
    assert error_codes(validate_package(source)) == ["body_file_missing"]


def test_a_wrong_config_is_refused_before_anything_is_read() -> None:
    source = MemorySource({})
    with pytest.raises(ConfigError):
        validate_package(source, config={})  # type: ignore[arg-type]
    assert source.reads == []
