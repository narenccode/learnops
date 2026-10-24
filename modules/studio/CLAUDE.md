# Module 1 — Course Studio (owner: Student 1)

Adds to the root `CLAUDE.md`; never overrides it. Spec: PRD §C1. Release 2 (core), Release 5 (practice, stretch).

## Scope
FR-S-01…11 (Release 2); FR-S-12 practice (Release 5, only after the guide's go).

## Contracts
- **Owns:** B1 course package, B7 H5P output. Changes only via `/contract-change`.
- **Uses:** B2 course model (validation through the checker library), B3 LTI, B5 model interface (stretch), B6 media slugs.

## Module rules
1. `.mbz` output must restore on fresh Moodle **4.5 and 5.3**. Every build is restore-tested by the harness; a build that fails restore is a failed build.
2. `sections-only` output must never contain a protected `idnumber` or the protected section (PRD §B1.4). Treat any attempt as a validation error.
3. Generate the Moodle 4.5 backup format; never write Moodle 5.x-only structures.
4. Marking tables follow PRD §B1.3 exactly (HTML keeps `data-marking-table="v1"`); the grading assistant parses them.
5. Validation uses the shared checker rule library from `libs/`/`modules/checker`; never re-implement rules here.
6. `idnumber`s and slugs never change when titles change.
7. Practice items are always **ungraded** and mentor-approved (C-09, B7).
8. Reverse import must round-trip: package → `.mbz` → restore → backup → package gives no structural differences (checker diff).

## Typical commands
`studio validate <pkg>` · `studio build <pkg> --mode full|sections-only [--dry-run]` · `studio import-mbz <file>`
