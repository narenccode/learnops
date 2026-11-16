# Traceability (PRD E4)

| Requirement | Test(s) | Demo step | Bloom level |
|---|---|---|---|

## B1 course package contract (v1), Release 0 foundation

Files: `contracts/course-package.v1.schema.json`, `contracts/examples/course-package.v1/`,
`libs/contracts/tests/test_course_package_v1.py`; the package validator in `libs/contracts/*.py`
(shared validator reference EXT-09: the schema stage, idnumbers unique within one package,
configured protected idnumbers, and reading a package folder with its body files) with its tests
`test_validate_course.py`, `test_validate_package.py`, `test_config.py` and `test_report.py`. B1 has no requirement ID of its own in the PRD (it is a contract, PRD B.0), so
no row in the table above maps to it.

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

### Enforced by validator code (`libs/contracts`) and covered by automated tests

`validate_course_document()` runs the schema on a parsed `course.yaml`, then (when the structure
is valid) the idnumber rules, and returns a report. `validate_package()` does the same for a
package folder: it reads `course.yaml` first and, when that is valid, also checks the body files. Settings come in through `ValidationConfig`;
the library reads no environment variables. Test names are in `test_validate_course.py`
(course.yaml as parsed data), `test_validate_package.py` (a package folder), `test_config.py` (the settings object) and `test_report.py` (the
report types).

**B1.2 rule 6 has two halves, and only the first is enforced.** The validator checks that
`idnumber`s are unique *within the one package it is given*. It does not check that an idnumber is
*never reused for a different activity* across package versions: that needs information about the
previous version of the package and an owner that is not assigned yet (Studio's design proposes a
comparison with the previous version, `docs/design/studio.md` §5 "Identity", which is a
proposal and not decided). Every
report lists that half as not checked (`idnumber_reuse_not_checked`). Rule 6 is therefore not
claimed as fully implemented.

