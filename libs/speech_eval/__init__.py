"""G-6 caption word-error-rate (WER) evaluation support (PRD G-6, App-C 7, C4.7).

Preparation only. Nothing here measures a speech model on its own: the tool compares reference
transcripts with hypothesis transcripts that somebody else produced, and it refuses an `official`
run until the official inputs and approvals exist. See docs/evaluation/g6-wer-procedure.md.
"""

from speech_eval.inputs import EvalRun, LectureInput, load_run
from speech_eval.report import render_report
from speech_eval.wer import EditCounts, LectureResult, RunResult, edit_counts, evaluate

__all__ = [
    "EditCounts",
    "EvalRun",
    "LectureInput",
    "LectureResult",
    "RunResult",
    "edit_counts",
    "evaluate",
    "load_run",
    "render_report",
]
