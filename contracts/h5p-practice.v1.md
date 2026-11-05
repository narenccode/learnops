# B7 H5P practice output (v1)

**Status:** Draft. Not approved. **Provisional: it cannot be frozen** until the H5P library versions
are verified in the lab (guide's answer to question 5, Issue #44; PRD App-C item 5).
**Owner:** Student 1. **Used by:** Module 1 (Course Studio), Module 2 (course checker, for CK-11) and
Module 4 (video pipeline); M2 was added to the PRD B.0 table in this pull request (guide, Issue #44).
**Source:** PRD §B7, B1.1, B1.2, B6.2, C-08, C-09, FR-S-12, FR-V-14, FR-C-03 (CK-11, CK-12). Where
this file and the PRD differ, the PRD wins.

Release 0 is not frozen (guide's answer 1). This file, its schema and the B1 `file` field change by
a normal pull request using `/contract-change`. After the freeze they change only by adding optional
fields (PRD B.0 rule 2, EXT-02); a breaking change needs `h5p-practice.v2`.

## 1. Scope

B7 describes what Course Studio (FR-S-12) and the video pipeline (FR-V-14) hand over when they
produce **ungraded H5P practice** for a course: which content types, how a practice item appears in
a course package, and which rules it must obey.

**Practice is optional.** The standard week stays one guide Page and one task Assignment (PRD
B1.2 rule 1); an H5P practice item is an optional extra and never replaces either (guide, Issue #44).

B7 does **not** cover:

- how questions are drafted. That is the model interface (B5);
- the Moodle backup (`.mbz`) structure for H5P activities (Studio's technical requirement, PRD C1.5);
- what the future player does at a cue (FR-X-12, Release 6);
- the structure of `cues.json`. B6 owns it; B7 defines **no second format** (section 6).

## 2. What the guide decided (Issue #44)

| Q | Decision | Where it is applied |
|---|---|---|
| 1 | Release 0 is not frozen; B7 goes through a normal pull request with `/contract-change`. | This file, header |
| 2 | B1 gets a `file` field on `h5p` activities: a relative path ending in `.h5p`, same rule as `body`. Same pull request. | Section 4, B1 schema |
| 3 | No ordering field. The list order is the order; B7 says the `h5p` entry comes right after the guide Page. Applied to ordinary optional practice only; video checkpoints stay open (sections 4 and 6). | Section 4 |
| 4 | B7 is `h5p-practice.v1.md` plus a small schema and an example listing the allowed content types, like B4. | Sections 3 and 8 |
| 5 | H5P library versions are provisional, marked "to verify in the lab". B7 cannot freeze before they are known. | Section 3 |
| 6 | Do not define a second format. `cues.json` belongs to B6. Which `ref` kinds it allows is for Student 4 to say. | Section 6 |
| 7 | No real `.h5p` file in the repository. The example is a `course.yaml` that points to a path. This rule is written here because `.gitignore` does not block `.h5p`. | Section 5 |

## 3. Content types

PRD B7 names these content types, and this file uses its wording. The schema
(`h5p-practice.v1.schema.json`) allows only these four phrases, each at most once, and its example
(`examples/h5p-practice.v1.content-types.json`) lists all four.

| Content type (PRD B7 wording) | Where it may be used | H5P library and version |
|---|---|---|
| question set | Courses (checkpoints) | **to verify in the lab** |
| drag-the-words or drag-and-drop / ordering | Courses | **to verify in the lab** |
| branching scenario | Courses | **to verify in the lab** |
| interactive video | Lab demonstrations only, with openly licensed videos | **to verify in the lab** |

- **No H5P machine name and no version is invented here. OPEN DECISION: library versions.** The
  exact library versions available on Moodle 4.5 and 5.3 are verified in the lab (PRD App-C item 5)
  and added if needed. Until then B7 cannot be frozen. Results are recorded in `docs/decisions/`, as
  for B4.
- **Interactive video is for lab demonstrations only** (PRD B7; see the table). The schema does not
  mark this; it is a rule of this text and is not enforced (section 8). A boolean field in the data
  was considered and left out because no answer approves it; it is a question for reviewers.
- **OPEN DECISION: the second row.** The PRD says "drag-the-words or drag-and-drop / ordering". The
  schema keeps that phrase as one literal entry and does not decide whether it is one content type
  or a choice between several. The lab check and the guide decide.

## 4. The practice item in a course package

PRD B7: each practice item is a standard `.h5p` file plus an entry in `course.yaml`. The entry is
defined by B1 (`contracts/course-package.v1.schema.json`), not by this file:

| Field | Rule |
|---|---|
| `type` | `h5p` |
| `idnumber` | Lowercase ASCII letters and digits separated by single hyphens; unique in the course; not a protected idnumber (B1.2 rule 6, B1.4) |
| `title` | Non-empty text |
| `graded` | Required, and always `false` |
| `file` | **Required.** A relative path ending in lowercase `.h5p`. The same path rules as `body`: not a URL, not absolute, no `..` segment, no backslash |

- `file` is defined for `h5p` activities only. On any other activity type it is an unknown field and
  is not checked.
- The schema checks the shape of `file` only. It does not look for the file.
- The example (`examples/h5p-practice.v1/course.yaml`) uses the illustrative name
  `wk-01-practice.h5p`. B7 does not fix a folder or a naming convention.
- **Placement of ordinary optional practice:** there is no ordering field. The order of the
  `activities` list is the order, and the practice entry comes right after the week's guide Page
  (guide's answer 3). This is not checked by any schema or validator yet (section 8). It does not
  cover video checkpoints (next points).
- **OPEN DECISION: several practice items in one week.** Not decided. This file makes no rule about
  how many there may be or how they are ordered among themselves. The guide decides.
- **OPEN DECISION: video checkpoint placement.** PRD B7 says a video checkpoint is "a separate
  activity after the video"; the guide's answer 3 covers only the entry after the guide Page. Where
  a video checkpoint goes is not decided here (section 6). The guide decides.

## 5. Rules for every practice item

| # | Rule | Source |
|---|---|---|
| R1 | A practice item is **never graded**. It has no grade item. | PRD B7, B1.2 rule 1 |
| R2 | It is **optional**. A week without one is a complete week. | Guide, Issue #44; PRD B1.2 rule 1 |
| R3 | **AI output is a draft.** A practice item drafted with AI reaches learners only after a mentor approves it. In Studio the mentor can keep, edit, regenerate or drop each draft. | PRD C-09, FR-S-12; root `CLAUDE.md` §2 rule 5 |
| R4 | Media is referenced by a **relative path**, never a full URL. | PRD C-08; root `CLAUDE.md` §2 rule 7 |
| R5 | **No real `.h5p` file is kept in the repository.** Examples and tests point to a path only. `.gitignore` does not block `.h5p`, so this rule is stated here and checked by a test. | Guide, Issue #44 (answer 7); root `CLAUDE.md` §2 rule 4 |

PRD FR-S-12's review card (question, correct answer, distractors, explanation) is behaviour of
Studio. **B7 v1 defines no JSON structure for a draft or a review card.**

## 6. Video checkpoints

PRD B7 and FR-V-14 give two modes. The default is a separate activity after the video: a practice
item as in sections 4 and 5, whose placement is an OPEN DECISION (section 4); the guide-page
placement rule is not applied to it. The other is `cues.json` entries for the future player (F-1).

**B7 does not define a cue structure.** `cues.json` is owned by B6 (PRD B6.2: optional, "moments
where an activity should appear"; the manifest field `cues` holds its path). The guide has said
small schemas for `chapters.json`, `slides.json` and `cues.json` come in a separate pull request
before the end of Release 0 (guide's comment on PR #32). B7 follows whatever that schema says.

**PROVISIONAL — pending the B6 cue schema PR.** Student 4 has said (Issue #44, 2026-11-05) that the
B6 `cues.json` schema is not finalized, that she will add it in a separate pull request, and that
the B6 schema will own the cue fields and their validation rules. What follows is her proposal. It is
**not** a B7 requirement. B7 does not enforce it, and no B7 schema, example or test uses it. If the
B6 schema says otherwise, the B6 schema wins and this block is corrected.

- Proposed cue for a B7 practice item: `{"type": "h5p", "ref": "<activity-idnumber>"}`. The `ref`
  would be the plain Moodle `idnumber` of the practice item in `course.yaml`, resolved within the
  course (EXT-06: activities are identified by `idnumber`, never by position or display name).
- Proposed rules for the cue fields, all pending the B6 schema: `t` is a required, non-negative
  number of seconds (like `duration_s`); `type` is required and comes from a cue-type list not yet
  agreed; `ref` is required and its format depends on the type; `label` is required and not empty;
  `t` lies within the media duration; and `ref` resolves to a resource of the matching type.

- **OPEN DECISION: the `ref` kinds.** Which kinds of reference a cue may carry is for Student 4 to
  answer in the B6 schema (guide, Issue #44, answer 6). PRD FR-X-12 shows more than H5P: "an H5P
  from B7, a whiteboard image, a scenario, or an external activity URL allowed by configuration".
  The proposal above covers only the practice-item case and is itself provisional.
- PRD FR-X-12 also says a learner can skip a cue "unless the cue is marked `required`". Where that
  mark is stored is not defined, and is B6's to define.

## 7. Dependencies

| Depends on | What B7 relies on |
|---|---|
| B1 course package | The `h5p` entry in `course.yaml`, including the `file` field added with B7 |
| B2 course model | `grade_item: null` as "no grade item", read by CK-11. B2 is Student 2's contract (a draft when this was written) |
| B5 model interface | AI drafts of the questions (FR-S-12, FR-V-14) |
| B6 lesson manifest | `cues.json` and its path (section 6). B6 is Student 4's contract (PR #32); B6 owns `cues.json`. Its cue schema is not written yet and is due before the end of Release 0; section 6 holds only a provisional proposal |

## 8. What is enforced where

"Not enforced" means nothing in the repository checks it today. The rules that schemas and tests do
enforce (`h5p` as an allowed activity type and its `graded` and `file` fields in the B1 schema, the
content-type list, the "nothing invented" rules, the example package, and the rule of no `.h5p`
file) are listed with their tests and PRD references in `docs/traceability.md`, section "B7 H5P
practice output contract". The placement and the standard week of the example package are checked
on that example only, not on packages in general.

**Planned checker rules (Module 2, Release 1, not built):** CK-11, a practice (H5P) activity has no
grade item (the B1 schema already rejects `graded: true` in a package; CK-11 checks the course
model, B2, where PRD B7 says "the checker enforces this"); CK-12, media referenced by a full URL.

**Not enforced by anything yet** (each is in the traceability table "Documented but not
automatically enforced"): placement (section 4), video checkpoints (sections 4 and 6), whether the
file named by `file` exists (section 4), interactive video only in lab demonstrations (section 3),
`cues.json` entries (section 6), the standard week of one Page and one Assignment (B1.2 rule 1), the
content type of the `.h5p` file, and mentor approval of AI drafts (a process rule of Studio).
