# 0015. The `shared.course_link` columns

**Date:** 2026-11-24
**Status:** Proposed by the B4 owner (Student 3). The key and the ownership are decided by the guide (issue #146, 20 November 2026). The columns below need the consumers' confirmation (Students 1, 2 and 4) and the guide's review at the Release 0 gate.
**Contracts:** B3 (`contracts/lti-launch.v1.md` section 7), B4 (`contracts/moodle-ws.v1.md`)
**Requirements:** PRD B3 "Course binding", OPS-06 and OPS-07 (grading design section 13, row 9)

## Context

PRD B3 says the LTI context id is mapped to the Moodle course id (through B4 web services) and stored in `shared.course_link`, keyed by `iss` plus context id. The guide decided that key (issue #58, 12 November 2026) and decided on #146 (20 November 2026) that **the columns stay with the B4 owner**, who records them in a decision record. The shared schema and its migrations are Student 2's. The B3 contract (section 7), the B3 ADR (OI-15) and the Studio design (section 12, item 33) say the columns are recorded by the B4 owner, and the Grading design cites this record. The Video design names the table and its keys only (section 5) and does not point to a record. None of them defines the columns. This is that record.

What the consumers need from the table:

| Consumer | Needs | Source |
|---|---|---|
| Studio | A primary key to refer to (`studio.package.course_link_id`) | Studio design section 5 |
| Grading | `(site_id, moodle_course_id)`, mapped to the LTI context; read-only access | Grading design sections 5.1 and 5.3 |
| Video | `iss` and the LTI context id as keys; no Moodle course id stored in its own tables | Video design section 5 |
| Whoever writes the row (open item 5) | To write one row after the first successful launch for a course, once B4 has confirmed the course | B3 ADR section 13 (the first successful launch should write the record), section 14.2 (B4 resolves the course and maintains the mapping) |

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
- Proposed: check `lti_context_id = moodle_course_id::text`. B3 section 3.1 makes the context id the Moodle course id, a positive integer in ASCII digits with no leading zero, so the two always have the same digits. Both are stored on purpose: `lti_context_id` is the launch value as received and is the lookup key; `moodle_course_id` is the integer that B4 confirmed, which Grading and Video use with `site_id`. The check stops them drifting apart. (Student 2 confirms with the shared schema.)
- One `site_id` per `iss`, taken from the platform registration. A table constraint cannot enforce this, so the gateway does.

**Not stored**
- No user data: no `sub`, name, email, roles or launch token.
- No course `idnumber`. LearnOps never uses a course idnumber (B4 section 2b): the service account does not have `moodle/course:update`.
- No site address, URL or credential. The address belongs to the platform registration, which is configuration.

**Who writes and reads**
- **Proposed (not decided):** the row is written once, after a verified launch and a B4 course lookup that succeeds, and never from an unverified `iss` (B3 section 7.1). Which component performs the lookup and the write is open (item 5). The B3 ADR (section 14.2) says B4 resolves the course and maintains the mapping, and B3 section 7.1 approves the gateway only as a consumer of B4.
- Modules only read the table. The grading design already gives the application role read-only access.
- Student 2 owns the schema, the migration and its `down` step, as the guide decided. The migration is plain SQL `up` and `down`, as the shared runner of Q36 requires.

## Open items

1. **How B4 sends the course id.** The form of `context.id` is decided: B3 section 3.1 (merged in #83 on 18 November 2026, with the guide's approval) makes it a positive integer written as a string in ASCII digits, and refuses anything else (section 8). What remains is not a question for anyone else: the guide decided in B3 ADR section 13 ("`context.id` at the B4 boundary") that B4 owns the form sent to Moodle and may pass the decimal string unchanged, that a value Moodle rejects fails closed at the B4 call, and that B3 sets no numeric-conversion rule. So it is the B4 owner's choice, to be written into B4 (section 2b says only that `field` and `value` are sent). This record stores the context id as received (text) and the Moodle id as an integer, so it holds either answer.
2. **The form of `site_id`.** `libs/moodle_ws` still has the fixed site ids `moodle45` and `moodle53`. The guide's assistant noted on #112 that the B4 `site_id` should be a value from the platform registration, and the guide decided to use the 5.3 lab only for now. Which one the table uses is not decided here. The type (text) holds either.
3. **A course B4 cannot see** (deleted, hidden from the service account, or renamed). Not decided. Proposal: keep the row, do not update `last_verified_at`, and let each consumer treat the course as unavailable. It depends on lab check OI-17, whether the service account can see the course.
4. **Consumers' confirmation.** Student 1 (Studio, `course_link_id`), Student 2 (shared schema, the second unique constraint and the check above) and Student 4 (Video keys) confirm or object before the migration is written. No confirmation is recorded yet; a peer review of this record is not one.
5. **Which component writes the row.** B3 ADR section 13 says the first successful launch should write the record, and section 14.2 says B4 resolves the course and maintains the mapping. Studio design section 12, item 27 lists which component does the lookup and stores it (`libs/lti`, `libs/moodle_ws` or Studio) as "Needs guide". Not decided here. Proposal: the lookup is a B4 call (`libs/moodle_ws`), the gateway calls it after a verified launch, and one writer stores the row.

## What this changes

Nothing in a contract, schema or code. B3 and B4 do not define these columns, as decided. The B3 ADR, the Studio design (section 12, item 33) and the Grading design (sections 5.1 and 13) still say the columns are "in a decision record"; they can point here in a follow-up.
