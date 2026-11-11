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
| The grade-value source (`mod_assign_get_grades`) is only a pending proposal (rules §6a): in no contract list or PRD table, and no text claims it works | B4 draft rule (pending, guide) | `test_the_grade_value_source_is_only_a_pending_proposal` |
| Course lookup sends `field` and `value`, by course id or shortname, never idnumber | B4 course identification | `test_course_lookup_does_not_rely_on_idnumber` |
| The capability lists (needed, never granted) are the guide's and do not overlap; a custom role is required | B4, SEC-03 | `test_the_capability_lists_are_the_guides_and_do_not_overlap`, `test_the_custom_role_rule_is_stated` |
| Every lab check in rules §5 is still open on both versions | App-C 1 | `test_every_lab_check_is_still_open` |
| A replacement name for a Moodle version also appears in the PRD B4 text | B4 ("replacements recorded here") | `test_a_replacement_name_is_also_in_the_prd` |
| No verification state is stored in the schema or example | Guide, Q1 | `test_invalid_document_is_rejected_at_the_expected_place` (three verified-flag cases) |
| Schema is valid; example validates; invalid documents fail at the expected place; unknown fields are accepted | B.0 rule 1, rule 2 | `test_schema_is_a_valid_draft_2020_12_schema`, `test_example_is_valid`, `test_invalid_document_is_rejected_at_the_expected_place`, `test_unknown_fields_are_accepted` |
| One token variable per site with a placeholder; no single `MOODLE_WS_TOKEN` | B4, SEC-03, C-06; guide, Q24 | `test_one_token_variable_per_site_with_a_placeholder` |

### Documented but not automatically enforced

| Rule | PRD |
|---|---|
| Only the functions listed in the contract are called (`libs/moodle_ws` will build its allow-list from the example; the library does not exist yet) | B4 |
| One service account per site, with a token restricted to those functions and the capabilities in rules §4 (the lists are tested; that they are enough is lab check 9) | B4, SEC-03 |
| The token is stored only in the environment | SEC-03, C-06 |
| A grade write uses workflow state `readyforrelease`, never `released`, and counts as done only when both the state and the grade value are confirmed; the grade-value source is pending the guide's decision (rules §6a), so for now no write is reported as done; only approved drafts are written | B4, C-09 |
| Each function exists and behaves as expected with the parameters used on Moodle 4.5 and 5.3 (all 12 lab checks are still open) | B4, App-C 1 |

Open: when the lab Moodle sites are available (all twelve checks in `moodle-ws.v1.md` §5 wait for
them; B4 cannot be frozen until they pass), and the field for feedback comments inside `plugindata` on
`mod_assign_save_grade` (lab check 6). Q1, Q24 and Q37 are decided (PR #27).
