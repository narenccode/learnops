"""A fake Moodle that behaves as the Moodle 4.5 and 5.3 SOURCE says, for the grade-write tests.

NOT a recording and NOT lab-verified. Every behaviour here is what B4 records from reading the
code (contracts/moodle-ws.v1.md §6a, §7) or what the guide read in it (§3a, PR #64):

* get_submission_status: `lastattempt.gradingstatus` is the workflow state; `lastattempt` is left
  out when the learner lacks viewownsubmissionsummary (R6, lab check 12).
* get_grades: `assignments[].grades[]` with `userid`, `attemptnumber` and `grade` as text with five
  decimals (R1, R9; the decimals are lab check 13); "no grades" is a warning.
* save_grade on 5.3: a submission already in readyforrelease or released keeps its old grade and
  state while the call looks successful. On 4.5 it is overwritten (R3, lab check 16).
* save_grade on both: a grade below 0 or above the maximum is silently ignored (R9, lab check 15).

When the lab checks are run, this file must be replaced by recorded answers (design Q53).
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Final

from moodle_ws import SiteSettings
from moodle_ws.errors import MoodleError

ASSIGNMENT: Final = 7
LEARNER: Final = 42
LOCKED: Final = ("readyforrelease", "released")


@dataclass
class SourceFakeMoodle:
    version: str
    state: str = "notmarked"
    grade: str | None = None
    attempt: int = 0
    max_grade: Decimal = Decimal(100)
    show_lastattempt: bool = True
    # Function name -> error raised instead of answering.
    failures: dict[str, MoodleError] = field(default_factory=dict)
    # The write is applied, then this error is raised: the answer was lost (R11).
    lose_save_answer: MoodleError | None = None
    # Runs after the first status read: another person acts between the check and the write.
    between_check_and_write: Callable[[SourceFakeMoodle], None] | None = None
    calls: list[tuple[str, dict[str, Any]]] = field(default_factory=list)

    def call(
        self, settings: SiteSettings, function: str, params: Mapping[str, Any]
    ) -> Any:
        assert settings.moodle_version == self.version
        self.calls.append((function, dict(params)))
        if function in self.failures:
            raise self.failures[function]
        handler = {
            "mod_assign_get_submission_status": self._status,
            "mod_assign_get_grades": self._grades,
            "mod_assign_save_grade": self._save,
        }[function]
        return handler(params)

    def count(self, function: str) -> int:
        return sum(1 for name, _ in self.calls if name == function)

    def _status(self, params: Mapping[str, Any]) -> Any:
        hook = self.between_check_and_write
        if hook is not None and self.count("mod_assign_get_submission_status") == 1:
            self.between_check_and_write = None
            answer = self._status_answer()
            hook(self)
            return answer
        return self._status_answer()

    def _status_answer(self) -> Any:
        if not self.show_lastattempt:
            return {}
        return {"lastattempt": {"gradingstatus": self.state}}

    def _grades(self, params: Mapping[str, Any]) -> Any:
        if self.grade is None:
            return {
                "assignments": [],
                "warnings": [
                    {"item": "assignment", "itemid": ASSIGNMENT, "warningcode": "3"}
                ],
            }
        row = {"userid": LEARNER, "attemptnumber": self.attempt, "grade": self.grade}
        return {
            "assignments": [{"assignmentid": ASSIGNMENT, "grades": [row]}],
            "warnings": [],
        }

    def _save(self, params: Mapping[str, Any]) -> Any:
        self._apply(params)
        if self.lose_save_answer is not None:
            raise self.lose_save_answer
        return None

    def _apply(self, params: Mapping[str, Any]) -> None:
        if self.version == "5.3" and self.state in LOCKED:
            return  # the call looks successful; nothing changes
        grade = Decimal(str(params["grade"]))
        if not Decimal(0) <= grade <= self.max_grade:
            # Silently ignored, no error. Whether the state still changes is not known; the
            # grade-value read-back fails either way.
            return
        self.grade = f"{grade:.5f}"
        self.attempt = params["attemptnumber"]
        self.state = params["workflowstate"]
