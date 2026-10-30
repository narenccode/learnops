"""Validating a package folder: reading course.yaml and checking that body files exist (B1.1)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from contracts import (
    DirectorySource,
    FileState,
    ValidationConfig,
    validate_package,
)

from .helpers import (
    HELD_RULE_CODES,
    WEEK1_GUIDE,
    WEEK2_GUIDE,
    Doc,
    error_codes,
    not_checked_codes,
    only,
    write_course,
)

# --- DirectorySource ------------------------------------------------------------------------


def test_source_reports_an_existing_file(package_dir: Path) -> None:
    source = DirectorySource(package_dir)
    assert source.file_state("weeks/01-guide.md") is FileState.OK
    assert source.read_text("weeks/01-guide.md").startswith("# Week 1")


def test_source_reports_a_missing_file(package_dir: Path) -> None:
    assert DirectorySource(package_dir).file_state("weeks/nope.md") is FileState.MISSING


def test_source_reports_a_directory(package_dir: Path) -> None:
    assert DirectorySource(package_dir).file_state("weeks") is FileState.NOT_A_FILE


@pytest.mark.parametrize("rel", ["../outside.md", "weeks/../../outside.md"])
def test_source_refuses_paths_that_leave_the_package(
    package_dir: Path, rel: str
) -> None:
    (package_dir.parent / "outside.md").write_text("secret", encoding="utf-8")
    assert DirectorySource(package_dir).file_state(rel) is FileState.OUTSIDE_PACKAGE


def test_source_refuses_an_absolute_path(package_dir: Path, tmp_path: Path) -> None:
    outside = tmp_path / "abs.md"
    outside.write_text("x", encoding="utf-8")
    state = DirectorySource(package_dir).file_state(str(outside))
    assert state is FileState.OUTSIDE_PACKAGE


def test_source_refuses_a_symlink_that_leaves_the_package(package_dir: Path) -> None:
    outside = package_dir.parent / "outside.md"
    outside.write_text("secret", encoding="utf-8")
    link = package_dir / "weeks" / "link.md"
    try:
        os.symlink(outside, link)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks are not available here (Windows without developer mode)")
    source = DirectorySource(package_dir)
    assert source.file_state("weeks/link.md") is FileState.OUTSIDE_PACKAGE


def test_source_does_not_read_a_file_it_refuses(package_dir: Path) -> None:
    (package_dir.parent / "outside.md").write_text("secret", encoding="utf-8")
    with pytest.raises(FileNotFoundError):
        DirectorySource(package_dir).read_text("../outside.md")


# --- the example package, and reading course.yaml -------------------------------------------


def test_example_package_has_no_errors(package_dir: Path) -> None:
    report = validate_package(DirectorySource(package_dir))
    assert report.errors == ()
    assert not_checked_codes(report) == HELD_RULE_CODES


def test_example_package_in_sections_only_mode_has_no_errors(
    package_dir: Path, example_doc: Doc
) -> None:
    example_doc["course"]["mode"] = "sections-only"
    write_course(package_dir, example_doc)
    assert validate_package(DirectorySource(package_dir)).errors == ()


def test_missing_course_yaml_is_an_error(package_dir: Path) -> None:
    (package_dir / "course.yaml").unlink()
    issue = only(validate_package(DirectorySource(package_dir)).errors)
    assert issue.code == "course_yaml_missing"
    assert "course.yaml" in issue.message
    assert issue.fix_hint


def test_unparseable_course_yaml_is_an_error(package_dir: Path) -> None:
    (package_dir / "course.yaml").write_text("sections: [unclosed\n", encoding="utf-8")
    issue = only(validate_package(DirectorySource(package_dir)).errors)
    assert issue.code == "course_yaml_unreadable"
    assert issue.fix_hint


def test_course_yaml_that_is_not_utf8_is_an_error(package_dir: Path) -> None:
    (package_dir / "course.yaml").write_bytes(b"title: \xff\xfe\n")
    issue = only(validate_package(DirectorySource(package_dir)).errors)
    assert issue.code == "course_yaml_unreadable"


def test_course_yaml_that_is_a_list_fails_the_schema(package_dir: Path) -> None:
    (package_dir / "course.yaml").write_text("- a\n- b\n", encoding="utf-8")
    issue = only(validate_package(DirectorySource(package_dir)).errors)
    assert issue.code == "schema_type"


def test_unquoted_yaml_date_fails_the_schema(package_dir: Path) -> None:
    text = (package_dir / "course.yaml").read_text(encoding="utf-8")
    text = text.replace('start_date: "2026-02-09"', "start_date: 2026-02-09")
    (package_dir / "course.yaml").write_text(text, encoding="utf-8")
    report = validate_package(DirectorySource(package_dir))
    assert error_codes(report) == ["schema_type"]


def test_course_rules_also_run_on_a_package(
    package_dir: Path, example_doc: Doc
) -> None:
    example_doc["sections"][1]["activities"][0]["idnumber"] = "wk-01-guide"
    write_course(package_dir, example_doc)
    issue = only(validate_package(DirectorySource(package_dir)).errors)
    assert issue.code == "duplicate_idnumber"


def test_configuration_is_passed_through_to_the_course_rules(
    package_dir: Path, example_doc: Doc
) -> None:
    example_doc["sections"][1]["activities"][0]["idnumber"] = "capstone-gate"
    write_course(package_dir, example_doc)
    source = DirectorySource(package_dir)
    assert validate_package(source).errors == ()
    config = ValidationConfig(protected_idnumbers=frozenset({"capstone-gate"}))
    assert error_codes(validate_package(source, config=config)) == [
        "protected_idnumber"
    ]


# --- body files exist (B1.1) ----------------------------------------------------------------


def test_missing_body_file_is_an_error_at_the_activity(package_dir: Path) -> None:
    (package_dir / "weeks" / "02-guide.md").unlink()
    issue = only(validate_package(DirectorySource(package_dir)).errors)
    assert issue.code == "body_file_missing"
    assert issue.rule == "B1.1"
    assert issue.location == WEEK2_GUIDE + ("body",)
    assert issue.idnumber == "wk-02-guide"
    assert "weeks/02-guide.md" in issue.message
    assert issue.fix_hint


def test_every_missing_body_file_is_reported(package_dir: Path) -> None:
    for name in ("01-guide.md", "02-task.md"):
        (package_dir / "weeks" / name).unlink()
    report = validate_package(DirectorySource(package_dir))
    assert error_codes(report) == ["body_file_missing", "body_file_missing"]


def test_body_that_is_a_folder_is_an_error(package_dir: Path) -> None:
    (package_dir / "weeks" / "01-guide.md").unlink()
    (package_dir / "weeks" / "01-guide.md").mkdir()
    issue = only(validate_package(DirectorySource(package_dir)).errors)
    assert issue.code == "body_not_a_file"
    assert issue.location == WEEK1_GUIDE + ("body",)


def test_body_that_is_a_link_leaving_the_package_is_an_error(
    package_dir: Path,
) -> None:
    outside = package_dir.parent / "outside.md"
    outside.write_text("secret", encoding="utf-8")
    target = package_dir / "weeks" / "01-guide.md"
    target.unlink()
    try:
        os.symlink(outside, target)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks are not available here (Windows without developer mode)")
    issue = only(validate_package(DirectorySource(package_dir)).errors)
    assert issue.code == "body_outside_package"
    assert issue.location == WEEK1_GUIDE + ("body",)


def test_two_activities_may_share_one_body_file(
    package_dir: Path, example_doc: Doc
) -> None:
    # Nothing in the PRD forbids it, so it is not an error.
    example_doc["sections"][1]["activities"][0]["body"] = "weeks/01-guide.md"
    write_course(package_dir, example_doc)
    assert validate_package(DirectorySource(package_dir)).errors == ()


def test_activities_without_a_body_need_no_file(
    package_dir: Path, example_doc: Doc
) -> None:
    example_doc["sections"][0]["activities"].append(
        {"type": "url", "idnumber": "wk-01-link", "title": "Link"}
    )
    write_course(package_dir, example_doc)
    assert validate_package(DirectorySource(package_dir)).errors == ()


def test_body_files_are_not_checked_while_the_structure_is_invalid(
    package_dir: Path, example_doc: Doc
) -> None:
    del example_doc["sections"][0]["title"]
    write_course(package_dir, example_doc)
    (package_dir / "weeks" / "02-guide.md").unlink()
    report = validate_package(DirectorySource(package_dir))
    assert error_codes(report) == ["schema_required"]
    assert "cross_rules_not_checked" in not_checked_codes(report)
