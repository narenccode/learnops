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

## B7 H5P practice output contract (v1), Release 0 foundation, DRAFT

Files: `contracts/h5p-practice.v1.md` (normative text), `contracts/h5p-practice.v1.schema.json`,
`contracts/examples/h5p-practice.v1.content-types.json`, `contracts/examples/h5p-practice.v1/`
(an example package, with no `.h5p` file), the `file` field in
`contracts/course-package.v1.schema.json`, and the tests `test_h5p_practice_v1.py` and
`test_course_package_v1.py` in `libs/contracts/tests/`. B7 has no requirement ID of its own in the
PRD (it is a contract, PRD B.0). It is used by FR-S-12 and FR-V-14 (Release 5, stretch) and by
FR-C-03 CK-11 (Release 1). No row in the table at the top maps to it.

**Status: draft, not approved, and it cannot be frozen** until the H5P library versions are
verified in the lab (PRD App-C item 5; guide's answer 5 on Issue #44). This section is separate
from the B1 section above, which another pull request is also changing.

### Enforced by the B1 schema and covered by automated tests

Test names are in `test_course_package_v1.py`.

| Rule | PRD | Test(s) |
|---|---|---|
| An `h5p` activity must have `graded: false` | B7 | `test_missing_required_field_is_rejected`, `test_wrong_type_or_value_is_rejected`, `test_h5p_missing_field_is_named_and_only_that_field` |
| An `h5p` activity must have `file` | B7, Issue #44 answer 2 | `test_missing_required_field_is_rejected`, `test_h5p_missing_field_is_named_and_only_that_field`, `test_wrong_type_or_value_is_rejected` |
| `file` is a relative path ending in lowercase `.h5p`; URLs, absolute paths, `..`, backslashes, other or upper-case extensions and an empty name are rejected | B7, C-08 | `test_h5p_file_that_is_not_a_relative_h5p_path_is_rejected` |
| `file` is not checked on other activity types (it is an unknown field there) | Issue #44 answer 2 | `test_valid_variation_is_accepted` |
| An `h5p` activity cannot take a protected idnumber | B1.4 | `test_h5p_with_a_protected_idnumber_is_rejected` |

### Enforced by the B7 schema and tests

Test names are in `test_h5p_practice_v1.py`. Rows that say "example only" check the example
package, not packages in general.

| Rule | PRD | Test(s) |
|---|---|---|
| The content-type schema is valid and its example validates; bad lists are rejected: invented names, other capitals, machine names, half a phrase, a name listed twice, a missing name, a wrong schema name, an empty list | B.0 rule 1 | `test_schema_is_valid_and_example_validates`, `test_invalid_content_type_list_is_rejected`, `test_missing_root_field_is_rejected`, `test_unknown_fields_are_accepted` |
| The schema enum holds exactly the four phrases PRD B7 uses, and the example lists all four; the contract text says interactive video is for lab demonstrations only (a rule of the text, not a schema field) | B7 | `test_schema_enum_and_example_hold_exactly_the_prd_phrases` |
| The schema and example have no key `version`, `library`, `libraries` or `machine_name`, no string like `H5P.<letter>`, and no key `cue`, `cues` or `ref`. Other ways to write a version are not detected | App-C item 5, B6.2 | `test_no_listed_machine_name_version_or_cue_key_is_defined` |
| Every content type is marked "to verify in the lab"; the text says it cannot be frozen, keeps its open decisions marked, and says practice is optional and never graded | B7 | `test_text_marks_versions_open_decisions_and_the_draft_rules` |
| `file` is defined in the `h5p` branch of the B1 schema only | Issue #44 answer 2 | `test_file_is_defined_in_the_h5p_branch_only` |
| Example only: the package validates against B1; its week has one Page and one Assignment; its ordinary practice item is ungraded, names a lowercase `.h5p` path that does not exist, and comes right after the guide Page | B1, B7 | `test_example_package_validates_against_b1`, `test_example_week_is_standard_with_an_optional_practice_item` |
| No `.h5p` file exists anywhere in the repository | Issue #44 answer 7 | `test_no_h5p_file_is_kept_in_the_repository` |

### Documented but not automatically enforced

| Rule | PRD | Where the PRD places it |
|---|---|---|
| An ordinary practice entry comes right after the week's guide Page, and a week has one Page and one Assignment, in a package in general | B7, B1.2 rule 1 | Needs validator code; B1.2 rule 1 is itself not enforced yet |
| Where a video checkpoint goes | B7 | Open decision; PRD B7 says "after the video" |
| A practice (H5P) activity has no grade item | B7 | CK-11 (FR-C-03, Release 1), on the course model (B2) |
| Media referenced by a full fixed URL instead of a relative path | C-08 | CK-12 (FR-C-03, Release 1) |
| The file named by `file` exists, and uses an allowed content type | B7 | No check exists; no real `.h5p` is kept in the repository |
| Interactive video only in lab demonstrations | B7 | A rule of the contract text; no check exists |
| AI-drafted items are approved by a mentor before they reach learners | C-09, FR-S-12 | A process rule of Studio, not a data rule |
| `cues.json` entries are valid | B6.2, FR-V-14 | The B6 cues schema does not exist yet |

### Open decisions and not mapped

Open: H5P library versions and whether "drag-the-words or drag-and-drop / ordering" is one type
(until the lab check, App-C item 5); the `ref` kinds of a cue (Student 4, in the B6 cues schema);
several practice items in one week and video checkpoint placement (the guide has not decided; B7
makes no rule). Not mapped: a row, demo step and Bloom level for FR-S-12 and FR-V-14, because the
PRD does not say schema tests count towards them. Adding M2 to the PRD B.0 "Used by" row is the
guide's change (Issue #44, answer 1) and is in the pull request description, not in `docs/PRD.md`.
