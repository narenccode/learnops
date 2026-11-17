# B3 integration review: what each module design says about the LTI launch

**Status:** Draft. A review note, not a design. Nothing here is approved.
**Owner:** Student 2 (integration lead for B3).
**Rebuilt:** 17 November 2026, from the repository at `origin/main` (`2904386`) and the B3 branch
(`5e5d276`). An earlier version was planned but never committed, so this is a reconstruction.
**Companion:** `docs/design/shared-course-link.md` (the proposed table and its open questions).

This note reads the four module designs against the decided B3 contract. It changes none of them.
Each finding names the file and the owner; the owner makes the edit in their own file.

Labels: **Confirmed** (a guide decision or PRD text, with source), **Proposed** (my suggestion),
**Unresolved** (an open question, no default chosen).

## 1. What B3 fixes (Confirmed)

| Decision | Source |
|---|---|
| Session identity is `(iss, sub, context id)` | PRD B3 "Session"; `contracts/lti-launch.v1.md` §6; ADR 0001 OI-21 |
| Course-link identity is `(iss, context id)` | PRD B3 "Course binding"; contract §7 |
| Unlisted roles are ignored; refuse only when no recognised role remains | PRD A5 rules; contract §5; ADR 0001 OI-22 |
| Baseline tools accept Mentor and Administrator; Learner-only launches are refused | PRD B3, EXT-07; contract §5 |
| A course id from one registered platform is never resolved against another platform's B4 client | contract §7.1 (confirmed by the B4 owner, ADR 0001 §13) |

## 2. What each module design says today

Line numbers are for `origin/main` at `2904386`.

| Module | What the design says | Matches B3? |
|---|---|---|
| Studio (`docs/design/studio.md`) | Line 98: "session bound to (`sub`, context id)". Line 112: `studio.package_version.author_sub` is the LTI `sub` alone. Line 119 and §12 items 27, 33: the `shared.course_link` key and who does the lookup are open | **No**: `iss` is missing from the session identity |
| Video (`docs/design/video.md`) | Line 95: "session bound to (`sub`, context id)". Line 123: the manifest records `source.uploaded_by` as the LTI `sub` alone | **No**: `iss` is missing from the session identity; `sub` is unique only within one issuer (contract §4) |
| Checker (`docs/design/checker.md`) | Line 89: provides B3, "no change planned". Line 155: "Restrict access to the course context associated with the authenticated LTI session." It says nothing on session identity or on `shared.course_link` | Silent, so it neither agrees nor conflicts |
| Grading (`docs/design/grading.md`) | §5.1 (line 288): a course is `(site_id, moodle_course_id)`, "mapped to the LTI context through `shared.course_link`"; web routes use the internal course link id. Tables on lines 296 to 319 store `(site_id, moodle_course_id)`. It says nothing on session identity | Consistent in spirit; see finding F-3 |

## 3. Findings

Each is a **Proposed** edit for the owner. None is a decision.

| # | Finding | Where | Suggested edit (owner's call) | Owner |
|---|---|---|---|---|
| F-1 | The session identity omits `iss`. A user on one Moodle site and a user on another can share a `sub`, and two sites can share a course number (ADR 0001 OI-21). | `studio.md` line 98 | Write "(`iss`, `sub`, context id)" and cite PRD B3 | Studio owner (Student 1) |
| F-2 | Same omission. | `video.md` line 95 | Same edit. ADR 0001 §14.3 and OI-18 already ask the Video owner to confirm `(iss, sub, context id)` for upload resume | Video owner |
| F-3 | Grading stores `(site_id, moodle_course_id)` in several tables. It could store `course_link_id` instead and read `site_id` and `moodle_course_id` from the link. Which is better depends on the columns of the link table (Q-C in `shared-course-link.md`). | `grading.md` §5.1, lines 296 to 319 | Decide after Q-C. Until then neither is wrong, but the two must not both be the source of truth | Grading owner (Student 3) |
| F-4 | The manifest stores `source.uploaded_by` as `sub` alone. `sub` is unique only within an issuer. | `video.md` line 123; PRD B6.3 (the example at line 581 uses `"<lti sub>"`) | Not a design-doc edit: B6 is a contract, so changing it to include `iss` would be a change under PRD B.0 (additive and optional after Release 0). Ask the guide first | Video owner, guide |
| F-5 | Checker says nothing on session identity or the course link, so each reader has to guess. | `checker.md` line 155 | Add one sentence that the session is `(iss, sub, context id)` and the course comes from `shared.course_link` | Checker owner (Student 2) |
| F-6 | Studio and Video both store a user reference (`sub`). Grading stores none (it uses `site_id` plus the Moodle user id). The three are not comparable. | `studio.md` line 112; `video.md` line 123; `grading.md` line 290 | Pick one rule for "user reference" across modules once F-1 and F-4 are answered. Not decided here | Guide |

## 4. Role matching (Unresolved)

