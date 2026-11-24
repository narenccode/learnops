# LearnOps interim presentation: evidence map

Source of status claims: the four-member GitHub audit of `narenccode/learnops` (main at `ecb4389`, fetched 2026-11-16). PRD = `docs/PRD.md`. Classification: **merged** (on main), **open PR**, **draft** (draft PR), **planned** (design only or not started), **PRD** (specification, not an implementation claim), **unsupplied** (needed input not available).

| Slide | Claim presented | Supporting evidence | Class | Caveat |
|---|---|---|---|---|
| 1 | Title, team, department | PRD title; `GETTING-STARTED.md` §2; git author names | PRD | Reg. nos., batch, mentor are placeholders. Names of S1/S2 come from handles; confirm spelling |
| 3 | Five problems P1-P5 and today's figures | PRD §A2 | PRD | Baselines are PRD figures, not measured by the team. Approved problem statement not supplied |
| 3 | Four modules and relationship | PRD §A1, §A8 | PRD | Intended, not implemented |
| 4 | Svarah: 9.6 h, 117 speakers, 19 languages | `docs/literature-video.md` S2 (PR #100, merged) | merged | Owner-audited; the paper's own references not independently verified; "Submitted to INTERSPEECH" is not proof of publication |
| 4 | Grading list of 6 sources | PR #62 §12.1 | open PR | Not re-opened for this deck |
| 4 | Studio and Checker: no survey on main | Audit §K | planned | Absence found by reading, not proof none exists elsewhere |
| 4 | Research gap | None | planned | Hypothesis only |
| 5 | Four provisional objectives | PRD §A3 goals G-1..G-10, §C1.12-C4.12, GETTING-STARTED §7 | unsupplied | Approved proposal not supplied; slide marked "requires confirmation" |
| 5 | S1: B1 schema + 5 examples; validator; B8.1 README | #23, #37, #48, #49, #57 | merged | |
| 5 | S1: B7, B8.2, B1 amendments | #54, #61 (changes requested), #87, #94, #95, #101 | open PR | |
| 5 | S2: validator chain; design skeleton | Merged chain (#90, #92, #102 named in audit; #91 merged to a stacked branch only) | merged | Exact set merged to main not individually confirmed |
| 5 | S2: B2, B3 + ADR 0001 | #46 (changes requested), #83 (review required) | open PR | #68 possibly superseded, unconfirmed |
| 5 | S3: design + sandbox on main, no code | #18, #30 | merged | Design is Draft |
| 5 | S3: B4, B5, model_interface, moodle_ws, B8.4, B8.6 | #27, #25 (approved, awaiting owners), #35 (draft), #63/#76/#79/#80, #31, #33 (draft) | open PR / draft | 5 PRs merged only into stacked branches (#73-75, #77, #78) |
| 5 | S4: manifest, media_paths, B8.5 checker, literature | #32, #84, #86, #82, #89, #99, #100 | merged | |
| 5 | S4: B6.2, templates, speech ADR, WER prep, literature | #93, #85 (approved), #98 (draft), #103 (draft), #106 (draft) | open PR / draft | |
| 5 | Bloom chips | PRD App-B; module Bloom mappings | PRD | Chip state is the deck author's reading of the audit; no L5 evaluation exists |
| 6 | Architecture and flow | PRD §A8 diagram, §A9, §A10, OPS-10, EXT-07 | PRD | Dashed items are not running |
| 6 | Merged: contracts + validator, B1, B6 manifest, media_paths validate/sign, CI | Audit §E, §F; #23, #32, #84, #86 | merged | |
| 6 | Open: B2-B5, B6.2, B7, templates, model_interface, moodle_ws | #46, #83, #27, #25, #93, #54, #85, #35 | open PR / draft | |
| 6 | LTI gateway, DB, queue, harness, modules | Audit §F, §I | planned | No `lti` code; only the ADR in #83 |
| 7 | B8.1-B8.6 status | Audit §G; #57, #61, #31, #33; ADR 0004 | mixed | B8.3 "no PR found" |
| 7 | B8.5 PENDING fields | Audit §C, §G | merged | Local commits (ffprobe durations) are not on GitHub and not counted |
| 7 | Minimums: 30+ submissions, 5+ lectures, 30+ min | PRD §B8 | PRD | |
| 8 | No HPC needed for R0 | PRD OPS-11, §A11, §D1 | PRD | |
| 8 | Lab VMs unevidenced; BBB records "No lab access" | Audit §A, §D | planned | Lab may exist outside GitHub; confirm with guide |
| 8 | Resources used: developer machines, GitHub CI | Audit CI result | merged | No GPU specification exists in sources |
| 9 | 96 PRs; 61 merged, 55 to main; 31 open (9 draft); 4 closed | Audit §A, §M | merged / open PR | |
| 9 | Student PR counts by status | Audit §B matrix | merged / open PR | Open = non-draft, Draft = draft, read from the "open / draft" pairs; the 64 student PRs reconcile |
| 9 | CI success; 2049 tests; mypy 30 files; 3 examples / 2 schemas; 137 CI-script tests | CI run log on main at `ecb4389` | merged | Counts are from the audit; the deck author did not re-run them |
| 9 | 131 reviews by students | Audit §B (23+29+32+47) | merged | Includes changes-requested reviews |
| 10 | Demo plan from main / open PR | Audit §L | plan | Commands must be tested on a fresh clone before the session |
| 11 | Per-student proposed timeline | Audit §O, §D | plan | Proposed, not agreed. Week ranges are the deck author's |
| 11 | 0/7 contracts, 0/4 designs, 0/6 datasets, 0/10 App-C | Audit §D, §N | merged | |
| 11 | ADR 0005/0006 clash; #96, #97 failing check; Issue #65; S3 12 open PRs | Audit §D, §O | open PR | Latest status read by the audit |
| 11 | Interim dates 12-14 Nov 2026 vs audit date 16 Nov | Guidelines PDF; audit header | n/a | Unresolved; confirm actual slot |
| 12 | SDG 4, targets 4.3, 4.4, 4.5 | sdgs.un.org/goals/goal4 | planned | Proposed by the deck author; no approved mapping found. Target wording shortened |
| 13 | R0 not complete; 1 of 5 libraries functional | Audit §D, §F, §N | merged | |
| 14 | References | See slide | n/a | Moodle and BBB entries are official landing pages. Re-open each link before presenting |

## Information excluded as unsupported
- Registration numbers, batch number, mentor name and designation.
- Approved proposal objectives and problem statement text.
- Any deployment URL, lab resource figures, GPU specification, measured accuracy or time savings.
- Publications, patents or copyrights (none evidenced).
- Individual sources of the grading literature list (PR #62 not reproduced).
- Local-only work (including `video/b6-media-paths` edits and local B8.5 duration commits).
