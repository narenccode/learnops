# Design: `shared.course_link`

**Status:** Draft. A **proposal**. Nothing in this document is approved or lab-verified.
**Owner:** Student 2 (Module 2 owns `shared.course_link`; see §2).
**Rebuilt:** 17 November 2026, from the repository text listed in §10. An earlier draft of this
document was planned but never committed, so this is a reconstruction, not a recovery. Where the
repository does not say something, this document says so and asks the question (§7). It does not
decide it.

How to read the labels:

- **Confirmed** means a guide decision or a PRD requirement, with its source. It is not a statement
  that Moodle behaves that way: nothing here is verified on a Moodle site.
- **Proposed** means this document's own design. It can change when the questions in §7 are
  answered.
- **Unresolved** means a question that is open. No default is chosen.

If this document conflicts with `docs/PRD.md`, the PRD wins (root `CLAUDE.md`).

## 1. Purpose

B3 says the LTI context id is mapped to the Moodle course through B4 and stored in
`shared.course_link`, keyed by `iss` plus context id (PRD B3, "Course binding"). Four modules
need that table (Studio, Checker, Grading, Video), and the PRD does not define its columns. The
Studio design (`docs/design/studio.md` §12 item 33) and the Grading design
(`docs/design/grading.md` §5.1, Q36) both wait for it before they write a foreign key. This
document proposes the columns, the migration and the rules for readers so that those items can be
answered in one place.

## 2. Confirmed