Contract §5 lists four full IMS role URIs: Instructor, Learner, institution Administrator
(recognised or refused) and system Administrator (ignored). Everything else is "ignored" (OI-22).

The contract does not say whether matching is **exact on those four full URIs only**, or whether it
should also recognise other forms Moodle or LTI might send, for example a short name such as
`Instructor`, or a sub-role URI such as `…/membership/Instructor#TeachingAssistant`. I did not find
a decision in the repository, and I have not seen what Moodle 4.5 or 5.3 sends (ADR 0001 OI-16, a
lab check). Under the current text those forms would be ignored.

Exact question for the guide: **should role matching recognise only the four full IMS role URIs in
contract §5, with every other value ignored, or should it also recognise short names and sub-roles?
If the latter, which ones map to `mentor`?** A related point from the Grading reviewer: a site that
grants the capability `mod/lti:admin` to a teacher would make that teacher arrive as
`administrator`; whether §5 should warn about it is the guide's call.

## 5. PR #83 review state

Checked on 17 November 2026 through GitHub. Head `5e5d276`. State OPEN, not a draft.

| Item | State |
|---|---|
| Merge state | Conflicting with `main` (`DIRTY`); review decision `REVIEW_REQUIRED` |
| CI | `checks` and `review` green on `5e5d276`; `guide-bot` failing because it waits for the owners and the guide |
| Studio (Student 1) | Approved on `5e5d276`, 16 Nov |
| Grading and B4 (Harshitha, through the review assistant) | Approved on `5e5d276`, 17 Nov, but **provisional**: the branch conflicts with `main`, so the merged head needs a fresh look. It does not approve ADR 0001 Stage 1 or Stage 2 |
| Video | **No review** |
| Guide | No approval |

Advice from the reviews that is not yet addressed on the contract files (owned by others; I do not
edit them):

1. Who converts `context.id` to an integer for B4, `libs/lti` or the caller.
2. Raw non-ASCII characters in `contracts/test-vectors/lti-launch-optional-claims.v1.json`.
3. A length limit for `context.id` (no upper bound today; related to Q-F).
4. The missing LTI version claim (`version == "1.3.0"`) in contract §3 and §8 and in the PRD B3 row.
5. A note in §5 about `mod/lti:admin` (section 4 above).
6. The PR description is stale: it says the example validator is not on `main`, and its test table is
   from an older head.

## 6. Drafts (not posted)

Nothing below has been sent. Each needs the sender's go.

**Draft A, question to the guide on PR #83 or Issue #58:**

> Guide, B3 and the course link need answers on these points before the module designs can
> finish. Details are in `docs/design/shared-course-link.md` §7 and
> `docs/design/b3-module-integration.md` §4.
>
> 1. **Q-A:** is the value sent to `core_course_get_courses_by_field` the string from `context.id`
>    or an integer?
> 2. **Q-B:** where does the mapping from `iss` to `moodle45` or `moodle53` live, and who owns it?
> 3. **Q-C:** may the four module owners and you agree the `shared.course_link` columns on the
>    proposal in that document, and approve the gateway as a B4 consumer (OI-15)?
> 4. **Q-D:** which component does the first-launch lookup and writes the row: `libs/lti`,
>    `libs/moodle_ws` or a module?
> 5. **Q-E:** which migration tool, and who creates the `shared` schema?
> 6. **Roles:** only the four full IMS role URIs in contract §5, or also short names and
>    sub-roles?
> 7. **Session identity in Studio and Video:** their designs say (`sub`, context id) without
>    `iss`; Video's manifest stores `sub` alone (a B6 contract field). Should the owners align to
>    `(iss, sub, context id)`, and is a change to `uploaded_by` acceptable under B.0?

**Draft B, review request to the Video owner on PR #83:**

> Video owner, PR #83 (B3 LTI launch contract) has approvals from Studio and Grading/B4 but none
> from Video, and Video is a consumer. Please review the contract at the new head after `main` is
> merged, and in particular: `iss` in the session identity (your design says `sub` and context id),
> and `source.uploaded_by` as `sub` alone. A short "no blocking items" or a list is enough.

## 7. Integration tests that are blocked

These need real session code. None exists on `main`: `libs/` holds only `libs/contracts` and
`libs/media_paths`. No fake gateway will be built to get around this. When `libs/lti` or any
module's session code exists, add:

1. A valid launch result is consumed by a module, which reads the role and course from the session.
2. The course context comes from the session, not from the request.
3. One session cannot read another course's data.
4. A launch whose course has no `shared.course_link` row is refused with a clear message.

Until then, the only tests are the contract tests and `tests/integration/test_course_link_schema.py`,
which test the table definition and nothing about a launch.

## 8. Not claimed

- That Moodle 4.5 or 5.3 behave as the PRD and ADR 0001 expect: no lab launch has been made.
- That the gateway is secure or that any module enforces the isolation rules: no module code exists.
- That B4 returns the course data the link table assumes: B4 is a draft and its lab checks are open.
