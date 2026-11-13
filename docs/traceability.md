# Traceability (PRD E4)

| Requirement | Test(s) | Demo step | Bloom level |
|---|---|---|---|

## B1 course package contract (v1), Release 0 foundation

Files: `contracts/course-package.v1.schema.json`, `contracts/examples/course-package.v1/`,
`libs/contracts/tests/test_course_package_v1.py`. B1 has no requirement ID of its own in the PRD
(it is a contract, PRD B.0), so no row in the table above maps to it.

FR-S-03 ("Validate against B1 and the checker rule library", Release 2) is deliberately not in the
table above. The tests below cover only the B1-related part of it: structure checks against the
schema. They do not implement FR-S-03, which also needs the checker rule library (Module 2) and
validation on every save in Course Studio. FR-S-03 gets its row in the pull request that
implements it.

### Enforced by the JSON Schema and covered by automated tests

Structure only. Test names are in `test_course_package_v1.py`.

| Rule | PRD | Test(s) |
|---|---|---|
| `schema` equals `learnops.course/v1`; `course` and `sections` required | B1.1 | `test_missing_required_field_is_rejected`, `test_wrong_type_or_value_is_rejected` |
| Required fields and types on course, section and activity (`type`, `idnumber`, `title`; section `number`, `activities`) | B1.1 | same two tests |
| `mode` is `full` or `sections-only` | B1.1, B1.4 | `test_wrong_type_or_value_is_rejected`, `test_example_in_sections_only_mode_is_valid` |
| `slug`, `idnumber` and `unlock.after` are lowercase ASCII with hyphens (format only, not uniqueness) | B1.1, B1.2 rule 6 | `test_invalid_identifier_is_rejected` |
| The two default protected idnumbers (`final-project`, `course-feedback`) are rejected on sections and activities, in both modes | B1.4 | `test_protected_idnumber_is_rejected` |
| An assignment has `body`, `points`, `submission` and `completion`; a page has `body` | B1.1 | `test_missing_required_field_is_rejected` |
| `unlock.start_date` is an ISO date string or null (impossible dates are rejected; an unquoted YAML date is rejected) | B1.1 | `test_invalid_start_date_is_rejected`, `test_unquoted_yaml_date_is_rejected_so_it_must_be_quoted` |
| An H5P activity has `graded: false` | B7 | `test_missing_required_field_is_rejected`, `test_wrong_type_or_value_is_rejected` |
| Unknown fields are accepted | B.0 rule 2, EXT-02 | `test_valid_variation_is_accepted` |
| The schema is valid, and the example package validates (also as `sections-only`) | B.0 rule 1 | `test_schema_is_a_valid_draft_2020_12_schema`, `test_example_package_is_valid`, `test_example_in_sections_only_mode_is_valid` |

Enforced and tested, but chosen in the schema rather than stated as a rule in the PRD (to be
confirmed by the contract reviewers): the `type` spellings `url` and `label`; `completion` limited
to `submit`; `submission` limited to `onlinetext` and `file`; `section.number` at least 1; points
as non-negative integers; non-empty titles; the shape of `body` (relative path, no `..`);
`activities` and `sections` not empty.

### Documented but not automatically enforced

No validator code for these exists yet, so nothing in the repository checks them. The schema's
`$comment` lists them too. The example package was checked against them by hand when it was
created; that check is not automated and is not committed.

| Rule | PRD | Where the PRD places it |
|---|---|---|
| One guide Page and one task Assignment per week | B1.2 rule 1 | No checker rule is named for it (CK-01…CK-13) |
| Week N unlocks when the week N-1 task is submitted; `unlock.after` names an existing earlier activity | B1.2 rule 2 | Related: CK-04, CK-05 (FR-C-03, R1) |
| Graded points sum to `total_points` | B1.2 rule 3 | CK-03 |
| Assignments use marking workflow | B1.2 rule 4 | CK-10 (not a package field) |
| Completion tracking on for every activity used in an unlock rule | B1.2 rule 5 | CK-13 |
| `idnumber`s unique within the course and never reused for a different activity | B1.2 rule 6 | CK-06 (uniqueness); "never reused" has no PRD rule |
| Marking table present and valid: markers, columns, points sum, allowed `Check` names | B1.3, C3.5 | CK-09 |
| Protected idnumbers configured beyond the two defaults; `protected_section` collision | B1.4 | CK-07 for the course model; `protected_section` has no default in the PRD |

### Not mapped

Left out because the PRD does not establish the mapping:

- **A row, demo step and Bloom level for FR-S-03.** See the note at the top of this section. PRD
  C1.12 gives levels to kinds of work (for example "Design (L6): schema, validator, generator"),
  not to individual requirements.
- **FR-S-02, FR-S-04, FR-S-07, FR-S-08, FR-C-01, FR-G-01.** They touch B1 but need code that does
  not exist yet, and the PRD does not say that schema tests count towards them.
- **C1.7 "a package containing a protected idnumber is rejected with a clear message".** The schema
  rejects the two default idnumbers; the user-facing message is not tested.
- **Requirement IDs for the contract work itself.** None in the PRD.

