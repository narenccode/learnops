# Design document: Course Studio


**Module:** studio
**Owner:** @Akshita21-09 · **Peer reviewer:** @shraddha0103
**Release(s):** Release 2 (core), Release 5 (stretch)
**Status:** Draft

`Status` values: `Draft` → `In review` (peer reviewing) → `Approved`. **Only the guide sets
`Approved`**, in a pull request the guide merges. Feature code for this module starts only when the
status is `Approved` (foundation work listed in §13 under "Release 0" is allowed earlier).

## 1. Purpose and scope

Course Studio helps mentors create and manage course content more efficiently using structured text or forms. It validates course packages, previews course content, and generates Moodle backup files (`.mbz`) that administrators can restore using Moodle's own Restore feature. It also supports importing existing Moodle backups back into editable course packages. The main goal is to reduce the time required to load a four-week course to 15 minutes or less, compared with the current 2–3 hours.

**PRD chapter and goals:** PRD §C1 — Course Studio; Goal G-1 — Fast course creation.

**Out of scope:** Editing live Moodle courses directly, quizzes and Moodle-stored rubrics, and workshops. Course Studio will generate backup files for administrators rather than directly modifying Moodle courses. These exclusions follow PRD §C1.11 and the system constraints in PRD §A7.

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