| Rule | PRD | Test(s) |
|---|---|---|
| The schema is applied to a parsed `course.yaml`; every error is reported (not only the first), in a fixed order by place (list positions in numeric order: `sections[2]` before `sections[10]`), with its place, a message and a fix hint; an impossible calendar date and a document that is not an object are errors | B.0 rule 4, B1.1 | `test_example_document_has_no_errors`, `test_schema_errors_are_reported_with_their_place`, `test_every_schema_error_is_reported_not_only_the_first`, `test_errors_are_ordered_by_number_not_by_text`, `test_an_impossible_calendar_date_is_rejected`, `test_a_document_that_is_not_an_object_is_an_error` |
| The two default protected idnumbers are rejected with a clear message that names the place and says what to do; the validator reports each one once | B1.4 | `test_default_protected_idnumbers_are_left_to_the_schema`, `test_default_protected_idnumber_gets_a_clear_message` |
| **Uniqueness within one package** (first half of rule 6): `idnumber`s are unique in the `course.yaml` being checked. Sections and activities share one namespace. The later use in document order is the error, with its exact place, and the message names the first use. Reported in both modes. Two different duplicated ids are reported in document order | B1.2 rule 6 | `test_duplicate_idnumber_is_an_error_at_the_later_use` (7 cases, each with the exact error place and first-use place, including an activity reusing an earlier or a later section id), `test_an_idnumber_used_three_times_is_reported_for_each_extra_use`, `test_two_different_duplicated_ids_are_both_reported_in_document_order`, `test_similar_idnumbers_are_not_duplicates`, `test_duplicate_idnumbers_are_an_error_in_sections_only_mode_too` |
| **Not enforced: reuse across package versions** (second half of rule 6) is listed in every report as `idnumber_reuse_not_checked`, with a message that says why (it needs the previous version of the package) | B1.2 rule 6 | `test_cross_version_reuse_of_idnumbers_is_listed_as_not_checked`, `test_held_rules_are_reported_as_not_checked_never_skipped_silently` |
| Protected idnumbers a site adds to the two defaults are rejected on sections and activities, in both modes, with the exact place, the idnumber and a fix hint. They add to the defaults and never replace them, are matched exactly, and several can be configured. The result does not depend on the order in which they were given | B1.4 | `test_configured_protected_idnumber_is_rejected_in_both_modes`, `test_the_library_reads_no_environment_variables` (also: not protected unless configured), `test_only_an_exact_match_is_protected`, `test_several_configured_ids_are_each_rejected_in_document_order`, `test_protected_and_duplicate_problems_are_both_reported`, `test_a_default_protected_id_is_always_rejected_and_reported_once` |
| `ValidationConfig` accepts a collection of valid idnumbers and keeps its own immutable `frozenset` copy (later changes to the caller's collection do not reach it; equal configurations hash alike). It refuses with a `ConfigError` that says what to fix: a bare string or bytes (which would be read one character at a time), `None` or any non-collection, a mapping, a member that is not text, and an invalid idnumber (the first bad one in sorted order is named) | B1.4 | `test_config.py`: `test_default_configuration_adds_no_protected_idnumbers`, `test_several_configured_ids_are_kept_and_the_same_id_twice_counts_once`, `test_any_collection_of_idnumbers_is_stored_as_a_frozenset`, `test_the_configuration_cannot_be_changed_after_creation`, `test_changing_the_callers_collection_later_does_not_change_the_configuration`, `test_equal_configurations_are_equal_and_hash_alike_whatever_they_were_built_from`, `test_a_configured_idnumber_must_be_a_valid_idnumber`, `test_a_bad_idnumber_message_names_the_value_and_what_to_do`, `test_something_that_is_not_a_collection_of_idnumbers_is_refused`, `test_a_member_that_is_not_text_is_refused` |
| `validate_course_document()` refuses a `config` that is not a `ValidationConfig` (a dict, a list, a string, the class itself) with a `ConfigError` that says what to pass, before the document is read; it never ignores it | B1.4 | `test_an_unsupported_config_type_is_refused_not_ignored` |
| The library reads no environment variables; validation does not change the document it is given | CLAUDE.md §2.3 | `test_the_library_reads_no_environment_variables`, `test_the_document_is_not_changed_by_validation` |
| The idnumber rules run only when the schema finds no error anywhere in the document (an unrelated schema error holds them back too, and so does a document that is not an object). The report then adds `cross_rules_not_checked`, whose text names no rule so that it stays true as more rules are implemented | n/a | `test_any_schema_error_holds_back_the_idnumber_rules`, `test_a_document_that_is_not_an_object_is_an_error` (also checks the notice), `test_the_course_level_notice_names_no_rule` (a valid document has no such notice: `test_held_rules_are_reported_as_not_checked_never_skipped_silently`) |
| Rules that are not implemented are listed as "not checked" in every report, so that "no errors" is not read as "fully checked" (a design choice, not a PRD rule). A report for a parsed document lists nine (see the next section). A report for a package lists eight, because it checked the body files | n/a | `test_held_rules_are_reported_as_not_checked_never_skipped_silently`, `test_a_document_with_weekly_structure_problems_is_not_judged_here`, `test_example_package_has_no_errors` |
| A package folder is read through a `PackageSource`; `DirectorySource` never reads outside the folder: a path with `..`, an absolute path or a link that leaves the folder is refused, a link that stays inside is followed. A refused file is never read | B1.1 | `test_source_reads_an_existing_file`, `test_source_tells_a_missing_file_from_a_folder`, `test_source_refuses_paths_that_leave_the_package`, `test_source_refuses_a_link_that_leaves_the_package`, `test_source_follows_a_link_that_stays_inside_the_package` (the two link tests run on the Linux CI) |
| `validate_package()` reads `course.yaml` from the folder. A missing file, text that is not UTF-8, bad YAML (also an unquoted impossible date), and a file that is not an object are errors with a fix hint, never an exception; an unquoted real date fails the schema | B1.1 | `test_missing_course_yaml_is_an_error`, `test_course_yaml_that_cannot_be_read_is_an_error`, `test_an_unquoted_yaml_date_is_an_error`, `test_course_yaml_that_is_not_an_object_fails_the_schema` |
| **Body files exist** (B1.1: the package is a folder with `course.yaml` plus the Markdown files; implied, not a numbered rule). Each `body` must name a file inside the package, in both modes. A missing file, a folder and a link leaving the folder are errors at the activity, in document order, after the idnumber errors. A shared body file and an activity without a body are not errors. Only existence is checked, never the content | B1.1 | `test_missing_body_file_is_an_error_at_the_activity`, `test_every_missing_body_file_is_reported_in_document_order`, `test_body_that_is_a_folder_is_an_error`, `test_body_that_is_a_link_leaving_the_package_is_an_error`, `test_a_body_file_may_be_shared_and_an_activity_may_have_no_body`, `test_duplicate_idnumbers_are_reported_before_missing_body_files`, `test_any_package_source_works_and_only_course_yaml_is_read` |
| `body_files_not_checked` is listed for a parsed document (it reads no files) and for a package whose `course.yaml` could not be validated, and is left out only when the body files were checked. The idnumber rules and the settings apply to a package too, and a wrong `config` is refused before anything is read | B1.1 | `test_body_files_are_listed_as_not_checked_and_never_looked_for`, `test_body_files_are_not_checked_while_the_structure_is_invalid`, `test_the_other_course_rules_and_the_settings_also_apply_to_a_package`, `test_a_wrong_config_is_refused_before_anything_is_read` |
| A report is ok when it has no errors; "not checked" entries do not make it fail; issues cannot be changed after creation | n/a | `test_empty_report_is_ok`, `test_report_with_an_error_is_not_ok`, `test_not_checked_items_do_not_make_a_report_fail`, `test_issue_defaults_are_a_document_level_issue`, `test_issue_cannot_be_changed_after_creation` |

This is not FR-S-03 or FR-C-03: the checker's rules (CK-xx) work on the course model (B2), which
this library does not build.

### Documented but not automatically enforced

Nothing in the repository enforces these yet. Each is listed as "not checked" in every report the
validator returns (eight entries, plus the body files when they were not checked; the B1.3 row
has two of them, and rule 4 has none because it is not a package field).
The schema's `$comment` lists them too, and also lists the two parts that the validator now
enforces (rule 6 within one package, configured protected idnumbers). Updating that comment
needs a separate contract-change review and is not part of this change. The example package was
checked against these rules by hand when it was created; that check is not automated and is not
committed.

| Rule | PRD | Where the PRD places it |
|---|---|---|
| One guide Page and one task Assignment per week | B1.2 rule 1 | No checker rule is named for it (CK-01…CK-13) |
| Week N unlocks when the week N-1 task is submitted; `unlock.after` names an existing earlier activity | B1.2 rule 2 | Related: CK-04, CK-05 (FR-C-03, R1) |
| Graded points sum to `total_points` | B1.2 rule 3 | CK-03 |
| Assignments use marking workflow | B1.2 rule 4 | CK-10 (not a package field) |
| Completion tracking on for every activity used in an unlock rule | B1.2 rule 5 | CK-13 |
| An `idnumber` is never reused for a different activity (listed as `idnumber_reuse_not_checked`; uniqueness within one package is enforced above) | B1.2 rule 6, second half | The PRD states this rule. It cannot be judged from one `course.yaml`: it needs the previous package version, and no owner or checker is assigned yet (CK-06 covers duplicate or invalid idnumbers in the course model only) |
| Marking table present and valid: markers, columns, points sum, allowed `Check` names | B1.3, C3.5 | CK-09 |
| `protected_section` collision (configured protected idnumbers are enforced above) | B1.4 | `protected_section` has no default in the PRD; CK-07 covers the course model |

### Not mapped

Left out because the PRD does not establish the mapping:

- **A row, demo step and Bloom level for FR-S-03.** See the note at the top of this section. PRD
  C1.12 gives levels to kinds of work (for example "Design (L6): schema, validator, generator"),
  not to individual requirements.
- **FR-S-02, FR-S-04, FR-S-07, FR-S-08, FR-C-01, FR-G-01.** They touch B1 but need code that does
  not exist yet, and the PRD does not say that schema tests count towards them.
- **C1.7 "a package containing a protected idnumber is rejected with a clear message".** The
  validator reports the two default idnumbers with a clear message (tested above); the Course
  Studio screen and CLI that show it do not exist yet.
- **Requirement IDs for the contract work itself.** None in the PRD.

## B8.1 template course backup (test data), Release 0 foundation

Files: `testdata/b8-1-template-course/README.md` (the requirements, the proposals and the open
decisions, and a plain list of the expected protected items for the checker); the B8.1 entry in
`testdata/README.md`. B8.1 is a test data set (PRD §B8, B1.4) and has no requirement ID of its own,
so no row in the table at the top maps to it. This change is documentation only: no `.mbz`, no code
and no test exist for B8.1 yet.

| What is documented | PRD | Test(s) |
|---|---|---|
| The template course backup holds the four protected items: the final project assignment (`final-project`), the course feedback activity (`course-feedback`), the course completion criteria and the course badge. The idnumbers are the PRD defaults and are configurable. The protected section number (3) is a proposal | B8.1, B1.4 | None yet: the `.mbz` does not exist |
| A plain list of the expected protected items (idnumber, type, section, count) for the checker, which builds its model from the `.mbz` | B8.1, B1.4 | None yet |
| A sections-only backup is merged into the template and the protected items stay unchanged. The intended comparison writes down the same table for each protected item before and after the merge, with the fields type, name, idnumber, section number, points, completion setting and visibility, and the two tables must be equal (Owner, Issue #55, 2026-11-12); no check or test implements this yet. The Release 0 backup procedure is written as an untested draft | B1.4, C1.7, App-C item 2 | None yet: needs a Moodle site |
| Moodle 4.5 is the owner-confirmed build version. The owner stated that a 4.5 backup restores into the same or a newer Moodle version, including 5.3. That 4.5-to-5.3 restore is the owner's statement, not a result. The owner decided to build once on 4.5, test the restore on 4.5 and on 5.3, and not test 5.3 to 4.5, recording the Moodle version, the date and the outcome of each restore (Issue #55, 2026-11-12) | C-03 | None yet: not verified; needs Moodle lab testing on 4.5 and 5.3 |

### Not covered here

These are pending and are not claimed by this change:

- **The `.mbz` backup, its SHA-256, the release asset (tag `testdata-b8-1-v1`) and the download
  script.** None of them exists yet.
- **Moodle 4.5 and 5.3 verification:** the restore, the protected items, the completion criteria,
  the badge and the sections-only merge (PRD C1.7, App-C item 2). The owner's statement that a 4.5
  backup restores on 5.3 has not been verified.
- **The decision record for App-C item 2** (`docs/decisions/NNNN-b8-1-template-course.md`). It is
  not written; the next free number is taken when you merge, after rebasing (Owner, Issue #55). The
  owner also asks for a short, text-only results table in it that names the local evidence files;
  screenshots and logs stay local and are not committed.
- **The open decisions** in the B8.1 README (§9) are pending guide confirmation. This entry does
  not settle them.

## B8.5 lecture video test data set, Release 0 foundation

Files: `testdata/b8-5-lecture-videos/` (README, folder `.gitignore`, placeholder outlines and
transcripts), the B8.5 inventory in `testdata/README.md`, the guide's decision
`docs/decisions/0004-b8-5-lecture-videos.md`, and the validation test
`libs/contracts/tests/test_b8_5_dataset.py`. B8.5 is a test data set (PRD B8), not a functional
requirement, so it has no FR ID and no row in the table at the top. It is the data for PRD G-6
(caption word error rate, Release 3), App-C 7 (the error-rate target from a first baseline run)
and App-C 8 (licence or consent for every B8.5 video).

**Status: PENDING.** No lecture is recorded, no consent line is written and no transcript is
typed. The tests show that the committed placeholders are well formed and that the PENDING status
is true. They do **not** show that B8.5 or App-C 8 is met.

### Enforced by the test and covered by automated tests

The checker in `test_b8_5_dataset.py` runs on the real set in this pull request, through two tests:

| Rule | Source | Test(s) |
|---|---|---|
| The committed set has no errors: the ten fixed columns and well-formed rows, at least 5 lectures with unique `lecture-NN` ids, each cell in its documented form, outlines and transcripts that exist, a decision record with the exact consent sentence and a well-formed `## Consent lines` section, and the files Git tracks in the set folder are exactly the permitted paths | B8.5, decision 0004, set README | `test_the_real_set_has_no_errors` |
| The Status is true: both READMEs agree; COMPLETE needs no gap and a real Total line; PENDING needs something still missing and keeps the Total line PENDING; the total is checked against 1800 s once durations are filled in | B8.5 (at least 30 minutes, PRD §B8 as updated in #47), decision 0004 | `test_the_real_status_is_true` |

### Not yet covered by tests

The checker also contains rules that the real set (PENDING, no consent lines) does not exercise,
for example duration and SHA-256 forms, consent-line forms, placeholder detection, the Total line
and Git inspection. Tests that run the checker on broken, partly filled and complete synthetic
sets, and on `git ls-files` itself, are not in this pull request. Until they are added, those
rules are implemented but **not shown to work**.

### Not verified (by this test or anything else in the repository)

- That a recording exists, that its duration and SHA-256 are right, that the speech is Indian
  English, or that the speaker spoke from the outline (checked by people).
- That a transcript is accurate (Harshitha's check) and which model, if any, drafted it.
- That recordings are stored as agreed, and that speakers were told about the interim storage.
- That a speaker personally wrote their consent line (shown by Git history and review).
- Any use of the set by the video pipeline or the caption error-rate measurement (G-6, App-C 7);
  no Moodle restore, checker, BigBlueButton or Moodle 4.5/5.3 integration is involved or tested.

## B6 lesson manifest contract (v1), Release 0 foundation

Files: `contracts/lesson-manifest.v1.schema.json`, `contracts/examples/lesson-manifest.v1/`
(`single-track.json`, `camera-screen.json`: one top-level file per example),
`libs/contracts/tests/test_lesson_manifest_v1.py`. B6 has no requirement ID of its own in the PRD
(it is a contract, PRD B.0), so no row in the table above maps to it.

FR-V-08 ("Write `lesson.json` (B6.3) last, only when all required files exist", Release 3) is
deliberately not in the table above. The tests below cover only the schema that FR-V-08 and the
C4.7 criterion "`lesson.json` validates against B6.3" will be checked against. FR-V-08 gets its row
in the pull request that implements it.

### Enforced by the JSON Schema and covered by automated tests

Structure only. Test names are in `test_lesson_manifest_v1.py`.

| Rule | PRD | Test(s) |
|---|---|---|
| `schema` equals `learnops.lesson/v1` | B6.3 | `test_missing_required_field_is_rejected`, `test_wrong_type_or_value_is_rejected` |
| Nine root fields required: `schema`, `course_slug`, `lesson_id`, `title`, `duration_s`, `tracks`, `captions`, `transcript`, `chapters`; `slides`, `cues`, `summary`, `source`, `processing` optional | B6.2, B6.3 | `test_schema_requires_exactly_the_nine_root_fields`, `test_missing_required_field_is_rejected`, `test_valid_variation_is_accepted` |
| Exactly one `main` track | B6.2, B6.3 | `test_invalid_track_is_rejected`, `test_example_manifest_is_valid` |
| At least one caption with `lang` exactly `en` (`hi`, `EN` or `en-US` alone is rejected), because B6.2 requires `captions.en.vtt` (guide decision) | B6.2, B6.3 | `test_captions_without_english_are_rejected`, `test_captions_with_english_are_accepted`, `test_valid_variation_is_accepted` |
| Track roles are open lowercase names (slug form); known roles `main`, `main-low`, `camera`, `screen`; others such as `audio` accepted | B6.3 | `test_invalid_track_is_rejected`, `test_added_track_with_known_or_new_lowercase_role_is_accepted`, `test_examples_use_every_known_track_role` |
| A single-track lesson stays valid when `camera` and `screen` tracks are added | C4.7, EXT-03 | `test_single_track_lesson_stays_valid_with_camera_and_screen_added` |
| Every path is relative (`$defs/relative_path`): non-empty; forward slashes only; no whitespace; no `?`, `#` or backslash; no URL scheme or drive letter; not absolute; no empty, `.` or `..` segment; no Unicode control or format character (the complete Unicode 15.0.0 categories Cc and Cf, pinned; private-use, surrogate and unassigned code points accepted; guide decision); no `%` anywhere, so no percent-encoded form however often encoded (`%2e`, `%252e`, `%25%32%65` and so on; guide decision, because the B6.4 `none` signer appends the path to the media base URL and layers may decode it; paths are never decoded). Applied to all eight path fields: the seven file paths (`tracks[].file`, `captions[].file`, `transcript`, `chapters`, `slides`, `cues`, `summary`) are relative to the lesson folder, and `lesson_id` is relative to the course folder (readers build the lesson folder's path from it). Valid and invalid cases come from the shared vectors `contracts/test-vectors/relative-path.v1.json`. The schema defines the rule; `libs/media_paths` (B6.1 folder paths, the B6.4 `relative_path` argument) is to follow the same vectors, tested in its own pull request | B6.1, B6.3, B6.4, C-08, EXT-09 | `test_path_that_is_not_relative_is_rejected`, `test_valid_relative_path_is_accepted`, `test_every_path_field_in_the_schema_is_tested`, `test_path_vectors_cover_every_rule`, `test_path_vectors_have_no_duplicates`, `test_lesson_id_that_is_not_a_relative_path_is_rejected`, `test_lesson_id_that_is_a_lesson_slug_path_is_accepted`; Cc and Cf `test_python_unicode_database_is_the_pinned_version`, `test_unicode_15_0_has_2_cc_and_21_cf_ranges`, `test_schema_rejects_exactly_cc_and_cf_among_all_code_points`, `test_every_cc_and_cf_range_is_rejected_at_its_edges_and_inside`, `test_code_point_next_to_a_cc_or_cf_range_is_accepted`, `test_private_use_surrogate_and_unassigned_are_not_rejected_by_category`, `test_every_path_field_rejects_control_and_format_characters`; percent sign `test_percent_sign_is_rejected_in_every_segment`, `test_every_path_vector_with_a_percent_sign_is_invalid` |
| `course_slug` is lowercase ASCII with hyphens | B6.1 | `test_invalid_course_slug_is_rejected` |
| Unknown fields are accepted | B.0 rule 2, EXT-02 | `test_valid_variation_is_accepted` |
| The manifest is a JSON object (an array, a string, a number or `null` is rejected) | B6.3 | `test_document_that_is_not_an_object_is_rejected` |
| The schema is valid; both examples and the PRD B6.3 example validate | B.0 rule 1 | `test_schema_is_a_valid_draft_2020_12_schema`, `test_example_manifest_is_valid`, `test_prd_example_is_valid` |

Enforced and tested, but chosen in the schema rather than stated as a rule in the PRD (to be
confirmed by the contract reviewers): `source.kind` is required inside `source` but is any non-empty string (the PRD names only
`upload`); `captions` not empty; `height` a positive integer; `duration_s` a non-negative number;
`processing.completed_at` an RFC 3339 timestamp with a time zone; non-empty strings. Tests:
`test_invalid_completed_at_is_rejected` (`completed_at`), `test_missing_required_field_is_rejected`,
`test_invalid_track_is_rejected`, `test_wrong_type_or_value_is_rejected`, `test_valid_variation_is_accepted`.

### Documented but not automatically enforced

| Rule | PRD | Where the PRD places it |
|---|---|---|
| The files the manifest names, and `poster.jpg`, exist in the lesson folder | B6.2 | FR-V-08 (R3) |
| `lesson.json` written last, only when all required files exist | B6.2 | FR-V-08 (R3) |
| `course_slug` and `lesson_id` match the folder's place in the path template | B6.1 | `libs/media_paths` (Release 0, separate pull request) |
| Calendar validity of `processing.completed_at` (for example no 31 February) | — | Only with a `date-time` format checker (`rfc3339-validator`, not installed in CI) |
| Contents of `transcript.en.json` (B5.4 shape) | B5.4, B6.2 | B5 contract (no schema in `contracts/` yet) |
| Shapes of `chapters.json`, `slides.json`, `cues.json` | B6.2 | No schema yet |
| Windows reserved names (such as `CON`, `NUL`, `COM1`) and Unicode normalization in paths: considered, not v1 rules (guide decision) | B6.3 | Not enforced in v1: the store is on Linux or S3 and no consumer compares names; a v2 discussion if a store later needs them |
| A maximum path length | B6.3 | None specified in v1 (guide decision): paths are built from bounded slugs and the store enforces its own limits |

## B3 LTI launch contract (v1), Release 0 foundation

Files: `contracts/lti-launch.v1.md`, `contracts/lti-launch.v1.schema.json`,
`contracts/examples/lti-launch.v1/` (`instructor-mentor.json`, `institution-administrator.json`,
`mentor-minimal-with-unknown-field.json`: valid examples only), the optional-claim vectors
`contracts/test-vectors/lti-launch-optional-claims.v1.json`, and
`libs/contracts/tests/test_lti_launch_v1.py`. Decision record: `docs/decisions/0001-lti-library.md`.
B3 has no requirement ID of its own in the PRD (it is a contract, PRD B.0), so no row in the table
at the top maps to it.

**Tests for this contract (PRD B.0 rule 3).** In Release 0 the shared contract tests listed below
are the tests that cover B3. A consuming module adds its own tests when its code that reads the
contract exists; before that, the shared contract tests cover the change. No placeholder or skipped
module tests exist, and none are planned here.

SEC-01, SEC-02, SEC-06, SEC-09, EXT-07 and FR-X-01 are deliberately not in the table at the top.
Nothing in this contract's tests implements them: the launch validation, session and refusal
behaviour belong to `libs/lti`, which does not exist yet (ADR 0001, Stage 2 not approved). Each gets
its row in the pull request that implements and tests it.

### Enforced by the JSON Schema and covered by automated tests

Structure only. Test names are in `test_lti_launch_v1.py`.

| Rule | Contract section | Test(s) |
|---|---|---|
| The schema is a valid Draft 2020-12 schema with the B3 v1 `$id` | PRD B.0 rule 1 | `test_schema_is_valid_draft_2020_12` |
| Every example validates; the examples folder holds valid examples only (JSON files, none invalid) | PRD B.0 rule 1, §11 | `test_examples_folder_has_the_required_examples`, `test_examples_folder_holds_json_files_only`, `test_every_example_is_valid` |
| Required fields at every depth: `iss`, `sub`, `deployment_id`, `message_type`, `role`, `context`, `context.id`, `resource_link`, `resource_link.id` | §4 | `test_invalid_launch_result_is_rejected_at_the_right_place` (one `missing-…` case each), `test_every_required_field_has_a_missing_case` (fails if a required field has no case) |
| `message_type` is `LtiResourceLinkRequest` only | §2, §4 | `test_invalid_launch_result_is_rejected_at_the_right_place` (`wrong-message-type`) |
| `role` is one of the values in the schema's enum (currently `mentor`, `administrator`; the value set is under review, ADR 0001 OI-25) | §4, §5 | `test_both_baseline_roles_are_accepted`, `test_invalid_launch_result_is_rejected_at_the_right_place` (`role-…` cases) |
| `context.id` is a positive integer written as a string in ASCII digits: zero, negative, non-numeric, leading-zero, whitespace-padded, non-ASCII-digit and newline-containing values are rejected; no upper bound | §3.1 | `test_positive_integer_context_ids_are_accepted`, `test_invalid_launch_result_is_rejected_at_the_right_place` (`context-id-…` cases, including the trailing newline) |
| Required strings are non-empty strings; `sub` and `context.id` are strings, not numbers | §4 | `test_invalid_launch_result_is_rejected_at_the_right_place` (`empty-…`, `numeric-…`, `…-not-an-object` cases) |
| `name` and `email` may be `null` or absent; an empty string is rejected. `context.title` may be omitted; an empty string and `null` are rejected | §3.2, §4 | `test_optional_fields_may_be_absent_or_null`, `test_name_and_email_are_valid_when_null`, `test_name_and_email_are_valid_when_absent`, `test_context_title_is_valid_when_omitted`, `test_invalid_launch_result_is_rejected_at_the_right_place` (`empty-name`, `empty-email`, `empty-context-title`, `null-context-title`) |
| Unknown fields are accepted | PRD B.0 rule 2, EXT-02 | `test_unknown_fields_are_accepted` |

### Optional-claim rule (§3.2): shared vectors, covered by automated tests

The vectors in `contracts/test-vectors/lti-launch-optional-claims.v1.json` state the rule as data.
The tests check the vectors and the schema side only. **No normaliser exists:** the rule is to run
once, in `libs/lti`, which has not been created and must pass the same vectors when it is added.

| Rule | Contract section | Test(s) |
|---|---|---|
| `name`, `email`: absent, `null`, empty, White_Space-only and non-string values become `null`. `context.title`: the same values are omitted, never `null` | §3.2 | `test_claim_vectors_cover_every_row_of_section_3_2`, `test_claim_vector_agrees_with_section_3_2`, `test_expected_result_for_every_claim_vector_is_schema_valid` (every vector × `name`, `email`, `context.title`) |
| Every other string is preserved unchanged, character for character, including white space before, after and inside | §3.2 | `test_claim_vectors_cover_every_row_of_section_3_2` (padded cases must exist), `test_expected_result_for_every_claim_vector_is_schema_valid` (UTF-8 bytes equal the input) |
| "White_Space-only" is the 25 code points of Unicode 15.0.0 White_Space, not Python's `str.isspace()`: U+001C to U+001F, U+200B, U+FEFF, U+180E and U+2060 are kept | §3.2 | `test_python_unicode_database_is_unicode_15_0`, `test_vectors_file_lists_exactly_unicode_white_space`, `test_white_space_rule_is_not_python_isspace`, `test_each_white_space_character_alone_is_absent`, `test_isspace_only_character_is_preserved` |
| A non-string value is rejected by the schema, so a result can never carry one | §3.2, §4 | `test_invalid_launch_result_is_rejected_at_the_right_place` (`numeric-name`, `object-name`, `boolean-name`, `boolean-email`, `list-email`, `numeric-email`, `numeric-context-title`, `list-context-title`) |
| The schema alone accepts a White_Space-only string (the gap the normaliser closes) | §3.2 | `test_schema_alone_accepts_a_white_space_only_string` |
| Contract text names the vectors file and the `str.isspace()` distinction (drift guard) | §3.2 | `test_contract_section_3_2_names_the_vectors_file` |

### Documented but not automatically enforced

These rules are written in `contracts/lti-launch.v1.md`. No code enforces them today and no test
covers them. They belong to `libs/lti` (not yet created). ADR 0001 §12, LTI-01 to LTI-32, lists
*proposed* acceptance tests for the launch boundary: they are not approved (Stage 2 is not
approved), none exists yet, and none is claimed as working.

| Rule | Contract section | Where it belongs |
|---|---|---|
| Signature, `exp`, `aud`, `azp`, `iss`, `deployment_id`, message type, single-use nonce and state checks | §8, PRD SEC-01 | `libs/lti` |
| `iss` must exactly match a registered platform (no normalisation); an unverified `iss` only locates the candidate configuration for signature verification; B4 is called only through the client bound to the configuration for the registered issuer, with no fallback to another platform's client | §7.1 | `libs/lti` and the B4 client. The B4 owner has confirmed the registered-issuer and client-binding part; the exact-match and untrusted-until-verified wording is B3's. The guide's formal approval of the gateway as a B4 consumer (B4 pull request #27, ADR 0001 OI-15) is pending |
| Role-URI mapping and precedence; ignoring unlisted roles; refusal when no recognised role remains; refusal under EXT-07 | §5, §8, PRD A5, EXT-07 | `libs/lti`; each tool also refuses what it does not accept |
| Running the §3.2 normalisation of `name`, `email` and `context.title`, once, at the boundary. The rule and its vectors are tested above; no code performs it yet | §3.2 | `libs/lti` (not yet created), to be tested against `contracts/test-vectors/lti-launch-optional-claims.v1.json` |
| Session identity `(iss, sub, context id)`, two-hour idle expiry, course-context isolation | §6, §7, PRD SEC-02 | `libs/lti` and each module's authorisation |
| `name` and `email` never written to logs | §10.1, PRD SEC-06 | Every module's logging; no test yet |
| No raw ID token, nonce, state or key material reaches a module | §10 | `libs/lti` |

### Requirement text changed by this pull request

Wording only. These changes carry no new tests, because no code implements the requirements yet.

| Text | Change | Tests |
|---|---|---|
| PRD A5, rules paragraph | Role URIs not listed in B3 are ignored; a launch is refused only if no recognised role remains | None yet (`libs/lti`) |
| PRD B3 table | Claims split into inspected by the gateway and exposed to modules; `iss` added; session bound to `(iss, sub, context id)`; `shared.course_link` keyed by `iss` plus context id | The structure is covered by the schema tests above; the rest belongs to `libs/lti` |
| PRD EXT-07, FR-X-01, A5 player row | Learner wording is under review (ADR 0001 OI-25); see those PRD rows and the ADR for the current state | None (not implemented) |
| PRD B.0 rule 3 | One sentence added: a consuming module adds its tests when its code that reads the contract exists; before that, the shared contract tests cover the change | Not applicable (process rule) |
