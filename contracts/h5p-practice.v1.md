# B7 H5P practice output (v1)

**Status:** Complete for Release 0: no open decision remains. The H5P library versions were verified
in the lab on 2026-11-11 (the guide's lab check, PRD App-C item 5) and are pinned in section 3. The
last three open decisions were settled on Issue #186 (2026-11-26): the two placement rules by the
guide (section 4), and the cue `ref` kinds by the B6 cue schema (section 6). Approved under PRD B.0
rule 3 by an affected owner on the pull request that set this line; frozen with the other contracts
at the Release 0 freeze.
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
| 3 | No ordering field. The list order is the order; B7 says the `h5p` entry comes right after the guide Page. Extended on Issue #186 (2026-11-26) to several practice items and to video checkpoints (below). | Section 4 |
| 4 | B7 is `h5p-practice.v1.md` plus a small schema and an example listing the allowed content types, like B4. | Sections 3 and 8 |
| 5 | H5P library versions were provisional, marked "to verify in the lab". The guide's lab check of 2026-11-11 verified them on both lab sites. They are pinned in section 3 and recorded in `docs/decisions/0008-h5p-content-types.md`. | Section 3 |
| 6 | Do not define a second format. `cues.json` belongs to B6. Which `ref` kinds it allows is for Student 4 to say; the B6 cue schema now says it. | Section 6 |
| 7 | No real `.h5p` file in the repository. The example is a `course.yaml` that points to a path. This rule is written here because `.gitignore` does not block `.h5p`. | Section 5 |

Decided later, on Issue #186 ([guide's answer, 2026-11-26](https://github.com/narenccode/learnops/issues/186#issuecomment-7187497222), to [Student 1's question](https://github.com/narenccode/learnops/issues/186#issuecomment-7187026830)):

| Q | Decision | Where it is applied |
|---|---|---|
| 8 | Any number of practice items in a week. They form one run directly after the guide Page, in the order of `activities`, with nothing between them. | Section 4 |
| 9 | A video checkpoint goes directly after the Page that embeds the lesson video, in the same section; if that Page is the guide Page, it comes after the practice run. A rule for Course Studio and the video pipeline, not a validation error. | Sections 4 and 6 |
| 10 | Close the `ref` kinds point by pointing to the B6 cue schema; set the Status line; leave the 4.5 lab record as it is (decision 0017). An affected owner approves under PRD B.0 rule 3; no PRD text changes. | Header, sections 3 and 6 |

## 3. Content types

PRD B7 names these content types, and this file uses its wording. The guide's lab check of
2026-11-11 (both lab sites, Moodle 4.5 and 5.3) found the five H5P libraries below installed and
runnable. The schema (`h5p-practice.v1.schema.json`) allows only these five names, each at most
once, and pins each one to its library (`machine_name`) and exact `version`. Its example
(`examples/h5p-practice.v1/content-types.json`) lists all five.

| Content type (PRD B7 wording) | H5P library (machine name) | Version | Where it may be used |
|---|---|---|---|
| question set | `H5P.QuestionSet` | 1.21.14 | Courses (checkpoints) |
| drag-the-words | `H5P.DragText` | 1.10.50 | Courses |
| drag-and-drop | `H5P.DragQuestion` | 1.15.37 | Courses (also used where ordering is needed) |
| branching scenario | `H5P.BranchingScenario` | 1.11.2 | Courses |
| interactive video | `H5P.InteractiveVideo` | 1.28.37 | Lab demonstrations only, with openly licensed videos |

- **Pinned for Release 0 (guide, PR #54, 2026-11-11).** These are the versions that Moodle's own
  scheduled task downloaded from h5p.org on 2026-11-11. h5p.org may publish newer ones, so B7 pins
  these exact versions for the Release 0 tests, and a change is made only through a
  `/contract-change`. The result is recorded in `docs/decisions/0008-h5p-content-types.md` (PRD
  App-C item 5).
- **Two entries, and one type per practice item.** "drag-the-words" and "drag-and-drop" are two
  separate H5P libraries, so they are two entries. Each practice item uses one of them, and in
  general one of the five types.
- **Ordering is not a separate content type in v1.** Where ordering is needed, it is done with
  Drag and Drop. A later release can add a type as an optional entry (an additive change, PRD B.0
  rule 2).
- **Interactive video is for lab demonstrations only** (PRD B7; see the table). The schema does not
  mark this; it is a rule of this text and is not enforced (section 8). A boolean field in the data
  was considered and left out because no answer approves it, so v1 has none; a later release can
  add one as an optional field (PRD B.0 rule 2).
- The schema checks the names and the pins. It does not check that an `.h5p` file really uses one
  of these libraries at that version (section 8).

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
- The example (`examples/course-package.v1/h5p-practice.yaml`, a B1 package whose bodies are in
  `examples/course-package.v1/h5p-practice/`) uses the illustrative path
  `h5p-practice/wk-01-practice.h5p`. B7 does not fix a folder or a naming convention.
- **Placement of ordinary optional practice:** there is no ordering field. The order of the
  `activities` list is the order, and the practice entry comes right after the week's guide Page
  (guide's answer 3).
- **Several practice items in one week:** any number is allowed. They form **one run directly after
  the guide Page**, in the order of `activities`, with nothing between them (decision 8).
- **Video checkpoint placement:** PRD B7 says a video checkpoint is "a separate activity after the
  video". In a course the video is embedded in a Moodle Page (FR-V-13), so the checkpoint goes
  **directly after the Page that embeds the lesson video**, in the same section. If that Page is the
  guide Page, the checkpoint comes **after the practice run** (decision 9).
- These placement rules are rules for Course Studio (FR-S-12) and the video pipeline (FR-V-14), the
  producers of practice items. They are **not validation errors**: neither B1 nor a validator can
  tell which Page embeds a video, and the guide-Page rule is not checked by any schema or validator
  either (section 8).

## 5. Rules for every practice item

| # | Rule | Source |
|---|---|---|
| R1 | A practice item is **never graded**. It has no grade item. | PRD B7, B1.2 rule 1 |
| R2 | It is **optional**. A week without one is a complete week. | Guide, Issue #44; PRD B1.2 rule 1 |
| R3 | **AI output is a draft.** A practice item drafted with AI reaches learners only after a mentor approves it. In Studio the mentor can keep, edit, regenerate or drop each draft. | PRD C-09, FR-S-12; root `CLAUDE.md` §2 rule 5 |
| R4 | Media is referenced by a **relative path**, never a full URL. | PRD C-08; root `CLAUDE.md` §2 rule 7 |
| R5 | **No real `.h5p` file is kept in the repository.** Examples and tests point to a path only. `.gitignore` does not block `.h5p`, so this rule is stated here and checked by a test. | Guide, Issue #44 (answer 7); root `CLAUDE.md` §2 rule 4 |
| R6 | A practice item uses **one** of the content types in section 3. This is not enforced: the content type is inside the `.h5p` file, and `course.yaml` holds only a path to it. | Guide, PR #54 (2026-11-11) |

PRD FR-S-12's review card (question, correct answer, distractors, explanation) is behaviour of
Studio. **B7 v1 defines no JSON structure for a draft or a review card.**

## 6. Video checkpoints

PRD B7 and FR-V-14 give two modes. The default is a separate activity after the video: a practice
item as in sections 4 and 5, placed directly after the Page that embeds the lesson video (section
4, decision 9). The other is `cues.json` entries for the future player (F-1).

**B7 does not define a cue structure.** `cues.json` is owned by B6 (PRD B6.2: optional, "moments
where an activity should appear"; the manifest field `cues` holds its path). Its schema is
`contracts/cues.v1.schema.json` (Student 4), and B7 follows it. For a B7 practice item, a cue has
`type: "h5p"` and a `ref` that is the practice item's Moodle `idnumber` in `course.yaml`, resolved
within the course (EXT-06: activities are identified by `idnumber`, never by position or display
name).

- **The `ref` kinds (settled by B6).** The B6 cue schema supports three types in v1: `h5p` (`ref`:
  an activity `idnumber`), `image` (`ref`: a path relative to the lesson folder) and `url` (`ref`:
  an absolute https address). A branching scenario is a B7 practice item and uses `h5p`. The guide
  gave this point to Student 4 (Issue #44, answer 6); B7 adds no rule to it.
- The `required` mark of PRD FR-X-12 (a learner cannot skip the cue) is the optional `required`
  field of the B6 cue. B7 adds no rule to it either.

## 7. Dependencies

| Depends on | What B7 relies on |
|---|---|
| B1 course package | The `h5p` entry in `course.yaml`, including the `file` field added with B7 |
| B2 course model | `grade_item: null` as "no grade item", read by CK-11. B2 is Student 2's contract (a draft when this was written) |
| B5 model interface | AI drafts of the questions (FR-S-12, FR-V-14) |
| B6 lesson manifest | `cues.json` and its path (section 6). B6 is Student 4's contract (PR #32); B6 owns `cues.json`, and its cue schema is `contracts/cues.v1.schema.json` |

## 8. What is enforced where

"Not enforced" means nothing in the repository checks it today. The rules that schemas and tests do
enforce (`h5p` as an allowed activity type and its `graded` and `file` fields in the B1 schema, the
pinned content-type list with its machine names and versions, the example package, and the rule of
no `.h5p` file) are listed with their tests and PRD references in `docs/traceability.md`, section "B7 H5P
practice output contract". The placement and the standard week of the example package are checked
on that example only, not on packages in general.

**Planned checker rules (Module 2, Release 1, not built):** CK-11, a practice (H5P) activity has no
grade item (the B1 schema already rejects `graded: true` in a package; CK-11 checks the course
model, B2, where PRD B7 says "the checker enforces this"); CK-12, media referenced by a full URL.

**Not enforced by anything yet** (each is in the traceability table "Documented but not
automatically enforced"): placement, including the practice run and video checkpoints (section 4;
rules for Studio and the video pipeline, not validation errors), whether the
file named by `file` exists (section 4), interactive video only in lab demonstrations (section 3),
that a cue's `h5p` `ref` names an activity in the course (section 6; the B6 schema checks the cue's
shape only), the standard week of one Page and one Assignment (B1.2 rule 1), the
content type, library and version the `.h5p` file really uses, and mentor approval of AI drafts (a
process rule of Studio).

**Held rule `h5p_files_not_checked` (B7).** The package validator (`libs/contracts`) lists it in every
report. It does not look for the `.h5p` file, does not check that it is valid and does not read the
content type, library or version inside it. So "no errors" does not mean the file was found, and it does not mean that
interactive video (lab demonstrations only) was not used.
