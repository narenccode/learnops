# Changelog

All notable changes to LearnOps, by release. The newest release is first. Release notes with limitations
are in `docs/releases/`.

## Release 0 (in preparation; NOT frozen, tagged or accepted)

Written 28 November 2026 from the contents of `main` (`c29f250`). "On main" means merged, not accepted: the
state of each item, and what is still missing, is in `docs/releases/r0.md` and
`docs/release-0/freeze-readiness-checklist.md`. Only the guide freezes and tags (PRD D2).

### Added

- **Contracts (PRD Part B), as files on `main`:** B1 course package, B2 course model, B3 LTI 1.3 launch,
  B4 Moodle web services, B5 model interface, B6 lesson manifest with slides, cues and chapters, B7 H5P
  practice. Each has a schema, examples and tests under `contracts/` and `libs/contracts/tests/`. None is
  declared frozen yet. B4 freezes separately (decision 0018).
- **`libs/contracts`:** validators for B1 course packages and course-level rules, and the repository-wide
  contract example validator with its CI step (EXT-09).
- **`libs/media_paths`:** B6 media path templates (Release 0 library, PRD D1).
- **Test data (B8):** folders for B8.1 template course, B8.2 sample course, B8.3 planted errors, B8.4
  synthetic submissions, B8.5 lecture videos and B8.6 model comparison. B8.3 holds 14 variants mapped to the
  rules; 4 are packages, and the 10 `.mbz` variants are not built (they need the Moodle 5.3 lab).
- **Design documents:** studio, grading and video are `Approved`; checker is `Draft`.
- **Decision records:** `docs/decisions/0001` to `0019`.
- **Repository standards:** CI (tests, lint, types, secret scan, dependency audit), pre-commit, code owners, the
  review handbook and `docs/RELEASING.md`.

### On main but not part of Release 0 (PRD D1: first release that uses them)

- `libs/model_interface` and the speech interface (Release 3), `libs/moodle_ws` (Release 1 for the Checker's
  course lookup), `libs/speech_eval`. `libs/lti` is not on `main`.

### Changed

- Nothing: Release 0 is the first release.

### Known limitations

See `docs/releases/r0.md`. In short: no Course Checker code, role tests or harness (Release 1); no restore or
role matrix has run on the lab; the B8.2 `.mbz` and the 10 B8.3 `.mbz` variants (nine, plus CK-08) are lab
work. The B8.1 backup is already built and published (release `testdata-b8-1-v1`, 24 November 2026).
