"""The validation result types."""

from __future__ import annotations

import dataclasses

import pytest

from contracts.report import Issue, ValidationReport


def make_issue(code: str = "x") -> Issue:
    return Issue(code=code, rule="B1.2 rule 6", message="m", fix_hint="h")


def test_empty_report_is_ok() -> None:
    assert ValidationReport().ok


def test_report_with_an_error_is_not_ok() -> None:
    assert not ValidationReport(errors=(make_issue(),)).ok


def test_not_checked_items_do_not_make_a_report_fail() -> None:
    # "Not checked" means the rule did not run. It is reported, but it is not an error.
    assert ValidationReport(not_checked=(make_issue(),)).ok


def test_issue_defaults_are_a_document_level_issue() -> None:
    issue = make_issue()
    assert issue.location == ()
    assert issue.idnumber is None


def test_issue_cannot_be_changed_after_creation() -> None:
    issue = make_issue()
    with pytest.raises(dataclasses.FrozenInstanceError):
        issue.code = "other"  # type: ignore[misc]
