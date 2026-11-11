# 0005: B7 H5P content types and versions (lab check)

**Status: recorded.** The lab check was reported by the guide on 2026-11-11. B7 itself is still a
draft contract (`contracts/h5p-practice.v1.md`).

This record closes PRD App-C item 5, "Exact H5P content-type versions available on both Moodle
versions".

## Result of the lab check

| Item | Value |
|---|---|
| Date | 2026-11-11 |
| Sites | Both lab Moodle sites: 4.5 and 5.3. The guide gave no point releases |
| How | Moodle's own scheduled task downloaded the content types from h5p.org on 2026-11-11 |
| Reported by | The guide, in a comment on PR #54 (2026-11-11, 09:19 UTC). The author of this record did not repeat the check |
| Outcome | All five libraries are installed and runnable on both sites, at the same versions |

| Content type | H5P library (machine name) | Version | Moodle 4.5 | Moodle 5.3 |
|---|---|---|---|---|
| Question Set | `H5P.QuestionSet` | 1.21.14 | installed, runnable | installed, runnable |
| Drag the Words | `H5P.DragText` | 1.10.50 | installed, runnable | installed, runnable |
| Drag and Drop | `H5P.DragQuestion` | 1.15.37 | installed, runnable | installed, runnable |
| Branching Scenario | `H5P.BranchingScenario` | 1.11.2 | installed, runnable | installed, runnable |
| Interactive Video | `H5P.InteractiveVideo` | 1.28.37 | installed, runnable | installed, runnable |

## Decisions (guide, PR #54, 2026-11-11)

1. "Drag the Words" and "Drag and Drop" are two separate H5P libraries, so they are two entries.
   Each practice item uses one of them.
2. Ordering is not a separate content type in v1. Where it is needed, it is done with Drag and
   Drop. A later release can add a type as an optional entry.
3. B7 pins these exact versions for the Release 0 tests. h5p.org may publish newer ones, so a
   change is made only through a `/contract-change`.
4. Interactive video stays "lab demonstrations only" (PRD B7). It cannot be enforced in
   `course.yaml`, because the content type is inside the `.h5p` file and `course.yaml` holds only a
   path to it. It stays listed with the held rules.

## What this closes, and what stays open

Closed: PRD App-C item 5, and two open decisions in B7 (the library versions, and whether "drag the
words" and "drag and drop / ordering" are one type or two).

Still open in B7, not settled by this check: several practice items in one week; where a video
checkpoint goes; the `ref` kinds of a cue (B6); and whether a data field should mark interactive
video as lab-only.

## Where it is applied

`contracts/h5p-practice.v1.md` (section 3), `contracts/h5p-practice.v1.schema.json`,
`contracts/examples/h5p-practice.v1.content-types.json` and
`libs/contracts/tests/test_h5p_practice_v1.py`. The test writes the five pairs out and checks that
the schema, the example, the contract text and this record all agree with them.

## Limits

- The repository holds no evidence of the lab check beyond the guide's report.
- The Moodle point releases of the two sites are not recorded.
- Nothing checks that an `.h5p` file really uses these libraries at these versions (held rule
  `h5p_files_not_checked`).