## B4 Moodle web-services contract (v1), Release 0 foundation

Files: `contracts/moodle-ws.v1.md` (normative rules), `contracts/moodle-ws.v1.schema.json`,
`contracts/examples/moodle-ws.v1.functions.json` (allow-list), `libs/contracts/tests/test_moodle_ws_v1.py`.
**Contract work only, draft, not verified on any Moodle site.** Guide's decisions on Q1, Q24 and
Q37: PR #27. Guide's B4 findings (set_user_flags removed, save_grade parameters, read-back,
capabilities, course identification): rules §2 to §4, with Moodle source evidence in rules §7.
Guide's decisions on the eleven B4 questions (PR #64, 2026-11-12): rules §3a (R1 to R11), §3b and
§4, the PRD B4 tables and draft rule, and lab checks 13 to 16.

FR-G-01 ("Fetch assignments, the marking table and submissions … through B4") and FR-G-06 ("Write
only approved drafts to Moodle via B4"), both Release 4, are deliberately not in the table above. They
need `libs/moodle_ws` and the grading module, which do not exist yet.

### Enforced by automated tests

Test names are in `test_moodle_ws_v1.py`.

| Rule | PRD | Test(s) |
|---|---|---|
| The allow-list names exactly the PRD B4 functions, no extra, none missing, no duplicates | B4 | `test_function_names_equal_the_prd_b4_list`, `test_prd_b4_lists_the_expected_number_of_functions` |
| The allow-list and the rules text (`moodle-ws.v1.md` §2) name the same functions | B.0 rule 1 | `test_function_names_equal_the_rules_table` |
| Each entry's purpose is the PRD B4 purpose | B4 | `test_purpose_is_the_prd_purpose` |
| Always-sent and optional parameters equal the PRD B4 parameter table for each function; none is in both lists; `mod_assign_save_grade` sends `workflowstate` | B4, App-C 1 | `test_every_parameter_is_named_in_the_prd_for_its_function`, `test_example_parameters_equal_the_prd_parameter_table`, `test_the_prd_names_exactly_these_parameters`, `test_no_parameter_is_both_required_and_optional`, `test_a_parameter_not_named_for_its_function_is_found`, `test_save_grade_sends_the_workflow_state` |
| `mod_assign_save_grade` has the guide's seven required and two optional parameters | B4 (guide's findings) | `test_save_grade_has_the_guides_required_and_optional_parameters` |
| "Always sent" (LearnOps's rule) is kept apart from what Moodle requires; the PRD column says "Always sent" | B4 | `test_always_sent_is_kept_apart_from_moodle_required` |
| `mod_assign_set_user_flags` is in neither the allow-list, the PRD B4 tables nor the rules table | B4 (guide's findings) | `test_set_user_flags_is_allowed_nowhere` |
| The read-back sends `assignid` and `userid`, and the rule (`lastattempt.gradingstatus` exactly `readyforrelease`, otherwise not verified) is stated in the rules and the PRD | B4 draft rule | `test_the_status_read_back_sends_assignment_and_learner`, `test_the_read_back_field_is_stated_in_the_rules_and_the_prd` |
| A write counts as done only when both the state and the grade value are confirmed; the state alone is never enough | B4 draft rule | `test_success_needs_both_the_state_and_the_grade_value` |
| The write rules are exactly R1 to R11 (guide's decisions, rules §3a) | B4 draft rule | `test_the_write_rules_are_exactly_r1_to_r11` |
| R1: `mod_assign_get_grades` is the stored-grade read-back, in the allow-list, rules §2 and the PRD tables (always sent: `assignmentids`), with the §3b matching rule | B4 draft rule | `test_r1_get_grades_is_the_stored_grade_read_back` |
| R2: `attemptnumber` is the explicit attempt, never `-1`; the read-back matches it | B4 draft rule | `test_r2_attempt_number_is_explicit_never_minus_one` |
| R3: a write is refused before sending when the state is already `readyforrelease` or `released`, and is still read back; the 4.5 / 5.3 difference is recorded for the lab | B4 draft rule | `test_r3_locked_states_are_refused_before_sending_and_still_verified` |
| R4: `viewhiddencourses`, `viewhiddendetails` and `useremail` are not granted | B4, SEC-03 | `test_r4_declared_capabilities_are_not_granted` |
| R5: suspended learners are skipped and reported as skipped; `viewsuspendedusers` is not granted | B4 | `test_r5_suspended_learners_are_skipped_and_reported` |
| R6: `viewownsubmissionsummary` stays lab check 12 | B4, App-C 1 | `test_r6_view_own_submission_summary_stays_a_lab_check` |
| R7: `mod/assign:reviewgrades` is granted on both versions | B4, SEC-03 | `test_r7_review_grades_is_granted_on_both_versions` |
| R8: a failed read-back is `NOT_VERIFIED` and the write is never repeated | B4 draft rule | `test_r8_failed_read_back_is_not_verified_and_never_rewrites` |
| R9: exact numeric match after parsing, no tolerance; range checked before writing | B4 draft rule | `test_r9_exact_numeric_match_and_range_check_before_writing` |
| R10: no submission, no grade and no access are separate outcomes, never success; other learners continue | B4 | `test_r10_missing_and_inaccessible_are_separate_outcomes` |
| R11: an uncertain write is never retried automatically; read back, the mentor decides | B4 draft rule | `test_r11_uncertain_write_is_never_retried_automatically` |
| The `docs/design/grading.md` §10.1 conflict with R11 and the unreadable pre-write state are recorded as open | B4 | `test_the_grading_design_conflict_with_r11_is_an_open_follow_up` |
| Three cases the decisions do not settle (state unreadable, marking workflow off, lost answer with a matching read-back) are open questions for the guide, each with its fail-closed proposal, and none is in §3a | B4 §6 | `test_the_fail_closed_proposals_are_open_questions_for_the_guide` |
| Course lookup sends `field` and `value`, by course id or shortname, never idnumber | B4 course identification | `test_course_lookup_does_not_rely_on_idnumber` |
| The capability lists (needed, never granted) are the guide's and do not overlap; a custom role is required | B4, SEC-03 | `test_the_capability_lists_are_the_guides_and_do_not_overlap`, `test_the_custom_role_rule_is_stated` |
| Every lab check in rules §5 (1 to 16) is still open on both versions, with no decision record; checks 13 to 16 name the rule they cover | App-C 1 | `test_every_lab_check_is_still_open`, `test_the_decision_lab_checks_name_their_rules` |
| A replacement name for a Moodle version also appears in the PRD B4 text | B4 ("replacements recorded here") | `test_a_replacement_name_is_also_in_the_prd` |
| No verification state is stored in the schema or example | Guide, Q1 | `test_invalid_document_is_rejected_at_the_expected_place` (three verified-flag cases) |
| Schema is valid; example validates; invalid documents fail at the expected place; unknown fields are accepted | B.0 rule 1, rule 2 | `test_schema_is_a_valid_draft_2020_12_schema`, `test_example_is_valid`, `test_invalid_document_is_rejected_at_the_expected_place`, `test_unknown_fields_are_accepted` |
| One token variable per site with a placeholder; no single `MOODLE_WS_TOKEN` | B4, SEC-03, C-06; guide, Q24 | `test_one_token_variable_per_site_with_a_placeholder` |

### Documented but not automatically enforced

| Rule | PRD |
|---|---|
| Only the functions listed in the contract are called. `libs/moodle_ws` builds its allow-list from the example and refuses any other function before the transport (`test_allowlist.py`: `test_the_list_equals_the_contract_example`, `test_anything_else_is_refused_before_the_transport`). Not enforced against a real Moodle: there is no real transport yet | B4 |
| One service account per site, with a token restricted to those functions and the capabilities in rules §4 (the lists are tested; that they are enough is lab check 9) | B4, SEC-03 |
| The token is stored only in the environment | SEC-03, C-06 |
| A grade write uses workflow state `readyforrelease`, never `released`, and counts as done only when both the state and the grade value are confirmed; the grade value is read with `mod_assign_get_grades` (R1); the write rules R1 to R11 are contract text here, and their enforcement in `libs/moodle_ws` is a separate follow-up; only approved drafts are written | B4, C-09 |
| Each function exists and behaves as expected with the parameters used on Moodle 4.5 and 5.3 (all 16 lab checks are still open) | B4, App-C 1 |

Open: when the lab Moodle sites are available (all sixteen checks in `moodle-ws.v1.md` §5 wait for
them; B4 cannot be frozen until they pass), and the field for feedback comments inside `plugindata` on
`mod_assign_save_grade` (lab check 6). Q1, Q24 and Q37 are decided (PR #27); the eleven B4
questions are decided (PR #64). Still open for the guide: what happens when the state cannot be read
before a write, whether marking workflow off is refused, and whether a lost answer with a
matching read-back counts as done (rules §6; each has a fail-closed proposal).

**Follow-up (not in this branch):** `docs/design/grading.md` §10.1 (Release 4, draft) says an unknown
outcome may "write again under the same idempotency key"; R11 forbids an automatic retry. The
grading design must be updated in its own pull request.

## `libs/moodle_ws` skeleton, Release 0 foundation

Files: `libs/moodle_ws/`. The library has no requirement ID of its own (design Q7, Q43, open), so no
row in the table above maps to it. Interim, per design §2: read side under FR-G-01, write side under
FR-G-06. Neither requirement is implemented by this skeleton.

| Rule | Source | Test |
|---|---|---|
| Only allow-listed functions are sent; the list comes from the contract example | B4 §2a, guide on Q1 | `test_allowlist.py` |
| A grade write sends `readyforrelease`, never `released` | B4 §3, C-09 | `test_client.py` |
| One token per site, from the environment only | B4 §1, Q24, SEC-03, C-06 | `test_config.py` |
| Tokens and full URLs stay out of logs and errors | SEC-03, OPS-04, design §4.1 | `test_redaction.py` |
| One error family with stable codes | Design §4.1, §10.2 (library documentation, Q37) | `test_errors.py` |

Not covered: all of this runs against a scripted fake transport. No real transport exists, and nothing
has been checked against Moodle (every check in `contracts/moodle-ws.v1.md` §5 is open).
