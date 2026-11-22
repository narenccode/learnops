# B8.5 licence and consent evidence: inventory, gap report and handling rules

**Status: PENDING. B8.5 is NOT complete. App-C 8 is NOT met.** This document records evidence and
gaps. It does not grant, infer or approve anything.
**Audit date:** 2026-11-20, re-audited at `origin/main` `5f3a794`. The local file check in section 2
was made on 2026-11-16 and was not repeated; everything about the repository was re-read on the
audit date. **Scope note (PRD §D1, PRs #113 and #116):** App-C 8 is no longer a Release 0 item; it
belongs to the first release that relies on it. The B8.5 set itself (test data B8 v1) is still in
Release 0.
**Covers:** the release task labelled T11 (licence and consent evidence) and T7 (official B8.5
dataset evidence) in the project tracker.

> **About the labels T7, T11, T20.** They are not defined in any file, issue or PR description in
> this repository (second pass searched `docs/`, `.claude/`, `.github/`, GitHub issues, and the
> bodies of PRs #96, #97, #98, #103, #105, #106; PRs #103, #105 and #106 each say the same about
> T9, T19 and T13). The only label the repository does tie to a requirement is **T10 = App-C 4**
> (PR #96) and **T17 = lab BigBlueButton verification** (PR #97). This document therefore works
> from the requirements that **are** in the repository: PRD App-C 8, PRD §B8.5 / §A6 item 4,
> decision 0004 and the B8.5 READMEs. **Mapping still PENDING confirmation against the external
> tracker:** T11 = App-C 8; T7 = the B8.5 dataset. If the tracker's wording differs, the tracker
> wins.

## 0. Summary counts (5 recordings assessed, labelled lecture-01 to lecture-05)

| Evidence | Verified | Missing | Ambiguous | Pending |
|---|---|---|---|---|
| Recording exists locally with matching SHA-256 | 5 | 0 | 0 | 0 |
| Duration measured with `ffprobe` | 5 | 0 | 0 | 0 |
| Provenance as official B8.5 (not temporary test clips) | 0 | 0 | 5 | 5 (G-8) |
| Written consent line (App-C 8) | 0 | 5 | 0 | 5 |
| Licence or permission evidence | 0 | 5 | 0 | 5 |
| Reference transcript, reviewed | 0 | 5 | 0 | 5 |
| Retention rule | Decided (decision 0011, 2026-11-19) | n/a | n/a | Nothing deleted yet: no evaluation has run |

"Verified" counts only what a command in section 7 actually showed. "Ambiguous" means the evidence
could be read two ways and nothing in the repository settles it.

## 1. Requirements found (verbatim sources)

| Source | Requirement |
|---|---|
| PRD App-C 8 | "Licence or consent for every B8.5 video." |
| PRD §B8 (B8.5) | "≥ 5 Indian-English technical lectures (≥ 30 min total, enough for the Release 0 baseline) with reference transcripts; recorded with written consent or openly licensed (licence verified and recorded)" (owner: Student 4) |
| PRD §A6 | "Lecture videos with reference transcripts can be obtained with permission (§B8.5)." |
| Decision 0004 | Each speaker writes **one consent line** with their name, the date and the exact sentence `used to test speech recognition; video stays in the lab; transcript published under Apache-2.0`. Recordings stay private and outside Git. Approved transcripts are published under Apache-2.0. Harshitha reviews the reference transcripts. |
| Decision 0004, completion criteria | At least five recordings; total at least 1800 s; reference transcripts prepared and reviewed; speaker consent lines documented. |
| Decision 0004, temporary exception | Guide approved that the 1800 s minimum need not be reached "for now"; the exception covers only that minimum. Approval reference: the guide's confirmation on issue #121, recorded in decision 0004 by PR #125. A second temporary exception allows four lectures for interim work (same record). |
| `docs/data-map.md`; decision 0011 | Retention/deletion of recordings, lab-storage access, names and transcripts, and processing services were decided by the guide on 2026-11-19 and are recorded in `docs/decisions/0011-b8-5-data-handling.md`; the data-map rows follow it. What the lab endpoint keeps is not recorded yet (decision 0002, PR #98). |

## 2. Evidence inventory (per recording)

"Local" = checked in this audit on the machine that holds the files. Paths and file names are
deliberately not recorded here.

| ID | Recording exists locally | SHA-256 in inventory matches local file | Duration (ffprobe, floor, this audit) | Speaker named | Consent line in decision 0004 | Licence evidence | Reference transcript | Transcript review | Usable as official B8.5 evidence |
|---|---|---|---|---|---|---|---|---|---|
| lecture-01 | Yes | Yes (`e42cca9d…7610`) | 62 s | PENDING | **None** | None; recording has no public licence by design | Placeholder (`PENDING`) | pending | **No** |
| lecture-02 | Yes | Yes (`d7325048…7afe`) | 82 s | PENDING | **None** | None | Placeholder | pending | **No** |
| lecture-03 | Yes | Yes (`2b8cbfd5…9432`) | 43 s | PENDING | **None** | None | Placeholder | pending | **No** |
| lecture-04 | Yes | Yes (`285ed527…7845`) | 68 s | PENDING | **None** | None | Placeholder | pending | **No** |
| lecture-05 | Yes | Yes (`8e8a4d57…89f8`) | 83 s | PENDING | **None** | None | Placeholder | pending | **No** |
| **Total** | 5 of 5 | 5 of 5 | **338 s** (6 min 38 s) | 0 of 5 | **0 of 5** | 0 of 5 | 0 of 5 | 0 of 5 | **0 of 5** |

How the local check was done (read-only; nothing copied, uploaded or modified):

1. Computed `Get-FileHash -Algorithm SHA256` for every video file (mp4/mov/mkv/webm/avi, under 500 MB)
   in the user's Desktop, Videos, Downloads and Documents folders outside any `learnops*` folder,
   and compared each with the five SHA-256 values in the B8.5 inventory (`testdata/README.md`).
   Result: 5 of 5 values matched exactly one file each.
2. Ran `ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1`
   on the five matched files. Results: 62.216722, 82.882033, 43.789333, 68.116271, 83.276563 s.
   These agree with the whole-second values (62, 82, 43, 68, 83) recorded on the **unmerged**
   branch `video/b8-5-dataset-evidence` (commit `9c6d703`). `origin/main` still shows durations as
   `PENDING`. **Correction of the first pass:** PR #99 did merge commits `b6c8753`, `9b94943` and
   `5b6460f` (hash-only inventory and the decision 0004 exception text); the single commit not on
   `main` is `9c6d703`, and `git diff origin/main origin/video/b8-5-dataset-evidence` over the
   B8.5 files shows only the five Duration cells in `testdata/README.md`.

What this check proves: that five files with the inventoried hashes exist locally and have the
stated durations. What it does **not** prove: who is in the recordings, that they consented, that
the speech is Indian-English technical content, that the files are the official B8.5 set rather
than temporary pipeline-test clips (see gap G-8), or anything about licence.

## 3. Gap report

| # | Gap | Evidence needed | Status |
|---|---|---|---|
| G-1 | No consent line exists for any speaker (`## Consent lines` says "No consent lines yet.") | One line per speaker, written by that speaker, in the exact decision 0004 form | **PENDING**; blocks App-C 8 |
| G-2 | Speaker names are `PENDING` for all five lectures, so no recording can be linked to a speaker or a consent line | Speaker column filled by the recording team; name must match the consent line | **PENDING** |
| G-3 | No record that speakers were told about the interim storage and the public name/consent line before consenting (decision 0004 requires it) | A statement in the PR or decision record by the person who obtained consent | **PENDING** |
| G-4 | No outline or reference transcript exists (all ten files are placeholders); no Harshitha review | Reviewed transcripts, then `checked` | **PENDING** |
| G-5 | Total duration 338 s is below the 1800 s threshold. The guide approved a temporary exception; decision 0004 now cites the guide's confirmation on issue #121 (PR #125), but not the date of the earlier approval. A second temporary exception allows four lectures instead of five for interim demonstration and testing only | Both exceptions are temporary and are not waivers: the set is complete only with five recordings, and the 1800 s total is still the acceptance threshold | **Reference recorded** (date of the earlier approval not recorded); requirement still **not met** |
| G-6 | Retention and deletion of recordings, extracted audio and drafts; lab-storage access; retention of names, consent lines and transcripts (and what happens on withdrawal) | The guide's decisions, recorded in `docs/decisions/0011-b8-5-data-handling.md` | **Decided** (2026-11-19); what the lab endpoint keeps is **still to be recorded** |
| G-7 | Recording file names are `PENDING` in the inventory; the recording-team member who holds each file is not recorded | File names (no folders, no URLs) entered by the owner | **PENDING** |
| G-8 | Not confirmed that the five local files are the official B8.5 recordings and not temporary Video-pipeline test clips | Owner (Student 4) confirms in writing, in the PR or decision record | **PENDING OWNER** |
| G-9 | Unmerged work: commit `9c6d703` (the five measured durations) was not on `main` | A PR from that branch by its owner | **Resolved**: PR #154 (merged) put the five durations on `main` |
| G-10 | No openly licensed source is used: the licence path in PRD §B8.5 ("openly licensed, licence verified and recorded") is not exercised. The project chose the consent path | None, unless the guide changes the decision | Informational |

## 4. Required handling of a recording whose consent or licence evidence is missing

Rules 1 to 7 restate decision 0004 and `docs/data-map.md`. Rule 8 onward are **PROPOSED and need
the guide's approval**; nothing in this section is an approved policy.

1. A recording with no consent line is **not** official B8.5 evidence, whatever it contains.
   Consent is never inferred from the recording existing, from the speaker being a team member, or
   from the speaker having been present.
2. It stays only on the computer of the team member who recorded it, in a folder that is not synced
   or backed up to any cloud service, outside the repository.
3. It is never committed, uploaded, shared, attached to a PR or issue, or linked. This includes
   extracted audio, unreviewed transcript drafts and thumbnails.
4. It is not used for any measurement (caption word error rate, G-6, App-C 7) or as input to any
   model or speech provider.
5. No transcript from it is published until its speaker's consent line exists.
6. Its inventory row keeps `PENDING` in the Speaker and Consent cells and `pending` in review.
7. Nobody writes a consent line for another person.
8. **PROPOSED:** if a speaker declines or withdraws, the recording is excluded from the set, the
   inventory row returns to `PENDING`, and the owner asks the guide how to handle deletion of the
   file and of any published name or transcript. **Decided by the guide on 2026-11-19 (decision 0011):** a withdrawing speaker is removed from the current tree, the withdrawal is recorded, and Git history is not rewritten.
9. **PROPOSED:** if the set cannot reach five consented lectures, the owner reports it to the
   guide; the requirement is not reduced by anyone else.

## 5. Separation from synthetic and temporary test data

Synthetic recordings, synthetic transcripts and synthetic word-error-rate results (for example the
synthetic cases in `libs/contracts/tests/test_b8_5_dataset.py`, PR #89) test the **checker**, not the
dataset. They cannot satisfy T7, T11 or App-C 8 and must never be written into the B8.5
inventory. Temporary clips used to test the Video pipeline are likewise outside B8.5 until the owner
confirms otherwise in writing (G-8).

## 6. T7 official-dataset evidence checklist

Only items required by the repository's requirements are listed.

| # | Required item | Source | State |
|---|---|---|---|
| 1 | At least 5 recordings exist | Decision 0004 | Local files exist (5); owner confirmation of official status **PENDING** (G-8) |
| 2 | Total at least 1800 s | Decision 0004 | **Not met (338 s)**; temporary exception recorded in decision 0004 (guide, issue #121, PR #125) |
| 3 | Duration of each measured with `ffprobe` and recorded | Decision 0004 | Measured in this audit; recorded on `main` by PR #154 (G-9 resolved) |
| 4 | SHA-256 of each recording | Set README | On `main`; verified 5 of 5 locally in this audit |
| 5 | Recording file name in the inventory | Set README | **PENDING** (G-7) |
| 6 | Speaker per lecture | Set README | **PENDING** (G-2) |
| 7 | Consent line per speaker | Decision 0004, App-C 8 | **PENDING** (G-1) |
| 8 | Outline per lecture | Set README | **PENDING** placeholder |
| 9 | Reference transcript per lecture | PRD B8.5 | **PENDING** placeholder (G-4) |
| 10 | Transcript review by Harshitha | Decision 0004 | **PENDING** |
| 11 | Total line and `COMPLETE` status only when all of the above hold | Test `test_b8_5_dataset.py` | Correctly `PENDING` |
| 12 | Nothing but the permitted paths tracked under `testdata/b8-5-lecture-videos/` | Set README | Verified by test (below) |

The PRD does not specify further provenance metadata, evaluation inputs or file formats for B8.5;
none are invented here.

## 7. Verification actually run

| Command | Result |
|---|---|
| `python -m pytest -q libs/contracts/tests/test_b8_5_dataset.py` (worktree `learnops-r0-audit`, first pass at `3abbc02`) | `71 passed in 18.55s` |
| Same command, second pass, branch merged with `origin/main` `ecb4389`, exit code 0 | `71 passed in 5.19s` |
| Same command, third pass (2026-11-20), branch merged with `origin/main` `5f3a794` | `71 passed in 33.48s` |
| SHA-256 and `ffprobe` check described in §2 (first pass) | 5 of 5 hash matches; durations 62/82/43/68/83 s; total 338 s |
| Same local check repeated in the second pass (also searching `.m4v`, `.wav`, `.mp3`) | 5 of 5 distinct hash matches; identical durations; total 338 s; 0 copies inside any `learnops*` folder |
| `git ls-files testdata/b8-5-lecture-videos` | Only `.gitignore`, `README.md` and `outline.md` / `transcript.en.txt` for lectures 01 to 05: no media tracked |
| Full `python -m pytest -q` in a clean venv with `requirements-dev.txt` pinned versions | `1 failed, 2044 passed, 4 skipped`; the one failure is `test_validate_examples.py::test_misnamed_schema_is_reported_with_its_path[Thing.v1.schema.json]` (PR #92 code, not B8.5). Likely cause, not proven by a Linux run: Windows' case-insensitive filesystem makes `Thing.v1…` overwrite `thing.v1…` in the test tree. CI runs on Linux |

The pytest result shows the committed placeholders are well formed and the `PENDING` status is
truthful. It does not show that B8.5 or App-C 8 is met.

## 8. Not verified, and what a person must still do

- That each speaker consented, and was told about interim storage (G-1, G-3).
- That the recordings are Indian-English technical lectures spoken from an outline.
- That the files are the official set (G-8).
- Transcript accuracy and review (G-4).
- The date of the guide's earlier approval of the 1800 s exception (G-5). The guide's decisions on retention, storage, names and transcripts and processing services are recorded in decision 0011; what the lab endpoint keeps is still to be recorded (decision 0002).
