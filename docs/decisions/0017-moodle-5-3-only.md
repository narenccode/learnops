# Moodle 5.3 only

**Status:** decided by the guide (chat with his assistant, 2026-11-25, posted on issue #186). It confirms
the direction he set when he waived Moodle 4.5 for the lab grade-write test (11 November 2026) and for B8.1
and the Release 0 tests (14 November 2026).
**Number:** 0017, the next free number when this was written (2026-11-25: `main` has 0001 to 0014; open
pull requests #209 and #223 take 0015 and 0016). It is taken again at merge if another record has merged first.

## Decision

LearnOps supports **Moodle 5.3 only**. Moodle 4.5 is not built for, tested or required in any release.
PRD C-03 reads "Everything works on Moodle 5.3".

## Scope

From now on: no new work, test, lab check, design or plan is made for Moodle 4.5, and no one asks for it.
What is already built or written stays as it is. Existing documents that still mention 4.5 (contract B4,
design documents, test-data READMEs, runbooks and earlier decision records) are **not** rewritten; their
4.5 parts are simply not pursued. Where such a document asks for 4.5 work, this record governs.

## Reason

Time and urgency: one Moodle version removes the second lab site, the second half of the test matrix and
the second set of test data, and the 5.3 lab site is the one that is ready.

## Cost

A site that still runs Moodle 4.5 is not covered by any LearnOps test. Using a LearnOps release on such a
site would need its own check first, outside this project.

## Where it was decided

- Guide, chat with his assistant, 2026-11-25; [posted on issue #186](https://github.com/narenccode/learnops/issues/186#issuecomment-7157429478).
- Earlier waivers: decisions 0009 and 0014, and the 11 November lab grade-write decision (5.3 only).
