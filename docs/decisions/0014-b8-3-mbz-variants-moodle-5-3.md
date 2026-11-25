# B8.3 `.mbz` variants: Moodle 5.3 only for Release 0

**Status:** decided by the guide on issue #112 (2026-11-23, item 22 of `docs/design/checker.md` §12).
**Number:** 0014, the next free number on `main` when this was written (2026-11-24: `main` has 0001 to
0013). It is taken again at merge if another record has merged first.

## Decision

For Release 0 the B8.3 planted-error `.mbz` variants (CK-01, CK-04, CK-05, CK-06 twice, CK-07, CK-08,
CK-10, CK-11 and CK-13; checker design §11.3) are built on **Moodle 5.3 only**. Moodle 4.5 is
**not tested**. It is not recorded as passed.

This is a **new** exception to PRD C-03 (everything works on Moodle 4.5 and 5.3), not a reading of an
earlier one: decision 0009 waives 4.5 for B8.1 only and says it must not be applied to any other data
set, and decision 0010 covers only the B8.2 restore and merge tests. The PRD text is not changed.

## Scope

The B8.3 `.mbz` variants only. It covers nothing else.

- The B8.3 package variants (CK-02, CK-03, CK-09, CK-12) need no Moodle at all and are not affected.
- C-03 still applies to the checker itself and to its harness (FR-C-08).

## Reason

The `.mbz` variants are made by restoring the B8.2 sample course and changing one setting; the CK-07
variant is made from the merged course with the B8.1 template. In Release 0, B8.1 and the B8.2 restore
and merge tests exist on Moodle 5.3 only (decisions 0009 and 0010), so there is nothing to restore on 4.5.

## Cost

On Moodle 4.5 the variants are a **rebuild, not a restore**: decision 0009 records that a 5.3 backup is
not expected to restore on 4.5, which is unverified. So each variant is made again by hand on 4.5 later.
The alternative, building on both versions now, was not chosen because it waits for the 4.5 lab.

## Ends

At the Release 1 restore and role-test matrix (PRD D2 item 3), when the variants are built on 4.5.

## Where it was decided

- Guide, issue #112, 2026-11-23, item 22:
  [5.3 first, a new narrow exception](https://github.com/narenccode/learnops/issues/112#issuecomment-7095842207).
- The exception row is in `docs/decisions/README.md`; other documents point there and here.