| # | Statement | Source |
|---|---|---|
| C1 | The course-link identity is `(iss, context id)`. | PRD B3 "Course binding"; `contracts/lti-launch.v1.md` §7; ADR 0001 §13 ("Decided by the guide") |
| C2 | The LTI session identity is `(iss, sub, context id)`. | PRD B3 "Session"; `contracts/lti-launch.v1.md` §6; ADR 0001 OI-21 |
| C3 | Moodle supplies its course id as the LTI context id, so Moodle course tools use `context.id` as the course id. | ADR 0001 §13 (the guide's clarification, with the Moodle source line `'context_id' => $course->id`). From a reading of Moodle source: not yet seen in a real launch (ADR 0001 OI-16) |
| C4 | The course lookup is `core_course_get_courses_by_field` with `field=id`. | ADR 0001 §13; PRD B4 function list |
| C5 | The first successful launch confirms that the course exists, retrieves its shortname for display, and writes the `shared.course_link` row. | ADR 0001 §13 |
| C6 | `shared.course_link` is owned by Module 2; the other modules use it and do not change it. | `docs/design/grading.md` §5.2 and §5.3 (a draft design); hand-over brief of 17 Nov |
| C7 | The lookup may use the course shortname as an accepted alternative to the id, and `idnumber` must not be used for it. | Hand-over brief of 17 Nov (relayed guide decision). I could not find this wording in the repository; no link is recorded |
| C8 | A launch whose `iss` does not exactly match a registered platform is refused; B4 is called only through the client bound to the verified `iss`; there is never a fallback to another platform's client. | `contracts/lti-launch.v1.md` §7.1; ADR 0001 §13 (confirmed by the B4 owner) |
| C9 | Database migrations are versioned and reversible; there is one PostgreSQL database with one schema per module plus `shared`. | PRD OPS-07; PRD A10 |
| C10 | The Moodle lab sites are named `moodle45` and `moodle53`. | PRD A11 |

Not confirmed, although other documents sound as if they were: the B4 draft (PR #27, head
`2d46030`) lists its course-lookup parameters as "To verify in the lab" and lists no response
fields. Lab checks 1 to 10 in that draft are all open. So the **raw response fields of
`core_course_get_courses_by_field` are not lab-verified**, and nothing below depends on a field
name Moodle returns beyond what the PRD and ADR 0001 §13 already say (the course id and the
shortname).

## 3. Proposed table

One row per `(iss, context id)`. Every column below is **Proposed**.

| Column | Type | Null | Rule | Why |
|---|---|---|---|---|
| `id` | `uuid`, default `gen_random_uuid()` | no | Primary key. Never reused, never changed. | Other tables refer to it (`studio.package.course_link_id`); the Grading design says web routes use "the internal course link id" |
| `iss` | `text` | no | Not empty. Compared as received, no normalisation. | C1, C8 |
| `context_id` | `text` | no | Matches `^[1-9][0-9]*$` (ASCII digits, no leading zero, no sign). | The B3 contract §3.1 rule for `context.id`; stored as text because B3 sets no upper bound |
| `site_id` | `text` | no | `moodle45` or `moodle53`. | C10; the Grading design (§5.1) keys its data by `(site_id, moodle_course_id)` |
| `moodle_course_id` | `bigint` | no | Greater than 0. | The id the B4 lookup confirmed (C5) |
| `course_shortname` | `text` | no | Not empty. | C5: retrieved at first launch, for display |
| `created_at` | `timestamptz`, default `now()` | no | | When the first launch wrote the row |
| `last_confirmed_at` | `timestamptz`, default `now()` | no | | The most recent launch that re-confirmed the course |

Constraints and indexes:

- Unique `(iss, context_id)`: this is the identity (C1).
- A plain (non-unique) index on `(site_id, moodle_course_id)`, for Grading's lookups. Whether that
  pair should be unique is a question (Q-G).

No column holds a user, a role, a token, a name or an email. The table is about courses only.

## 4. Proposed migration

The SQL is written without a migration tool (Q-E is open), so it fits any tool that can run a
plain up step and a plain down step. It assumes that the `shared` schema already exists, created
by an earlier shared migration. The Grading design says shared migrations run before module
migrations. Creating the schema is not part of this step, so the down step cannot drop something
it did not create (Grading design §5.3: "The down step drops only what its up step created").

The integration tests read these two blocks from this file, so the SQL here is the SQL that is
tested.

```sql up
CREATE TABLE shared.course_link (
    id                uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    iss               text        NOT NULL,
    context_id        text        NOT NULL,
    site_id           text        NOT NULL,
    moodle_course_id  bigint      NOT NULL,
    course_shortname  text        NOT NULL,
    created_at        timestamptz NOT NULL DEFAULT now(),
    last_confirmed_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT course_link_identity UNIQUE (iss, context_id),
    CONSTRAINT course_link_iss_not_empty CHECK (iss <> ''),
    CONSTRAINT course_link_context_id_format CHECK (context_id ~ '^[1-9][0-9]*$'),
    CONSTRAINT course_link_site_id_known CHECK (site_id IN ('moodle45', 'moodle53')),
    CONSTRAINT course_link_moodle_course_id_positive CHECK (moodle_course_id > 0),
    CONSTRAINT course_link_shortname_not_empty CHECK (course_shortname <> '')
);

CREATE INDEX course_link_site_course ON shared.course_link (site_id, moodle_course_id);
```

```sql down
DROP TABLE shared.course_link;
```

Dropping the table drops its index and constraints with it. The down step loses every row; that is
acceptable for a table that the next launch writes again, but it is stated here so nobody is
surprised.

## 5. Proposed consumer contract

For Studio, Checker, Grading and Video, all **Proposed**:

1. **Look up by identity.** Find a course with `WHERE iss = $1 AND context_id = $2`, using the
   `iss` and `context.id` of the validated launch result (B3). Never by `context_id` alone: the
   same number can come from two Moodle sites (`contracts/lti-launch.v1.md` §7.1).
2. **Refer by `id`.** A module table that belongs to a course stores `course_link_id` with a
   foreign key to `shared.course_link (id)`. That is what Studio's `studio.package` already does.
   A module does not copy `iss` or `context_id` into its own tables.
3. **Do not delete a row that something refers to.** The default foreign key (no cascade) refuses
   it. A module must not add `ON DELETE CASCADE` to its reference without agreement.
4. **Modules only read.** Only Module 2 writes (C6). The Grading design asks for read-only access
   for module application roles; the roles themselves are not defined here (Q-E, Q-D).
5. **The first-launch write is an upsert on the identity.** A repeated launch of a known course
   keeps `id` and `created_at` and refreshes `last_confirmed_at` and `course_shortname`. A launch
   whose B4 lookup finds no such course writes nothing and is refused with a clear message
   (contract §7.1: if no client is bound for the verified `iss`, the B4 call is refused).
6. **Session identity is not stored here.** `sub` never enters this table.

Grading can resolve `(site_id, moodle_course_id)` to a row through the index in §3, and a module
can go from a row to `(site_id, moodle_course_id)` without calling Moodle.

## 6. What the integration tests cover

`tests/integration/test_course_link_schema.py` runs the SQL from §4 on a real PostgreSQL 16 server
(a throwaway Docker container; the tests skip with a stated reason when Docker is not usable).
It covers only what §3 to §5 and the Confirmed rows above support:

| Area | What is checked |
|---|---|
| Identity (C1, C8) | The same context id from two issuers is two rows; the same issuer and context id twice is refused; issuers that differ only in case or a trailing slash are different rows |
| `context_id` format | The B3 §3.1 values that must be accepted and every value it says to refuse, including a trailing newline and non-ASCII digits |
| `site_id` | Only `moodle45` and `moodle53` |
| Other columns | Empty `iss` and shortname, and a course id of zero or below, are refused; nothing is nullable |
| Defaults | `id`, `created_at` and `last_confirmed_at` are filled in |
| First-launch upsert (§5.5) | `id` and `created_at` stay, `last_confirmed_at` and the shortname move |
| Consumer foreign key (§5.2, §5.3) | A reference to an unknown id is refused and a referenced row cannot be deleted (a throwaway table in the test, not a real module table) |
| Migration (C9) | Up, down, up again; down removes only this table and leaves another object in `shared` |
| This document | The two SQL blocks exist; the open questions are listed; the document does not claim approval or lab verification; `idnumber` is named as not to be used |

They do **not** show that a launch writes the row (no gateway exists), that Moodle returns the
course data this design expects, or that Moodle 4.5 and 5.3 behave the same. They prove the table
definition behaves as §3 states, and nothing more.

## 7. Unresolved questions

None of these is decided here. Each needs an answer from the named person.

| # | Question | Who answers |
|---|---|---|
| Q-A | Is the lookup value sent to `core_course_get_courses_by_field` the string from `context.id` or an integer? (B4 lab check 1 is open, and B3 sets no upper bound on `context.id`.) | Guide and B4 owner |
| Q-B | Where does the mapping from `iss` to `site_id` (`moodle45` or `moodle53`) live, and who owns it: configuration of the registered platforms, a table, or the `libs/lti` registration? | Guide |
| Q-C | Do Studio, Checker, Grading and Video agree these columns? (ADR 0001 OI-15: the B4 owner confirmed the issuer rule only; the columns and the guide's approval of the gateway as a B4 consumer are pending.) | The four module owners and the guide |
| Q-D | Which component performs the first-launch lookup and writes the row: `libs/lti`, `libs/moodle_ws`, or a module? (Studio design Q27.) | Guide |
| Q-E | Which migration tool does the repository use, and who creates the `shared` schema? The SQL in §4 is tool-neutral on purpose. (Grading design Q36.) | Student 2 and the guide |

Raised while rebuilding this document. They are mine, not decisions:

| # | Question | Who answers |
|---|---|---|
| Q-F | `context_id` and `moodle_course_id` hold the same number if C3 and C4 hold. Keep both (text for the contract, `bigint` for joins), or drop one? Also, a 19-digit or longer `context_id` fits B3 (no upper bound) but not `bigint`; the plan is that B4 refuses an unknown course before a row is written, which is not recorded anywhere. Related to PR #83 review advice on a length limit. | Guide |
| Q-G | Is `(site_id, moodle_course_id)` unique? It would stop two issuers from claiming one Moodle course, and it would block a legitimate change of a site's issuer URL. §3 leaves it non-unique. | Guide |
| Q-H | What should happen to `course_shortname` when a course is renamed in Moodle: refresh on every launch (as §5.5 proposes), or keep the first value? | Student 2 |
| Q-I | Is `uuid` the right type for `id`? The Grading design uses `uuid` for its own tables; the PRD names no type. | Student 2 |

## 8. Not claimed

- That any of this runs on Moodle 4.5 or 5.3. No lab launch has been made (ADR 0001 OI-16).
- That `core_course_get_courses_by_field` returns what is assumed here. B4 is a draft and its lab
  checks are open (§2).
- That the gateway, `libs/lti` or any module writes or reads this table. None exists on `main`.
- That the guide or any module owner has approved these columns (Q-C).
- That the migration works with the repository's migration tool. No tool is chosen (Q-E).

## 9. Impact on other documents

This document changes no other file. The findings for the module designs are in
`docs/design/b3-module-integration.md`, for their owners to act on.

## 10. Sources read

`docs/PRD.md` (B3, B4, A10, A11, OPS-06, OPS-07); `contracts/lti-launch.v1.md` §3.1, §6, §7;
`docs/decisions/0001-lti-library.md` §13, §14, OI-15, OI-16, OI-21; `docs/design/grading.md` §5.1
to §5.3, Q36; `docs/design/studio.md` §5, §12 items 27 and 33; `docs/design/video.md`;
`docs/design/checker.md`; the draft B4 contract (`contracts/moodle-ws.v1.md` on the branch of
PR #27, head `2d46030`).
