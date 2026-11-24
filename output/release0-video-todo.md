# Release 0: what only YOU can do as Video owner (22 Nov 2026)

Tick `- [x]` as you go. This is a new file; your older list `pr-todo.md` is untouched.
Repo: https://github.com/narenccode/learnops

## Already done for you (PRs ready for review: please ask your peers to review them)

| PR | What | Needs |
|---|---|---|
| [#154](https://github.com/narenccode/learnops/pull/154) | The five B8.5 durations on `main` | Peer review |
| [#155](https://github.com/narenccode/learnops/pull/155) | `media_paths` README: install, configure, run, check, undo | Peer review |
| [#156](https://github.com/narenccode/learnops/pull/156) | App-C 9 record (decision 0012): Moodle 5.3 AI features, source-checked | Peer review; its CI is red only because `main` is red (see "Not mine" below) |
| [#106](https://github.com/narenccode/learnops/pull/106) | Literature P9–P12 added, now ready for review | Peer review; your verification |
| [#104](https://github.com/narenccode/learnops/pull/104), [#105](https://github.com/narenccode/learnops/pull/105) | Status wording fixed after Harshitha's review | Re-review |
| [#140](https://github.com/narenccode/learnops/pull/140) | Design doc, Harshitha's 5 points fixed | Re-review, then your `In review` step |

## 1. Send / provide (nobody else has these)
- [ ] **Lab speech facts for PR #98** (non-secret only: model and size, engine and version, hardware, request format and limits, authentication method, whether word timestamps are returned). Never IPs, VM addresses or credentials. Give them to me and I will record them.
- [ ] **What the lab speech endpoint keeps** after processing (for the data map and decision 0011).
- [ ] **The lab image's `ffmpeg -version` output** (the configuration line). The guide needs it before an LGPL build is relied on.
- [ ] **Moodle 5.3 lab check for App-C 9:** ask whoever is a Moodle administrator on the lab 5.3 site to look at Site administration, AI: which providers and placements are installed and enabled, and the real Moodle build. Send me the result (no address or credential) and I add it to decision 0012 (#156).

## 2. B8.5 data (you have it ready: start this PR)
- [ ] Confirm in writing in the PR that the five local files are the **official** B8.5 recordings, not pipeline test clips (audit gap G-8).
- [ ] Fill the inventory in `testdata/README.md`: title, speaker, recording **file name only** (no folder, no URL). #154 already adds the durations.
- [ ] Add `outline.md` and `transcript.en.txt` per lecture (Apache-2.0).
- [ ] Each speaker writes **their own** consent line in `docs/decisions/0004-b8-5-lecture-videos.md` (name, date, the exact sentence). Nobody writes a line for another person. Tell each speaker first that a withdrawal removes the name from the current files but older versions stay in Git history (needs #104 merged, or merge `main` first).
- [ ] Ask **Harshitha** to review each transcript; only then change the review column to `checked`.
- [ ] Keep the Status `PENDING` (338 s of 1800 s; the guide's exceptions do not make it complete). Keep recordings, audio and drafts out of Git.
- [ ] Split into PRs of about 800 lines or fewer if it grows.

## 3. Reviews and approvals you must request or give
- [ ] Ask peers to review #154, #155, #156, #106, #104, #105, #140. After any push to an approved PR, the reviewer clicks **Re-request review** (rule #149). I never click approve or merge.
- [ ] #129: ask Akshita to re-review (her change request stands), Harshitha for the Video peer review, and the guide to approve the head.
- [ ] **Your peer duty:** review Harshitha's open PRs (Grading is your pair): #150, #151, #152, #153, #139 and the `moodle_ws` PRs (#76, #79, #80).

## 4. Your own sign-offs
- [ ] **Design document (#140):** read every **Proposed** part until you can explain it, tick the §14 owner box, then set it `In review`. Only the guide sets `Approved`, in a PR he merges.
- [ ] **Literature (#106):** open and verify each of P1–P12 yourself and read P3, P8, P10 and P12 properly. The count is **1 of 6** until you verify; the survey still has gaps (privacy and consent law, Moodle video embedding, modern lecture segmentation and summarisation).
- [ ] **B6 freeze sign-off:** as owner of B6 ask the users of B6 (Module 1, Module 2 and the player owners) and the guide to approve under PRD B.0. Nothing records it yet. I can draft the message.
- [ ] **Decision-number clash:** tell the guide that two records are numbered `0001` (`0001-lti-library.md` and `0001-b5-model-interface-v1.md`); he decides which is renumbered.

## 5. Lab BigBlueButton (formally Release 3, but you own the evidence)
- [ ] Get access to the lab BigBlueButton, run `docs/decisions/evidence/0005-app-c-4-bbb/verify_bbb.py` against it, and fill the PENDING cells in decisions `0005` and `0006`. Never write the address or secret into the repository.

## 6. Later, after the evaluation
- [ ] When the last B8.5 measurement is recorded (the Release 3 word error rate included), delete your local recordings, delete the lab copies and scratch files, and record the deletion in the evidence (decision 0011).

## Not mine to do, but you should know
- **`main` CI is red** since PR #138 (the Moodle 4.5 note in the PRD): `test_moodle_ws_v1.py::test_the_grade_value_source_is_only_a_pending_proposal` now sees the text twice. #138 belongs to Harshitha; the freeze needs a green `main`. #156 and #106 fail only for this reason.
- **Release 0 mechanics** (the "Release 0" issue, release PR, `CHANGELOG.md`, `docs/releases/r0.md`, the security review, the tags and the adoption test) belong to the release owner and the guide, not to you. Contribute your module's notes when they ask.
- **Design approvals, the contract freeze and the lab matrix** are the guide's.

## What I did not do and why
- **`modules/video/README.md`:** no module has a README yet and Video has no runnable code, so it would say nothing true. It belongs with Release 3.
- **Anything that needs your voice:** consent lines, the "I understand every section" tick, verifying sources, and any approval.
