# 0015. The `shared.course_link` columns

**Date:** 2026-11-24
**Status:** Proposed by the B4 owner (Student 3). The key and the ownership are decided by the guide (issue #146, 20 November 2026). The columns below need the consumers' confirmation (Students 1, 2 and 4) and the guide's review at the Release 0 gate.
**Contracts:** B3 (`contracts/lti-launch.v1.md` section 7), B4 (`contracts/moodle-ws.v1.md`)
**Requirements:** PRD B3 "Course binding", OPS-06 and OPS-07 (grading design section 13, row 9)

## Context

PRD B3 says the LTI context id is mapped to the Moodle course id (through B4 web services) and stored in `shared.course_link`, keyed by `iss` plus context id. The guide decided that key (issue #58, 12 November 2026) and decided on #146 (20 November 2026) that **the columns stay with the B4 owner**, who records them in a decision record. The shared schema and its migrations are Student 2's. The B3 contract, the B3 ADR and the Studio, Grading and Video designs all point to this record and do not define the columns themselves. This is that record.

What the consumers need from the table:

| Consumer | Needs | Source |
|---|---|---|
| Studio | A primary key to refer to (`studio.package.course_link_id`) | Studio design section 5 |
| Grading | `(site_id, moodle_course_id)`, mapped to the LTI context; read-only access | Grading design sections 5.1 and 5.3 |
| Video | `iss` and the LTI context id as keys; no Moodle course id stored in its own tables | Video design section 5 |
| The gateway (`libs/lti`) | To write one row after the first successful launch for a course | B3 ADR section 14, contract section 7 |

## Decision

| Column | Type | Null | Meaning |
|---|---|---|---|
| `id` | uuid | no | Primary key. `studio.package.course_link_id` refers to it |
| `iss` | text | no | The issuer of the verified launch, exactly as received, with no trimming, case folding or other normalisation (B3 section 7.1) |
| `lti_context_id` | text | no | `context.id` from the verified launch, as a string, as received |
| `site_id` | text | no | The registered platform, that is the B4 client bound to `iss` (B3 section 7.1). Grading and Video use `(site_id, moodle_course_id)` for a course |
| `moodle_course_id` | bigint | no | The Moodle course id, confirmed by B4 with `core_course_get_courses_by_field` (`field` = `id`) at the first launch. Greater than 0 |
| `course_shortname` | text | yes | For display only. It is never an identifier |
| `created_at` | timestamptz | no | First successful launch for this course |
| `last_verified_at` | timestamptz | no | The last time B4 confirmed that the course exists. Equal to `created_at` at the first launch |

**Constraints**
- Primary key `id`.
- Unique `(iss, lti_context_id)`: the key decided by the guide.
- Unique `(site_id, moodle_course_id)`: one LTI context per Moodle course on a registered platform. (Proposed. Student 2 confirms with the shared schema.)
- Check `moodle_course_id > 0`.
- One `site_id` per `iss`, taken from the platform registration. A table constraint cannot enforce this, so the gateway does.

**Not stored**
- No user data: no `sub`, name, email, roles or launch token.
- No course `idnumber`. LearnOps never uses a course idnumber (B4 section 2b): the service account does not have `moodle/course:update`.
- No site address, URL or credential. The address belongs to the platform registration, which is configuration.

**Who writes and reads**
- The gateway writes a row after a verified launch and a B4 course lookup that succeeds. It never writes from an unverified `iss` (B3 section 7.1).
- Modules only read the table. The grading design already gives the application role read-only access.
- Student 2 owns the schema, the migration and its `down` step, as the guide decided. The migration is plain SQL `up` and `down`, as the shared runner of Q36 requires.

## Open items

1. **The form of `context.id`.** Whether a `context.id` that is not a positive integer is refused, and how B4 sends it as `value`, is a B3 and B4 contract decision that waits for the guide (his assistant on #112, 17 November). This record stores it as received (text) and the Moodle id as an integer, so it holds either answer.
2. **The form of `site_id`.** `libs/moodle_ws` still has the fixed site ids `moodle45` and `moodle53`. The guide's assistant noted on #112 that the B4 `site_id` should be a value from the platform registration, and the guide decided to use the 5.3 lab only for now. Which one the table uses is not decided here. The type (text) holds either.
3. **A course B4 cannot see** (deleted, hidden from the service account, or renamed). Not decided. Proposal: keep the row, do not update `last_verified_at`, and let each consumer treat the course as unavailable. It depends on lab check OI-17, whether the service account can see the course.
4. **Consumers' confirmation.** Student 1 (Studio, `course_link_id`), Student 2 (shared schema, the second unique constraint) and Student 4 (Video keys) confirm or object before the migration is written.

## What this changes

Nothing in a contract, schema or code. B3 and B4 do not define these columns, as decided. The B3 ADR, the Studio design (section 12, item 33) and the Grading design (sections 5.1 and 13) still say the columns are "in a decision record"; they can point here in a follow-up.
