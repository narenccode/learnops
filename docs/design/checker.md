# Design document: Course checker, role tests, integration harness


**Module:** checker
**Owner:** @shraddha0103 · **Peer reviewer:** @Akshita21-09
**Release(s):** e.g. Release 2 (core), Release 5 (stretch)
**Status:** Draft

`Status` values: `Draft` → `In review` (peer reviewing) → `Approved`. **Only the guide sets
`Approved`**, in a pull request the guide merges. Feature code for this module starts only when the
status is `Approved` (foundation work listed in §13 under "Release 0" is allowed earlier).

## 1. Purpose and scope

The Course Checker identifies course-design errors before learners encounter them, verifies what different user roles can and cannot access through a real browser, and runs an integration test of the LearnOps toolkit. It checks course structure, activity availability, completion rules, grading totals, and other defined validation rules, then produces reports describing detected problems and suggested fixes. It also runs browser-based role tests across three screen profiles and Moodle versions 4.5 and 5.3. As integration lead, this module provides a single-command harness that builds a sample course, checks it, restores it on both Moodle versions, runs role tests, and generates a consolidated report.

**PRD chapter and goals served:** Part C, Section C2 — Course Checker. The module supports Release 1 (core), with the integration harness extended in subsequent releases. Its goals include detecting planted course-design errors without false positives, validating role permissions across screen profiles and Moodle versions, and verifying end-to-end integration.

**Out of scope:** Automatically fixing course errors, load testing, and checking quiz or workshop settings. The checker reports problems and suggests fixes; it does not automatically modify courses.

## 2. Requirements covered

| Requirement | Release | Approach in one line | Main components |
|---|---|---|---|
| FR-X-01 | R? | … | … |

Every requirement tagged for your releases in PRD §C appears here. Mark any you propose to defer
and say why.

## 3. Architecture

- Diagram of the components and how data flows between them (Mermaid is fine).
- Which parts are a **web service**, a **worker**, a **CLI**, and a **shared library** (PRD OPS-10:
  heavy work never runs inside a web request).
- Where the module touches Moodle, BigBlueButton, the model interface and the media store, and
  **only through the allowed routes** (PRD C-02).

## 4. Contracts

| Contract | Provided / used | Fields or functions I rely on | Change needed? |
|---|---|---|---|
| B? | | | none (after Release 0: additive only, via `/contract-change`) |

## 5. Data model

- Tables in the module's schema (`studio`, `checker`, `grading` or `video`): columns, types, keys.
- Migrations: how each is reversed.
- What is stored relative vs absolute (media: **relative paths only**, PRD C-08).

## 6. Interfaces

- **Web/API:** routes, request and response shapes, who may call them (role from the LTI launch).
- **CLI:** each command with `--dry-run`, `--check`, exit codes and its **undo** (PRD OPS-05).
- **Configuration:** each environment variable, its default, and whether it is in `.env.example`.

## 7. Key decisions and alternatives

| Decision | Alternatives considered | Why this one | Record |
|---|---|---|---|
| … | … | … | `docs/decisions/NNNN-title.md` |

## 8. Libraries and licences

| Library | Pinned version | Licence | Why needed | Alternative |
|---|---|---|---|---|

Licences must be MIT, BSD or Apache-2.0 (LGPL only as an unmodified library): PRD C-11.

## 9. Security and privacy

- Which of SEC-01…09 apply to this module and how each is met.
- Data this module stores or sends to an AI provider, for `docs/data-map.md`.
- Anything that handles untrusted input (uploads, learner code, URLs) and how it is contained.

## 10. Error handling

- Validation errors, system errors, user-facing messages and recovery actions (PRD UI-05, C.x.8).
- What happens when Moodle, BigBlueButton, the model provider or storage is unavailable.

## 11. Test plan

| Level | What is tested | Test data | Requirement IDs |
|---|---|---|---|
| Unit | | | |
| Contract | | | |
| Integration (harness) | | | |
| End-to-end | | | |

- How each **acceptance criterion** in the PRD chapter (§C.x.7) will be demonstrated.
- How each **metric** will be measured (data set, method, who measures).

## 12. Risks and open questions

| # | Risk or question | Needs the lab? | Plan or owner |
|---|---|---|---|
| 1 | | | |

Include every PRD Appendix C item that affects this module.

## 13. Work breakdown

Ordered list. **One requirement (or one tightly related group) per pull request.**

| Order | Pull request | Requirements | Depends on | Notes |
|---|---|---|---|---|
| 1 | | | | |

Mark the ones that are Release 0 foundation work (contracts, shared libraries, CI) with
"Release 0": those may start before this document is approved.

## 14. Review and approval

- [ ] Owner: I understand and can explain every section.
- [ ] Peer reviewer: checked against the PRD chapter and the contracts; comments resolved.
- [ ] Guide: approved (sets `Status: Approved`).
