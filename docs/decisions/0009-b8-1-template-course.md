# B8.1 — Template course: Moodle 4.5 waived for Release 0

## Decision

For Release 0 the B8.1 template course is built and tested on Moodle 5.3 only. Moodle 4.5 is **waived by the guide for Release 0 (decided 2026-11-14, confirmed as a C-03 deviation 2026-11-15; scope B8.1 only)**.

- Every restore and the sections-only merge test for B8.1 run on Moodle 5.3. The `.mbz` is labelled "built on Moodle 5.3".
- Moodle 4.5 is not tested. It is not recorded as passed.
- This is a recorded deviation from PRD C-03 (the tools must work on Moodle 4.5 and 5.3). The PRD text is not changed; the deviation is recorded here and in the C-03 row of `docs/traceability.md`.

## Scope

B8.1 only. A reader must not apply this waiver to any other data set or release.

- The B8.2 restore and merge tests have their own decision, made by the guide on 2026-11-16 (answer A5 on PR #61) and recorded with B8.2, not here.
- C-03 still applies to the checker harness (FR-C-08).

## Cost

If the project later needs the template on Moodle 4.5 (PRD C-03: it must work on 4.5 and 5.3), it is rebuilt once on 4.5. The owner reports that Moodle restores a backup only into the same or a newer version, so a 5.3 template is expected not to restore on 4.5. This is the owner's report and has not been verified.

## Where it was decided

- Guide, Issue #55, 2026-11-14: [build and test on 5.3 only](https://github.com/narenccode/learnops/issues/55#issuecomment-6877171351).
- Guide, PR #95, 2026-11-15: [confirmed as a formal deviation from C-03, scope B8.1](https://github.com/narenccode/learnops/pull/95#issuecomment-6902712542).
- Guide, PR #95, 2026-11-15: [the traceability row](https://github.com/narenccode/learnops/pull/95#issuecomment-6903284655).
- Guide, PR #95, 2026-11-16: [one phrase in every file](https://github.com/narenccode/learnops/pull/95#issuecomment-6907855168).
- Guide, PR #95, 2026-11-16: [this decision record, PRD unchanged, next free number at merge](https://github.com/narenccode/learnops/pull/95#issuecomment-6913152687).

## Results (App-C item 2)

No results yet. The short, text-only results table of the restore and merge tests goes in this file. It names the local screenshots and logs, which stay local and are not committed. The merge-test results must be in this file before the merge-test course is deleted.
