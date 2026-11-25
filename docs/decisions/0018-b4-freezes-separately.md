# Contract B4 freezes separately, after its lab checks

**Status:** decided by the guide (chat with his assistant, 2026-11-25, posted on issue #186).
**Number:** 0018, the next free number when this was written (2026-11-25: `main` has 0001 to 0014; open
pull requests #209 and #223 take 0015 and 0016; 0017 is "Moodle 5.3 only"). It is taken again at merge if
another record has merged first.

## Decision

Contracts B1, B2, B3 and B5 to B8 freeze at the end of Release 0, as PRD B.0 rule 2 and D1 say.
**Contract B4 freezes on its own**, when its lab checks (`contracts/moodle-ws.v1.md` section 5) pass on
Moodle 5.3, and before the first release whose code calls it. B4 is used by Modules 2 and 3 (PRD B.0
table), so it freezes before whichever of them first calls it.

## Reason

Two texts disagreed: the guide's ruling on PR #27 (recorded in the B4 contract, section 6: B4 "cannot be
frozen at the end of Release 0 until the checks pass") and PRD D1 (contracts B1 to B8 frozen in Release 0;
lab items in the first release that uses them). Freezing B4 separately keeps both: nothing is frozen before
it is verified, and the Release 0 freeze does not wait for the lab.

## Effect

- Until B4 freezes, a change to it follows PRD B.0 rule 3 as before the freeze.
- PRD D1 says B4 freezes separately and points here.

## Where it was decided

- Guide, chat with his assistant, 2026-11-25; [posted on issue #186](https://github.com/narenccode/learnops/issues/186#issuecomment-7157429478).
