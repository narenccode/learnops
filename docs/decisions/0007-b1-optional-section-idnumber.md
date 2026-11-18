# B1: the section `idnumber` is optional

**Status:** Proposed in a contract-change pull request; the guide decided the rule on issue #65
(2026-11-12) and approved the scope D1 to D7 on 2026-11-15.
**Number:** 0007 was the next free number when this change was prepared (2026-11-16). Open pull
requests already claim 0001 to 0006. The guide's rule is to take the next free number at merge, so
rename this file if another record merges first.

## Decision

1. **Identity.** Sections are matched by their **number** everywhere: a restore, a reverse import
   (FR-S-08), the round trip (PRD C1.7) and the course-model comparison (FR-C-05). Moodle stores no
   `idnumber` for a section: the `course_sections` table has none, the section file inside a backup
   has none, and a restore matches an existing section by its number only. The guide read Moodle's
   source for 4.5 and 5.3 and confirmed it for both.
2. **B1.** A section's `idnumber` is an optional **authoring label** for Studio that Moodle never
   stores. A section may leave it out. When it is present it must be a valid idnumber and is unique
   within the package (B1.2 rule 6). A reverse import leaves it out. Activities keep a required
   `idnumber`.
3. **Only an absent field is valid.** `null` and an empty string stay schema errors (D3). A reader
   that has no label writes nothing.
4. **CK-07 does not apply to a section without an `idnumber`**, because a protected item is defined
   by its `idnumber` (B1.4). The protected section is still found by its number (`protected_section`).
5. **Validator.** `course_rules.iter_items` skips a section without an `idnumber`: it never yields an
   empty string or `None`. So two sections without one are not duplicates of each other, an absent
   idnumber is not reported by CK-06, and `validate_package` does not raise `KeyError`. The schema
   change and the validator change are in the same pull request (D1), because the schema alone would
   make valid packages fail in the validator.

## Why

B1 required a section `idnumber` while B2 said that a section `idnumber` read from a `.mbz` is always
`null`. The two contracts could not both hold through the round trip, and FR-S-08 could not recover a
value that Moodle does not store. The platform stores nothing, so the identifier is an authoring
label and the identity of a section is its number.

## Left open on purpose

- **Duplicate section numbers (D2).** No new uniqueness rule for section numbers is added here. The
  schema requires `number` of at least 1 and the validator does not check that numbers are unique.
  This was deliberately left to a later decision.
- **The glossary (D5).** It already says the identifier is optional for an activity or a section, so
  its wording is unchanged.
- **The Studio design note (D7).** The consequence for sections-only mode (a merge restore keeps the
  name and summary of a section that already exists at that number, so generated sections must use
  numbers after the template's last section) goes into the Studio design document in a separate
  change. Studio (M1) is an affected owner of this contract change, because Studio writes the field.
- **The `relative_path` rule.** The guide first asked for it in this pull request; it is pull request
  #94, approved separately.

## Affected owners

B1 is used by M1, M2 and M3 (PRD B.0). The checker (M2) reads sections by number (FR-C-05, in its own
pull request #46). Studio (M1) writes the field. The grading design (M3) does not mention a
section `idnumber`.

## Changed files

`contracts/course-package.v1.schema.json`, `contracts/examples/course-package.v1/course-without-section-idnumber.yaml`
(new), `libs/contracts/course_rules.py`, `libs/contracts/tests/test_course_package_v1.py`,
`libs/contracts/tests/test_validate_course.py`, `libs/contracts/tests/test_validate_package.py`,
`docs/PRD.md` (B1.1 example comment, B1.2 rule 6 and the paragraph after it), `docs/traceability.md`.
