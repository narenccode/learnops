"""Markdown report. It distinguishes a synthetic software test from an official evaluation.

The report holds counts and settings only: never transcript text.
"""

from __future__ import annotations

from speech_eval.inputs import EvalRun
from speech_eval.wer import RunResult

BANNERS = {
    "synthetic-test": (
        "SYNTHETIC SOFTWARE TEST. NOT a speech-model evaluation. NOT G-6 evidence. "
        "The inputs are made-up text used to test this tool."
    ),
    "official": (
        "OFFICIAL RUN (gates are declared in the run description; the reviewer must verify each "
        "cited approval). Acceptance stays PENDING until the guide judges this report against the "
        "target."
    ),
}


def _pct(value: float) -> str:
    return f"{value * 100:.2f}%"


def _cell(value: object) -> str:
    """A table cell: run and approval values come from the run description, so escape them."""
    return str(value).replace("|", "\\|").replace("\r", " ").replace("\n", " ")


def render_report(run: EvalRun, result: RunResult) -> str:
    pooled = result.pooled
    lines = [
        "# G-6 caption WER report",
        "",
        f"> **{BANNERS[run.mode]}**",
        "",
        f"- Mode: `{run.mode}`",
        f"- Normaliser: `{run.normaliser}`"
        + (" (not an approved normalisation)" if run.mode == "synthetic-test" else ""),
        "- WER target (G-6): **PENDING** (not set; fixed from the first baseline run, App-C 7)",
        "- Acceptance result (C4.7): **PENDING**",
    ]
    if run.mode == "official":
        lines.append(
            f"- B8.5 dataset status read from the repository: {run.dataset_status}"
        )
        lines += ["", "## Run", "", "| Field | Value |", "|---|---|"]
        lines += [f"| {_cell(k)} | {_cell(v)} |" for k, v in run.run.items()]
        lines += ["", "## Approvals cited", "", "| Gate | Reference |", "|---|---|"]
        lines += [f"| {_cell(k)} | {_cell(v)} |" for k, v in run.approvals.items()]
    if run.warnings:
        lines += ["", "## Warnings", ""]
        lines += [f"- {_cell(w)}" for w in run.warnings]
    lines += [
        "",
        "## Per lecture",
        "",
        "| Lecture | Ref words | Hyp words | S | D | I | WER |",
    ]
    lines.append("|---|---|---|---|---|---|---|")
    for r in result.lectures:
        c = r.counts
        lines.append(
            f"| {r.lecture_id} | {c.reference_words} | {r.hypothesis_words} | "
            f"{c.substitutions} | {c.deletions} | {c.insertions} | {_pct(c.wer)} |"
        )
    lines += [
        "",
        f"**Pooled WER: {_pct(pooled.wer)}** ({pooled.errors} errors / {pooled.reference_words} "
        "reference words; total errors over total words, not the mean of lecture WERs).",
        "",
        "Not reported: confidence interval, WER by accent or term list, timing accuracy, speed.",
    ]
    return "\n".join(lines) + "\n"
