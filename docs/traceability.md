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

The test runs on the real set (`test_the_real_set_has_no_errors`, `test_the_real_status_is_true`)
and on synthetic sets built in a temporary folder. Each negative case checks for its exact error
message, so an unrelated error cannot keep it passing.

| Rule | Source | Test(s) |
|---|---|---|
| A complete set passes and its table parses back unchanged; a PENDING set (also a partly filled one) has no errors | B8.5, decision 0004 | `test_a_complete_set_passes_and_parses_back`, `test_a_pending_set_has_no_errors_but_is_not_complete`, `test_a_partly_filled_pending_set_has_no_errors` |
| At least 5 lectures with unique `lecture-NN` ids; total at least 1800 s; a numeric Total line equals the sum | B8.5 (≥ 5 lectures), decision 0004 (≥ 1800 s) | `test_a_broken_complete_set_fails[four-lectures, below-1800-s, wrong-total-line, duplicate-ids]` |
| The ten fixed columns; every row has exactly as many cells as the header (a `\|` in a value, an extra or a missing cell is an error, never shifted or cut) | set README | `[wrong-columns, pipe-in-a-value, extra-trailing-cell, missing-cell]` |
| Each cell in its documented form: Duration as ASCII whole seconds above 0 (Unicode digits such as `³`, `٣٦٠`, `３６０` are rejected, never a traceback), a bare recording file name (no path or URL), 64 lowercase hex SHA-256, the lecture's own outline path, review `pending` or `checked`; a PENDING value is a gap | set README | `[pending-cell, duration-*, recording-path, recording-url, sha-short, sha-uppercase, wrong-outline-path, review-pending, review-unknown]` |
| Outline and transcript exist; one that is empty or has a line starting with `PENDING` anywhere is a placeholder; a placeholder transcript cannot be `checked`; finished text with no PENDING line passes | set README ("no `PENDING` line") | `[placeholder-*, outline-pending-on-a-later-line, transcript-pending-on-a-later-line, transcript-blank-lines-only, missing-outline]`, `test_completed_text_without_a_pending_line_is_not_a_placeholder` |
| Consent: the decision record exists, states the exact sentence and has a `## Consent lines` section; lines are well formed (name, valid date, exact sentence) and unique; a lecture's Consent cell points to an existing line with the Speaker's name (compared in full, commas included); one line per speaker; every line is used | B8.5 (written consent), App-C 8, decision 0004 | `[no-decision-record, no-consent-section, no-exact-statement, consent-*, one-speaker-two-lines, unused-consent-line]`, `test_a_speaker_name_with_a_comma_is_accepted`, `test_consent_lines_outside_the_section_are_not_counted` |
| The files Git tracks in the set folder are exactly the permitted paths (no recording, audio, draft, nested or unlisted file). Ignored or untracked local files (Thumbs.db, desktop.ini, editor swap and backup files) do not count; a failing or missing `git` is an error, never a clean result | decision 0004 (recordings never in Git), set README | `[audio-wav, audio-mp3, video-mp4, draft-transcript, nested-outline, unlisted-lecture, top-level-note]`, `test_only_the_exact_permitted_paths_are_allowed`, `test_only_files_tracked_by_git_are_inspected`, `test_a_failing_git_command_is_an_error_not_a_clean_set`, `test_missing_git_is_an_error_not_a_clean_set` |
| The Status is true: both READMEs agree; COMPLETE needs no gap and a real Total line; PENDING needs something still missing and keeps the Total line PENDING (a finished set whose Status and Total lines both still say PENDING fails) | set README | `test_a_false_status_fails` (7 cases), `test_a_finished_set_cannot_hide_behind_a_pending_total` |

Names in brackets are cases of `test_a_broken_complete_set_fails`; `*` stands for every case with
that prefix.

### Not verified (by this test or anything else in the repository)

- That a recording exists, that its duration and SHA-256 are right, that the speech is Indian
  English, or that the speaker spoke from the outline (checked by people).
- That a transcript is accurate (Harshitha's check) and which model, if any, drafted it.
- That recordings are stored as agreed, and that speakers were told about the interim storage.
- That a speaker personally wrote their consent line (shown by Git history and review).
- Any use of the set by the video pipeline or the caption error-rate measurement (G-6, App-C 7);
  no Moodle restore, checker, BigBlueButton or Moodle 4.5/5.3 integration is involved or tested.
