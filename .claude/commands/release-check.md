---
description: Check whether a release meets the freeze criteria (PRD §D2)
argument-hint: <release number, e.g. 1>
---

Check whether Release $ARGUMENTS can be frozen. Use PRD §D1 for its contents and §D2 for the criteria.
Report each criterion as pass / fail / unknown with evidence (file, command output, link). Do not tag
anything.

1. Every FR tagged for this release: implemented? linked to passing tests in `docs/traceability.md`?
2. The module's acceptance criteria (PRD §C.x.7): each one, with the evidence that proves it.
3. Latest integration-harness report: restore + role tests + smoke tests on Moodle 4.5 **and** 5.3, all passing?
4. Contracts: unchanged since the last release, or changed only through §B.0 (check git history of `contracts/`).
5. README, `.env.example`, changelog updated for this release.
6. Security items (PRD §A13) relevant to this release reviewed; dependency scan clean.
7. Measurements due in this release (PRD §A3 goals) recorded with data set, method, date, and who measured.
8. Release notes drafted: contents, known limitations, upgrade steps.

End with a one-line verdict (ready / not ready) and the list of blockers. The guide performs the adoption test and the tag.
