# B7 H5P practice output (v1)

**Status:** Draft. Not approved. **Provisional: it cannot be frozen** until the H5P library versions
are verified in the lab (guide's answer to question 5, Issue #44; PRD App-C item 5).
**Owner:** Student 1. **Used by:** Module 1 (Course Studio), Module 2 (course checker, for CK-11) and
Module 4 (video pipeline). The PRD B.0 table still names only M1 and M4; adding M2 is the guide's
decision (Issue #44, answer 1) and is proposed in the pull request, not made in this file's text.
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
B1.2 rule 1). An H5P practice item is an optional extra on top of that and never replaces either
(guide, Issue #44).

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

- **No H5P machine name and no version is invented here.** The exact library versions available on
  Moodle 4.5 and 5.3 are verified in the lab (PRD App-C item 5). Until then B7 cannot be frozen.
  Results are recorded in `docs/decisions/`, as for B4.
- **Interactive video is for lab demonstrations only**, with openly licensed videos (PRD B7). The
  schema does not mark this; it is a rule of this text and is not enforced (section 8.4). A boolean
  field in the data was considered and left out because no answer approves it; it is a question
  for reviewers.
- **OPEN DECISION: library versions.** Not known until the lab check. They will be added once
  verified, if needed.
- **OPEN DECISION: the second row.** The PRD says "drag-the-words or drag-and-drop / ordering". The
  schema keeps that phrase as one literal entry and does not decide whether it is one content type
  or a choice between several.

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
  (guide's answer 3). This is not checked by any schema or validator yet (section 8.4). It does not
  cover video checkpoints (next points).
- **OPEN DECISION: several practice items in one week.** Not decided. This file makes no rule about
  how many there may be or how they are ordered among themselves.
- **OPEN DECISION: video checkpoint placement.** PRD B7 says a video checkpoint is "a separate
  activity after the video". The guide's answer 3 is about the practice entry after the guide Page.
  Where a video checkpoint goes, and whether it differs, is not decided here (section 6).

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

PRD B7 and FR-V-14 give two modes:

| Mode | What is produced |
|---|---|
| A separate activity after the video (default) | A practice item as in sections 4 and 5. Its placement is an OPEN DECISION (section 4); the guide-page placement rule is not applied to it. |
| `cues.json` entries for the future player (F-1) | Entries in the lesson's `cues.json`. |

**B7 does not define a cue structure.** `cues.json` is owned by B6 (PRD B6.2: optional, "moments
where an activity should appear"; the manifest field `cues` holds its path). The guide has said
small schemas for `chapters.json`, `slides.json` and `cues.json` come in a separate pull request
before the end of Release 0 (guide's comment on PR #32). B7 follows whatever that schema says.

- **OPEN DECISION: the `ref` kinds.** Which kinds of reference a cue may carry is for Student 4 to
  answer (guide, Issue #44, answer 6). PRD FR-X-12 shows more than H5P: "an H5P from B7, a
  whiteboard image, a scenario, or an external activity URL allowed by configuration". Until the B6
  schema exists, B7 says nothing about `ref`.
- PRD FR-X-12 also says a learner can skip a cue "unless the cue is marked `required`". Where that
  mark is stored is not defined, and is B6's to define.

## 7. Dependencies

| Depends on | What B7 relies on |
|---|---|
| B1 course package | The `h5p` entry in `course.yaml`, including the `file` field added with B7 |
| B2 course model | `grade_item: null` as "no grade item", read by CK-11. B2 is Student 2's contract (a draft when this was written) |
| B5 model interface | AI drafts of the questions (FR-S-12, FR-V-14) |
| B6 lesson manifest | `cues.json` and its path (section 6). B6 is Student 4's contract (PR #32); B6 owns `cues.json` |

## 8. What is enforced where

"Not enforced" means nothing in the repository checks it today.

### 8.1 Enforced by the B1 schema, with tests in `test_course_package_v1.py`

| Rule | Detail |
|---|---|
| `h5p` is an allowed activity `type` | Enum |
| `graded` is present and `false` on an `h5p` activity | Missing, `true` or any other value is rejected |
| `file` is present on an `h5p` activity | Missing is rejected |
| `file` is a relative path ending in lowercase `.h5p` | URLs, absolute paths, `..`, backslashes, other or upper-case extensions and an empty name are rejected |
| `idnumber` format; the two default protected idnumbers are rejected | `final-project`, `course-feedback` |
| `file` is not checked on other activity types | It is an unknown field there |
| Unknown fields are accepted | PRD EXT-02 |

### 8.2 Enforced by the B7 schema and tests, in `test_h5p_practice_v1.py`

| Rule | Detail |
|---|---|
| The schema allows only the four PRD B7 phrases, each at most once; invented names, other capitals and machine names are rejected | Schema (enum, `maxContains`) |
| The enum equals the phrases in the PRD B7 text, and the example lists all four | Test; reads `docs/PRD.md` |
| The schema and example have no key `version`, `library`, `libraries` or `machine_name`, and no string like `H5P.<letter>` | Test of those spellings only; other ways to write a version are not detected |
| The example package validates against the B1 schema | And uses only fields B1 defines |
| In the example, the ordinary practice item is ungraded and comes right after the guide Page, and the week still has one Page and one Assignment | Example only, not a general check; the example has no video lesson |
| No `.h5p` file exists in the repository | Fails if one is added |
| B7 defines no cue structure | The schema and example have no key `cue`, `cues` or `ref` |

### 8.3 Planned checker rules (Module 2). Not built; Release 1

| Rule | Checker rule |
|---|---|
| A practice (H5P) activity must not have a grade item | CK-11 |
| Media referenced by a full fixed URL instead of a relative path | CK-12 |

The checker works on the course model (B2). The B1 schema already rejects `graded: true` in a
package; CK-11 is the check on the course model, where PRD B7 says "the checker enforces this".

### 8.4 Documented here, not enforced by anything yet

| Rule | Why not enforced |
|---|---|
| An ordinary practice entry comes right after the week's guide Page | A schema cannot express it, and the validator does not check week structure yet (B1.2 rule 1 is itself not enforced) |
| Where a video checkpoint goes | Not decided |
| The standard week has one Page and one Assignment | Same: B1.2 rule 1 |
| The file named by `file` exists | No real `.h5p` is kept in the repository |
| The `.h5p` file uses one of the content types in section 3 | No check exists; library versions are not known |
| AI-drafted items are approved by a mentor before they reach learners | A process rule of Studio (FR-S-12), not a data rule |
| `cues.json` entries are valid | The B6 schema does not exist yet |
| Interactive video is used only in lab demonstrations | A rule of this text; the schema has no field for it |

## 9. Open decisions

| Marker | What is not decided | Who decides |
|---|---|---|
| OPEN DECISION: library versions (Q5) | Exact H5P library versions on Moodle 4.5 and 5.3 | The lab check (App-C item 5); B7 cannot freeze before |
| OPEN DECISION: `ref` kinds (Q6) | Which reference kinds a cue allows | Student 4, in the B6 cues schema |
| OPEN DECISION: several practice items | How many per week, and their order | The guide |
| OPEN DECISION: video checkpoint placement | Where a video checkpoint goes: PRD B7 says "after the video"; the guide-page placement is not applied to it | The guide |
| OPEN DECISION: the second content type | One type or a choice between several (the schema enum keeps one literal phrase) | The lab check and the guide |
