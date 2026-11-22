"""Word error rate by word-level edit distance. No third-party dependency.

WER = (substitutions + deletions + insertions) / words in the reference. The pooled WER is the
total errors over all lectures divided by the total reference words (not the mean of the
per-lecture WERs). Only the total error count is the metric: when several alignments are equally
good, the split into S/D/I may differ between implementations.

Text normalisation is NOT decided yet (testdata/b8-5-lecture-videos/README.md: "decided with the
first baseline run, App-C 7"). The only normaliser here is `unnormalised-whitespace` (split on
whitespace; case and punctuation kept). It is for software tests, not for an official result.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass

NORMALISERS: dict[str, Callable[[str], list[str]]] = {
    "unnormalised-whitespace": lambda text: text.split(),
}

# Pure-Python edit distance is O(n*m). Refuse inputs that would take minutes, with a clear message.
MAX_CELLS = 25_000_000


@dataclass(frozen=True)
class EditCounts:
    substitutions: int
    deletions: int
    insertions: int
    reference_words: int

    @property
    def errors(self) -> int:
        return self.substitutions + self.deletions + self.insertions

    @property
    def wer(self) -> float:
        if self.reference_words == 0:
            raise ValueError("WER is undefined for an empty reference")
        return self.errors / self.reference_words


@dataclass(frozen=True)
class LectureResult:
    lecture_id: str
    counts: EditCounts
    hypothesis_words: int


@dataclass(frozen=True)
class RunResult:
    lectures: tuple[LectureResult, ...]

    @property
    def pooled(self) -> EditCounts:
        return EditCounts(
            substitutions=sum(r.counts.substitutions for r in self.lectures),
            deletions=sum(r.counts.deletions for r in self.lectures),
            insertions=sum(r.counts.insertions for r in self.lectures),
            reference_words=sum(r.counts.reference_words for r in self.lectures),
        )


def edit_counts(reference: Sequence[str], hypothesis: Sequence[str]) -> EditCounts:
    """Levenshtein distance between two word lists, with substitution/deletion/insertion counts."""
    n, m = len(reference), len(hypothesis)
    if n * m > MAX_CELLS:
        raise ValueError(
            f"{n} reference x {m} hypothesis words is too large for this tool "
            f"(limit {MAX_CELLS} cells); split the lecture into shorter parts"
        )
    # Each cell: (errors, substitutions, deletions, insertions).
    prev = [(j, 0, 0, j) for j in range(m + 1)]
    for i in range(1, n + 1):
        cur = [(i, 0, i, 0)]
        for j in range(1, m + 1):
            e, s, d, ins = prev[j - 1]
            best = (
                (e, s, d, ins)
                if reference[i - 1] == hypothesis[j - 1]
                else (e + 1, s + 1, d, ins)
            )
            e, s, d, ins = prev[j]
            if e + 1 < best[0]:
                best = (e + 1, s, d + 1, ins)
            e, s, d, ins = cur[j - 1]
            if e + 1 < best[0]:
                best = (e + 1, s, d, ins + 1)
            cur.append(best)
        prev = cur
    errors, s, d, ins = prev[m]
    assert errors == s + d + ins
    return EditCounts(s, d, ins, n)


def evaluate(
    pairs: Sequence[tuple[str, str, str]], normaliser: str = "unnormalised-whitespace"
) -> RunResult:
    """`pairs` are (lecture_id, reference_text, hypothesis_text)."""
    if normaliser not in NORMALISERS:
        raise ValueError(
            f"unknown normaliser {normaliser!r}; known: {sorted(NORMALISERS)}"
        )
    tokenise = NORMALISERS[normaliser]
    results = []
    for lecture_id, ref_text, hyp_text in pairs:
        ref, hyp = tokenise(ref_text), tokenise(hyp_text)
        results.append(LectureResult(lecture_id, edit_counts(ref, hyp), len(hyp)))
    return RunResult(tuple(results))
