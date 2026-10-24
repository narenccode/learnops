# Module 2 — Course checker, role tests, integration harness (owner: Student 2, integration lead)

Adds to the root `CLAUDE.md`; never overrides it. Spec: PRD §C2. Release 1; the harness grows every release.

## Scope
FR-C-01…09.

## Contracts
- **Owns:** B2 course model, B3 LTI 1.3 launch (and `libs/lti`). Changes only via `/contract-change`.
- **Uses:** B1, B4, B6 (rule CK-12), B7 (rule CK-11).

## Module rules
1. Every rule in the catalogue (CK-01…13) has an id, severity, message and fix hint, and at least one planted-error test case in `testdata/` (B8.3).
2. Unknown activity types are reported as "not checked", never silently skipped.
3. Role tests: 5 roles × 3 screen profiles (375×812; 1366×768 at 100/125/150 % zoom; 683×768) × Moodle 4.5 and 5.3. **Every role has at least one negative check** (something it must NOT see or do).
4. Role expectations live in data files (YAML per course), not in test code.
5. One automatic retry for a flaky browser step, then fail with a screenshot. Never add sleeps to hide timing problems.
6. The harness runs from a clean state with one command and produces one report. Keep it green; a red harness blocks every release.
7. The LTI gateway validates signature, issuer, audience, nonce, expiry and deployment id, and refuses the Learner role (EXT-07).

## Typical commands
`checker check <pkg|mbz> [--json]` · `checker diff <a> <b>` · `pytest tests/e2e -k <role>` · `harness run`
