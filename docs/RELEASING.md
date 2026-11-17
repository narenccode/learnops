# Releasing

How a release is frozen, tagged and patched. The rules are in the PRD (§D1, §D2, §D3); this page says who does
what. A release is numbered, never dated.

## Who

| Role | Who | Does |
|---|---|---|
| Release owner | The owner of the module in the release (PRD App-A); Release 0: the integration lead | Steps 1 to 4 |
| Reviewer | The release owner's peer | Step 3 |
| Guide | The project guide | Steps 5 and 6 |

## Steps

1. **Scope.** Open an issue titled `Release N` that lists the FRs in the release (PRD §D1) and, for each, the
   merged pull request that implements it. FRs that will not be in the release are listed under
   **Known limitations**, with the release they move to.
2. **Release pull request.** On a branch `release/rN-prep` from `main`, update: `CHANGELOG.md` (what is new),
   `docs/releases/rN.md` (release notes: contents, known limitations, upgrade steps), the module README
   (install, configure, run, check, undo), `.env.example`, and `docs/traceability.md`. Run `/release-check`.
3. **Evidence table.** In the description of the release pull request, fill this table. Every row needs a link
   or a pasted result; "done" alone is not evidence.

   | PRD §D2 | Evidence |
   |---|---|
   | 1. Every FR of the release linked to passing tests | link to `docs/traceability.md` rows and the CI run |
   | 2. Acceptance criteria (§C.x.7) pass | the test or harness output for each criterion |
   | 3. Restore and role-test matrix on the lab Moodle versions | the harness report |
   | 4. Contracts unchanged, or changed only additively (§B.0) | `git diff` of `contracts/` since the last release tag |
   | 5. README, `.env.example`, changelog updated | links |
   | 6. Security items (§A13) reviewed; dependency scan clean | the scan output |
   | 7. Release notes written | link to `docs/releases/rN.md` |
   | 8. Adoption test | filled in by the guide |

   The reviewer checks every row, runs the tests, and approves. Auto-merge merges it.
4. **Release candidate.** After the merge, the release owner tags that commit `rN-rc1`
   (`git tag rN-rc1 <commit>` then `git push origin rN-rc1`; the next attempt is `rN-rc2`) and writes in the
   check-in issue: `Release N is ready for the adoption test: rN-rc1`.
5. **Adoption test (guide).** On a separate copy of the lab environment, install the release from the tag
   `rN-rcX` using only the README. If it fails, the guide writes what failed in the `Release N` issue; the
   release owner fixes it through a normal pull request and tags the next candidate.
6. **Tag (guide).** When the adoption test passes, the guide fills row 8, creates the tag `rN-v1.0` on that
   commit, publishes a GitHub release with the text of `docs/releases/rN.md`, and closes the issue. From then
   on the release is frozen.

## After the freeze (patches, PRD §D3)

- A bug in a frozen release is fixed on `main` first, through a normal pull request.
- If the fix must also reach the frozen release: the release owner creates the branch `release/rN` from the tag
  (only the first time), copies the fix there with `git cherry-pick`, and opens a pull request into
  `release/rN`. After it merges, the guide tags `rN-v1.0.1` (then `.2`, and so on) with release notes.
- No new features in a patch. Keep about one day a week at most for patch work.
