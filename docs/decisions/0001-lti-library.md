# ADR 0001: LTI 1.3 Launch Library Selection

**Status:** Proposed — pending guide review and approval

**Date:** 9 November 2026 (revised 15 November 2026 to record the B3 contract and the guide's decisions)

**Branch:** `contracts/b3-lti-launch`

**Decision owner:** B3 — LTI 1.3 Launch (Student 2, integration lead)

**Scope:** Selection and use of the Python LTI 1.3 library behind `libs/lti`

> **Decision boundary:** This ADR records a proposed library choice and the controls needed to use it safely. It does not approve dependency installation, application integration, or implementation. Those remain subject to the outstanding decisions and approval conditions below.

> **Two approval stages.** **Stage 1** approves the library choice and the pinned dependency and licence record (§17.2). **Stage 2** approves the security design, before any `libs/lti` implementation (§17.3). Neither stage has been approved. A one-page summary is in Appendix A.

---

## 1. Executive summary

The preferred candidate for LearnOps LTI 1.3 launch handling is **PyLTI1p3Next**, a maintained fork of the original `pylti1p3` project.

The candidate provides existing OpenID Connect and LTI 1.3 launch-validation functionality. Using it behind a LearnOps adapter is preferable to writing protocol and cryptographic handling from scratch.

The static source review also identified gaps between the candidate's inspected defaults and LearnOps requirements. In particular:

- The default launch-data storage is framework-session based, not the required server-side storage design.
- The inspected nonce-checking path does not demonstrate atomic, single-use nonce consumption.
- The inspected library does not consume OIDC state, and it records a successful state and ID-token hash as reusable. Together with the unconsumed nonce, a captured launch POST can be replayed (§6.7, §6.8).
- The candidate's cache storage needs its own session-ID cookie, `lti1p3-session-id`, a third cookie that is not in the guide's cookie policy (§8.7).
- The inspected defaults do not establish mandatory `exp` validation or the required audience and `azp` checks.
- The library supports multiple LTI message types; LearnOps v1 accepts only `LtiResourceLinkRequest`.
- No FastAPI-specific adapter was identified.
- `typing_extensions`, a direct runtime dependency, is PSF-2.0 licensed (verified for version 4.16.0, §5.1). The guide has since decided a broader licence policy that permits PSF-2.0 (§3.4, OI-01).
- The repository had no runtime dependency convention; the guide has since decided one: a root `requirements.txt` with exact pins (§3.4, OI-02).

**Proposed decision:** Select PyLTI1p3Next as the preferred candidate, conditional on implementing the LearnOps-specific controls and tests described here. The two dependency-policy questions have been decided by the guide (OI-01, OI-02). The licence policy is now written into PRD C-11 and root `CLAUDE.md` by PR #60 (`f8f6e35`); the root `requirements.txt` has not yet been created (§3.4, §5.4).

The most important blockers for guide review are:

1. **Decided by the guide:** dependency licence policy (OI-01; §3.4).
2. **Decided by the guide:** runtime dependency manifest and pinning convention (OI-02; §3.4).
3. How state and nonce single-use enforcement will be implemented.
4. Which server-side launch-data storage backend and configuration will be approved.
5. How strict expiry, audience, authorized-party, message-type, HTTPS, and session-isolation requirements will be enforced.
6. Whether the library's session-ID cookie (`lti1p3-session-id`) and its lifecycle are acceptable.

### 1.1 Decision status at a glance

**Decided by the guide** (requirements-level; recorded here, not implemented):

| Decision | Where |
|---|---|
| Session identity is `(iss, sub, context id)` | §3.2, §7.2, contract §6 |
| `shared.course_link` is keyed by `iss` plus context id | §13, contract §7 |
| The gateway is approved as a consumer of B4 (OI-15). B4 owns the `shared.course_link` columns; this approval does not approve or freeze them | §13, contract §7.1 |
| `context.id` stays a decimal string (positive integer, ASCII digits, no leading zero, no upper bound). B4 owns the form sent to Moodle and may pass the string unchanged; a value Moodle rejects fails closed at the B4 call | §13, contract §3.1 |
| Unlisted role URIs, including system administrator roles, are ignored; a launch is refused only if no recognised role remains | §10.3, contract §5 |
| Role URIs match exactly: the listed URIs only. The short name `Instructor`, the `TeachingAssistant` sub-role and any alias, prefix, case or scheme variant are unlisted, so they are ignored | §10.2, contract §5 |
| `mod/lti:admin` is not granted to non-site-administrators on the lab sites (OI-16). What Moodle sends for each persona is still to be checked in the lab | §10.2 |
| Role mapping: Instructor → `mentor`; institution Administrator → `administrator`; Learner refused by baseline tools (EXT-07); Administrator over Instructor; Instructor + Learner → `mentor` | §10.3, contract §5 |
| Only `LtiResourceLinkRequest` is required in v1; Deep Linking is not | §6.5, contract §2 |
| The schema describes the normalised launch result, not raw Moodle claims | §10.1, contract §1 |
| Invalid cases belong in tests or a vectors file, not in the valid examples folder | §10.1, §12 |
| OIDC state cookie `SameSite=None; Secure; HttpOnly`, short-lived, deleted after launch | §8.1 |
| Tool-session cookie `SameSite=Lax; Secure; HttpOnly`, two-hour idle session | §8.2 |
| Validate signature, `exp`, `aud` against the configured client ID, `azp` for multi-audience tokens, `iss`, `deployment_id`, message type and a single-use nonce | §6, §3.2 |
| Launch data is read only through the authenticated server-side session; raw JWTs and full tokens are not exposed to modules | §7.2, contract §10 |
| Forwarded-protocol headers are trusted only from explicitly configured proxies | §8.5 |
| Verification plan lives in Appendix B of this ADR, not in `docs/testing`; Moodle compatibility results belong in the release harness report (PRD E2) | Appendices B, C |

**Awaiting guide approval** (not decided):

| Item | Where |
|---|---|
| Storage ownership and migration responsibility (which schema, who owns the migrations) | §7.2, OI-06, OI-07 |
| CSRF protection mechanism | §8.6, OI-20 |
| Whether and how to handle the extra `lti1p3-session-id` cookie created by the candidate library, and its lifecycle | §8.7, OI-24 |
| Stage 1: library choice and pinned dependency and licence record, including the LGPL `jwcrypto` disclosure | §5.2, §17.2 |
| Stage 2: the security design as a whole, including the *mechanisms* proposed in §6 to §7 (consumption of state and nonce, lifetimes, leeway, the four overrides). The guide's decisions above fix what must be enforced; the way it is enforced is still proposed | §17.3 |

---

## 2. Context and problem statement

LearnOps launches its tools from Moodle using LTI 1.3. The shared LTI library must validate the platform launch and expose a normalized, trusted result to downstream modules.

The implementation must support, at minimum:

- ID-token signature validation.
- Issuer, audience, nonce, expiry, and deployment validation.
- Validation of the expected LTI message type.
- Validation of required launch claims.
- Moodle-to-LearnOps role mapping.
- A server-side application session with the agreed idle timeout.
- Authorization on every authenticated request using role and course context.
- Isolation of launch data between authenticated sessions.
- A stable interface for the Studio, Checker, Grading, and Video modules.

The PRD specifies a maintained open-source Python LTI 1.3 library with a compatible licence as the technology choice for Release 0. It also requires the LTI gateway to be a shared library rather than copied independently into modules.

Implementing the protocol and cryptographic validation ourselves would increase the amount of security-sensitive code LearnOps must own and maintain. The preferred approach is to use an existing library for protocol functionality and place LearnOps-specific policy behind `libs/lti`.

---

## 3. Requirements and authority

This ADR distinguishes requirements from the PRD, clarifications supplied by the guide, and proposed implementation choices.

### 3.1 PRD requirements

The following requirements are directly specified by the LearnOps PRD:

| Reference | Requirement relevant to this decision |
|---|---|
| A5 | Identity and role always come from Moodle through the LTI 1.3 launch; LearnOps keeps no passwords. The capability table gives Mentor (Instructor) access to their own courses ("courses where the user is Instructor", "own courses"), Administrator access to all courses, and Learner no baseline capabilities (Learner appears only in the Release 6 extension row). The rules below the table originally read: "a launch with any role not listed is refused with a clear message. A user sees only data for the course (LTI context) they launched from, except administrators." **Amended in this change** (OI-22): role URIs not listed in §B3 are ignored, and a launch is refused only if no recognised role remains; the course-context rule is unchanged. |
| C-11 | Open source under Apache-2.0. Third-party dependencies (runtime, development and CI alike) must have a permissive OSI-approved licence (for example MIT, BSD, Apache-2.0, ISC, PSF-2.0); weak copyleft (LGPL, MPL-2.0) only as an unmodified library; no GPL or AGPL. Each dependency's licence is recorded where it is declared (runtime: root `requirements.txt`; development and CI: `requirements-dev.txt`). This wording was introduced by PR #60 (`f8f6e35`), which implemented the guide's OI-01 decision (§3.4). |
| A10 | Use a maintained open-source Python LTI 1.3 library with a compatible licence, selected and recorded in Release 0. |
| B3 | Use `LtiResourceLinkRequest`; claims used now include `iss`; bind the server-side session to `(iss, sub, context id)` (amended in this change; it read `(sub, context id)`); expire after two hours idle; relaunch from Moodle to continue; `shared.course_link` is keyed by `iss` plus context id (amended in this change). |
| SEC-01 | Fully validate LTI launches: signature, issuer, audience, nonce, expiry, and deployment ID. |
| SEC-02 | Authorize every request from the LTI session using role and course context. |
| SEC-06 | Do not retain personal data beyond what LTI provides (name, email if shared, role); use test data only in the lab. |
| SEC-09 | Protect state-changing web requests against CSRF and use secure, same-site cookies for LTI sessions. |
| EXT-07 | **Current wording (amended in this change):** baseline tools refuse Learner-only launches; Learner access for the player and tutor is a planned extension, not currently supported; whether it can be enabled without changing the gateway or schema is unresolved (OI-25). *Historical, superseded:* the original wording said the gateway already validates Learner and that F-1 and F-3 "will enable Learner launches without changing the gateway". |
| FR-X-01 | **Current wording (amended in this change):** the Release 6 Learner launch is planned but conditional on OI-25 and the contract change that decision requires; it is not compatible with the v1 contract as it stands. |
| EXT-09 | Cross-cutting functionality belongs in one shared library per concern, including `libs/lti`. |

PRD B3's role-mapping row is also amended in this change: Learner-only launches are refused by baseline tools, and Release 6 Learner support is conditional on OI-25 (the original row said Learner is "accepted only by the player tool from Release 6"; that is historical and superseded).

The PRD's B3 session identity was written as `(sub, context id)`. The guide decided that the identity is `(iss, sub, context id)` (OI-21), and the PRD B3 text is amended in this change to match, so the PRD and this ADR now agree. The amendment is part of the contract pull request and is approved there, not by this ADR.

### 3.2 Guide clarifications

The guide has provided the following additional decisions. Evidence: the guide's comments on [GitHub Issue #58](https://github.com/narenccode/learnops/issues/58). Two of them were re-read for this revision and are cited by link where they are the source: the comment of 8 November 2026 ([issuecomment-6721370757](https://github.com/narenccode/learnops/issues/58#issuecomment-6721370757): role URIs, claims, refusals, sessions, course mapping) and the comment of 12 November 2026, 14:43 UTC ([issuecomment-6826722256](https://github.com/narenccode/learnops/issues/58#issuecomment-6826722256): OI-21, OI-22, OI-23, where the verification plan goes, the two approval stages). The bullets below keep their earlier attribution to Issue #58 and were not re-checked comment by comment.

- PyLTI1p3Next is the preferred candidate. Skip an Authlib + joserfc comparison unless an identified requirement cannot be satisfied by this candidate.
- Require `exp`; validate `aud` against the configured client ID and validate `azp` when multiple audiences are present.
- Validate issuer and deployment against the configured Moodle registration.
- Accept only `LtiResourceLinkRequest`.
- Enforce single-use nonce behaviour.
- Use server-side launch-data storage; do not retrieve launch data using a launch ID alone.
- Bind the authenticated session to `(iss, sub, context id)`.
- Use the same storage configuration for OIDC login and message launch.
- Baseline tools open in a new browser window.
- OIDC state cookie: `SameSite=None; Secure; HttpOnly`, short-lived, and deleted after launch.
- Tool session cookie: `SameSite=Lax; Secure; HttpOnly`, with a two-hour idle timeout.
- HTTPS is mandatory for all launches, including the lab. HTTP is allowed only for localhost development.
- Trust forwarded-protocol headers only from explicitly configured trusted proxies.
- Every authenticated request, including upload-chunk requests, counts as session activity.
- An unfinished upload is keyed to stable user and course identity, not a browser session ID.
- The Moodle institution administrator URI is the administrator marker; the system administrator URI is ignored.
- Administrator takes precedence over Instructor. Learner-only launches are refused by baseline tools, and a launch is refused when no recognised role remains. Unlisted roles are ignored when a recognised role is present (OI-22).
- Each tool declares its accepted roles. Baseline tools accept Mentor and Administrator. An earlier guide statement (historical) said Release 6 player functionality may add Learner without changing the gateway. It is not a current decision: it is not reconciled with the v1 schema, which has no Learner role value; it stays open as OI-25 (§10.4).

Further guide decisions recorded in this change. **Source:** the guide's comment on Issue #58 of 12 November 2026, 14:43 UTC, [issuecomment-6826722256](https://github.com/narenccode/learnops/issues/58#issuecomment-6826722256): Q1 is OI-21 (session identity and the `shared.course_link` key), Q2 is OI-22 (unlisted roles ignored; PRD §A5 corrected in the same PR), Q3 is OI-23 (the three paths; valid examples only; invalid cases in tests or a vectors file), Q4 is the verification plan as an appendix, and Q5 is the two approval stages with the list of items already decided. Where a bullet has a different source, it says so:

- Session identity is `(iss, sub, context id)`; `shared.course_link` is keyed by `iss` plus context id.
- Unlisted role URIs, including system administrator roles, are ignored; a launch is refused only if no recognised role remains.
- Only `LtiResourceLinkRequest` is required in v1; Deep Linking is not (PRD B3).
- The schema describes the normalised launch result, not raw Moodle claims.
- Invalid cases (no recognised role, Learner-only, missing context, wrong deployment) belong in tests or a vectors file, not in the valid examples folder.
- Launch data is read only through the authenticated server-side session (Q5). Raw JWTs and full tokens are not exposed to modules: that is the boundary of this contract (contract §10), consistent with the 8 November comment, where the schema holds what `libs/lti` hands to a module after validation.
- The verification plan is an appendix of this ADR, not a `docs/testing` folder.

### 3.3 Proposed implementation choices

The following are recommendations in this ADR, not independently confirmed PRD requirements:

- Keep PyLTI1p3Next behind a narrow adapter in `libs/lti`.
- Keep raw ID tokens and library-specific objects out of downstream module interfaces.
- Add focused tests for every security control that the library defaults do not establish.
- Keep the library's dependency and storage configuration centralized.
- Do not permit a launch identifier to act as an authorization credential.
- Treat unresolved dependency licences as blockers rather than assuming compatibility.

### 3.4 Guide decisions on dependencies (OI-01, OI-02)

Evidence: the guide's comment on Issue #58, dated 10 November 2026, is the source of the guide's decisions on both OI-01 and OI-02: <https://github.com/narenccode/learnops/issues/58#issuecomment-6759446683>.

**Policy documented:** PR #60 (`f8f6e35`, 10 November 2026) implemented these policy decisions in PRD C-11 (§3.1), root `CLAUDE.md` rule 10, `docs/design/TEMPLATE.md`, and CI (`.github/workflows/ci.yml` installs `requirements.txt` when the file exists).

**Not yet implemented:** the root `requirements.txt` has not yet been created, and no runtime dependency is pinned (§5.4, OI-02).

**OI-01, dependency licensing.** The guide replaced the earlier C-11 licence restriction with this policy (now PRD C-11):

- Permissive OSI-approved licences are allowed: MIT, BSD, Apache-2.0, ISC, PSF-2.0 and similar.
- Weak copyleft licences (LGPL and MPL-2.0) are allowed only as unmodified libraries.
- GPL and AGPL are not allowed.
- The policy applies equally to runtime, development and CI dependencies.
- Each dependency's licence must be recorded next to it, and the reviewer checks it.
- No separate exception record or per-package approval process is required.

**OI-02, runtime dependency management.** The guide decided:

- One root `requirements.txt` for runtime dependencies; the existing root `requirements-dev.txt` stays for development dependencies.
- Every dependency line uses an exact `==` version pin. These pinned files serve as the lock for now; no additional dependency-management tool is needed yet.
- Dependencies are declared centrally in the root requirements files, grouped by the library or module that needs them.
- Each dependency's licence is recorded in a comment beside its pinned version.
- CI will install the runtime and development requirements together.
- The Studio design document's reference to a lock file means the root `requirements.txt`.
- PyLTI1p3Next is added to `requirements.txt` only after this ADR is approved.

---

## 4. Candidate evaluation

### 4.1 PyLTI1p3Next — preferred candidate

Repository: <https://github.com/pymsglobal/pylti1p3next>

Static review details:

| Item | Observed value |
|---|---|
| Reviewed commit | `0595282` |
| Reviewed commit date | 22 August 2026 |
| Latest reviewed release | `2.0.2` |
| Release date | 2 June 2026 |
| Distribution package | `pylti1p3next` |
| Python import namespace | `pylti1p3` |
| Declared Python compatibility | Python 3.10 and later; Python 3.12 classifier present |
| Project licence | MIT |
| Framework adapters identified | Flask and Django |
| FastAPI adapter | None identified in the reviewed source |

Capabilities identified during static inspection:

- OpenID Connect login handling.
- JWT parsing and signature-validation flow.
- JWKS public-key retrieval.
- Registration and deployment lookup.
- State and nonce handling.
- LTI message validation.
- Launch-data storage abstractions.
- Framework cookie/session adapters.
- Type marker through `py.typed`.

**What is verified and what is not (Stage 1 evidence status):**

| Fact | Status |
|---|---|
| Source read at commit `0595282` (static review, nothing executed) | Verified by the B3 static review (§6, §18.3) |
| Release `2.0.2`, dated 2 June 2026; project licence MIT | Recorded from the review; the licence file at the commit was read (§18.3). Not re-checked against the published package |
| The reviewed commit (22 August 2026) is **later** than release `2.0.2` (2 June 2026) | Recorded; means the reviewed source may differ from the release that would be pinned. **Refined by the 17 November 2026 follow-up review below** |
| Full SHAs and tag relationship (17 November 2026, read from GitHub's REST API; nothing downloaded or executed) | Reviewed commit `0595282` resolves to `05952824b267c94699deae4b430e2c3a059cde2a` (22 August 2026, "Merge pull request #59 from pymsglobal/fix-black"). Tag `2.0.2` points to commit `aa9d756b2d4fe5848d179eb377b760ca481cde91`. GitHub's compare reports the reviewed commit as 12 commits ahead of tag `2.0.2` and 0 behind. The files changed between the two are `.github/workflows/test.yml`, `src/pylti1p3/deep_link.py`, `src/pylti1p3/deep_link_resource.py`, `src/pylti1p3/service_connector.py`, `test_reqs.txt` and test files. **None of the source areas in §18.3 that this ADR's findings rely on (`message_launch.py`, `oidc_login.py`, `session.py`, `launch_data_storage/`, `cookie.py`, `message_validators/`) and not `pyproject.toml` changed (`pyproject.toml` was compared and is unchanged).** Source: GitHub compare of `2.0.2...05952824b267c94699deae4b430e2c3a059cde2a` |
| PyPI metadata for `pylti1p3next` 2.0.2 (17 November 2026, from PyPI's JSON API) | Upload time 2 June 2026 (wheel and sdist). Declared requirements match §5 (`jwcrypto~=1.5`, `pyjwt>=1.5`, `requests~=2.32`, `typing_extensions~=4.2`). Python `>=3.10`. Published SHA-256: wheel `d496c2094be8edcf44f0c742198715eaea4d64fc89acc064e337e33a3b601821`, sdist `80f334e5e05aaa66e4ac4d8e9d729a3b01e16800680f323e769ba929dda09717`. These hashes are as published by PyPI; **this review did not download either file or recompute the hashes** |
| Which artefact would be pinned (PyPI release `2.0.2` or a Git commit) | **Not decided.** The evidence above shows that the reviewed security-relevant files are unchanged between tag `2.0.2` and the reviewed commit, which supports pinning release `2.0.2`. **Not verified:** that the PyPI wheel and sdist contents match tag `2.0.2` (this needs a download in a throwaway environment, V1, Appendix B). The choice and the check remain with the B3 owner and the guide |
| Resolved dependency tree and licences on Python 3.12 | **Not verified** (§5.3) |
| Security advisories for the tree (SEC-08) | **Not verified** |

The package distribution name differs from the import namespace. The original `pylti1p3` and PyLTI1p3Next both use the `pylti1p3` import namespace, so they should not be assumed to be safely installable side by side in one environment.

### 4.2 Original PyLTI1p3 — fallback candidate

Repository: <https://github.com/dmitry-viskov/pylti1p3>

The original project remains a possible fallback. **Guide-reported finding, pending independent verification:** the original repository's last observed push was in August 2024, while the preferred fork has more recent releases. This B3 review has not yet inspected the original repository.

Do not switch to the original project automatically. Reopen the library decision if PyLTI1p3Next cannot satisfy an essential requirement or its unresolved licence and maintenance risks cannot be accepted.

### 4.3 Why not implement LTI validation from scratch?

A custom implementation would make LearnOps responsible for protocol-sensitive behaviour, including:

- JWT signature and key validation.
- JWKS retrieval and key selection.
- OIDC state validation.
- Nonce replay prevention.
- Issuer, audience, and deployment validation.
- Expiry enforcement.
- LTI message-type validation.
- Launch-data storage and session isolation.

That would create additional security and maintenance work. The preferred approach is to use the candidate for protocol functionality and enforce LearnOps-specific policy through the adapter and tests.

### 4.4 Why not compare Authlib and joserfc now?

The guide explicitly recommended proceeding with PyLTI1p3Next and skipping the Authlib + joserfc comparison unless a specific gap cannot be closed.

A broader comparison is therefore not part of this decision's current scope. It may be reopened if a blocking gap is found.

---

## 5. Package and dependency assessment

The reviewed package metadata declares these runtime dependencies:

| Dependency | Observed requirement | Purpose |
|---|---|---|
| `jwcrypto` | `~=1.5` | Cryptographic and JWK functionality |
| `pyjwt` | `>=1.5` | JWT handling |
| `requests` | `~=2.32` | HTTP requests |
| `typing_extensions` | `~=4.2` | Typing compatibility |

The primary package is MIT-licensed. That does not establish that every dependency and transitive dependency is compatible with LearnOps policy.

### 5.1 Licence of `typing_extensions` (decided under the new policy)

**Source finding (independently verified for version 4.16.0):** PyLTI1p3Next declares `typing_extensions~=4.2` as a direct runtime dependency (`pyproject.toml:54`) and imports it at runtime (for example `message_launch.py:17`). The licence metadata for `typing_extensions` version 4.16.0 was independently inspected in the existing B2 Python virtual environment, without installing or modifying any dependency. Its package metadata declares `License-Expression: PSF-2.0` (`METADATA`, line 9), and its licence file is the Python Software Foundation License Version 2 (`licenses/LICENSE`, line 73). The version that would actually be resolved within `~=4.2` has not been verified; its licence must be checked when it is pinned.

The same package is already installed transitively by the repository's existing development and CI tools on Python 3.12, through `jsonschema` → `referencing` and through `mypy`.

**Policy:** under the earlier PRD C-11 wording, PSF-2.0 was not listed. The guide's new policy (§3.4) explicitly permits PSF-2.0, for runtime, development and CI dependencies alike, without a separate exception record. `typing_extensions` therefore needs no individual exception.

**Still required:** record the licence beside the exact pin when the dependency is added to `requirements.txt`, and the reviewer checks it (§3.4).

### 5.2 LGPL dependency: `jwcrypto` (disclosed for guide review under PRD C-11)

**Disclosure.** PyLTI1p3Next declares `jwcrypto~=1.5` as a direct runtime dependency (§5). If PyLTI1p3Next is adopted, `jwcrypto` becomes a runtime dependency of LearnOps. It is reported to be LGPL-3.0-or-later, a weak-copyleft licence. PRD C-11 permits LGPL "only as an unmodified library"; GPL and AGPL are not permitted. The guide is asked to review this explicitly as part of Stage 1 approval (Appendix A).

**Evidence status.** The licence is **guide-reported**. **Follow-up check, 17 November 2026:** PyPI's JSON API reports `jwcrypto` 1.6.1 (the latest release at that date) with `License-Expression` `LGPL-3.0-or-later`. This agrees with the guide's report. It is the **declared package metadata of one version** (1.6.1), not the version that would be pinned (`~=1.5` admits 1.5.x and 1.6.x), and **`jwcrypto`'s own licence file was not read**, so this is not Appendix C V2 evidence on Python 3.12. The licence is not confirmed for the pinned version, and the LGPL review under PRD C-11 is still the guide's. `jwcrypto` 1.6.1 declares `cryptography>=49.0.0` and `typing_extensions>=4.5.0` as dependencies (§5.3).

**Advisories for the `jwcrypto` range.** The GitHub advisory database lists (read 17 November 2026): CVE-2026-39373 (JWE ZIP decompression bomb, fixed in 1.5.7), CVE-2024-28102 (JWT bomb in `deserialize`, fixed in 1.5.6), CVE-2023-6681 (PBES2 count DoS, fixed in 1.5.1) and older ones. The `~=1.5` range admits releases before 1.5.7, so the floor must be set at pin time from the V3 scan (Appendix B). This ADR does not set it.

**Conditions if approved** (proposed, for the guide to confirm):

- `jwcrypto` is used unmodified, installed from its published distribution, and never vendored, patched or copied into the repository.
- Its exact version and licence go in the root `requirements.txt` as a comment beside the pin (§3.4).
- The licence is checked against the package's own metadata and licence file when it is pinned, and the result is recorded in Appendix C.

**If the licence is not acceptable or cannot be verified:** reopen the library decision (§15.4).

### 5.3 Full dependency-tree review

Before approval, verify the licence and security status of the complete resolved dependency tree, not just PyLTI1p3Next's direct dependencies.

Record the exact approved versions and licence evidence. Pin approved runtime dependencies with exact `==` pins in the root `requirements.txt`, with each licence in a comment beside its pin (§3.4). CI dependency scanning must satisfy SEC-08 and the release security checks.

**Known transitive dependency: `certifi`, through `requests`.**

- **Source finding:** PyLTI1p3Next declares `requests~=2.32` as a direct runtime dependency (`pyproject.toml:53`).
- **Independently verified, limited to the versions inspected:** the package metadata of the already-installed `requests` 2.34.2 declares `Requires-Dist: certifi>=2023.5.7` (`METADATA`, line 37), and the package metadata of the already-installed `certifi` 2026.5.20 declares `License: MPL-2.0` (`METADATA`, line 8), with its licence file carrying the Mozilla Public License 2.0 notice (`licenses/LICENSE`, lines 15–17). Nothing was installed or executed to obtain this.
- **Limitation:** these versions were inspected in the Python 3.14 user site-packages on the reviewer's machine, not in the project's Python 3.12 environment. The versions that would actually be resolved, and eventually pinned, for Python 3.12 have not been verified, and the exact Python 3.12 dependency tree has not been verified. Their licences must be checked and recorded when they are pinned.
- **Guide-reported, not independently verified:** the PR #60 commit message lists `certifi` (via `requests`) as MPL-2.0.
- **Policy:** under PRD C-11 (§3.1), MPL-2.0 is permitted only as an unmodified library. LearnOps must not modify `certifi`.

**Declared licences across the tree: PyPI metadata check, 17 November 2026.** Source: PyPI's JSON API, latest release of each package at that date. **The versions below are illustrative: they are the latest releases, not the versions that would resolve within the declared ranges (`~=1.5`, `>=1.5` and so on) or be pinned.** This is a first-pass read of **declared metadata only**. It is **not** the resolved Python 3.12 tree, no licence file was read, and nothing was installed. The tree listed in §5 was incomplete: it omitted the dependencies of `jwcrypto` and `requests`.

| Package (latest version checked) | Declared licence | Reached through |
|---|---|---|
| `pylti1p3next` 2.0.2 | MIT (licence text in package metadata) | direct |
| `jwcrypto` 1.6.1 | LGPL-3.0-or-later | direct (§5.2) |
| `pyjwt` 2.15.1 | MIT | direct |
| `requests` 2.34.2 | Apache-2.0 | direct |
| `typing_extensions` 4.16.0 | PSF-2.0 | direct, and `jwcrypto` |
| `cryptography` 50.0.2 | Apache-2.0 OR BSD-3-Clause | `jwcrypto` |
| `cffi` 2.1.1 | MIT-0 | `cryptography` (not on PyPy) |
| `pycparser` 3.12 | BSD-3-Clause | `cffi` (reported by PyPI as its licence; its place in `cffi`'s dependencies was not checked) |
| `urllib3` 2.8.0 | MIT | `requests` |
| `idna` 3.20 | BSD-3-Clause | `requests` |
| `charset-normalizer` 3.5.2 | MIT | `requests` |
| `certifi` 2026.10.23 | MPL-2.0 (§5.3 above) | `requests` |

Only `jwcrypto` (LGPL) and `certifi` (MPL-2.0) are weak copyleft; both must stay unmodified (PRD C-11). No GPL or AGPL licence appeared in this metadata. The versions that would resolve on Python 3.12, and the licence files, remain to be checked at pin time (V2).

### 5.4 Runtime dependency management (decided)

**Before the decision:** the reviewed B3 repository contained only `requirements-dev.txt` (development and CI dependencies) and no runtime dependency file.

**Guide decision (§3.4, OI-02):** runtime dependencies go in one root `requirements.txt`, alongside the existing `requirements-dev.txt`. Every line has an exact `==` pin and a licence comment, and dependencies are grouped by the library or module that needs them. These pinned files are the lock for now, and no additional tool is needed. CI will install both files together. The Studio design document's "lock file" means the root `requirements.txt`.

**Not yet done:** `requirements.txt` does not exist on this branch, and this ADR does not create it. PyLTI1p3Next and its dependencies are added to it only after this ADR is approved (§17.2).

---

## 6. Static source-review findings

The candidate was inspected through repository metadata, source files, and Git history. Third-party candidate code and tests were not installed or executed. Findings below refer to the reviewed commit and must be rechecked if the selected release or commit changes.

Evidence labels used in this section and in §7–§9:

- **Source finding:** read in the PyLTI1p3Next source at commit `0595282`. File references are relative to `src/pylti1p3/` unless stated otherwise.
- **Documented behaviour (not independently verified):** PyJWT behaviour and browser cookie rules taken from their documentation. PyJWT was not available locally and no code was run, so these are not source findings.
- **Proposed B3 design:** this ADR's recommendation, not an approved decision.
- **PRD requirement** and **guide decision:** as cited.

### 6.1 Validation sequence

The inspected `MessageLaunch.validate()` flow includes state, JWT-format, nonce, registration, signature, deployment, and message validation, followed by launch-data persistence.

Automatic validation is enabled by default.

**Proposed approach:** Retain the library's automatic validation. Do not disable it and replace it with a partial custom sequence. Add LearnOps-specific checks around the validated launch boundary.

The exact order and side effects of validation must be considered when implementing replay protection. In particular, invalid tokens should not be able to consume a legitimate user's nonce before signature validation has established the token's authenticity.

### 6.2 Expiry

The inspected implementation checks expiry if `exp` is present, but the review did not establish that the claim is mandatory.

**Source finding:** `validate_jwt_signature()` calls `jwt.decode(id_token, public_key, algorithms=[key_alg], options=self._jwt_verify_options)` (`message_launch.py:754–759`). The default options are `{"verify_aud": False}` (`message_launch.py:236`). No `audience`, `issuer`, `leeway`, or required-claims option is passed. The declared dependency is `pyjwt>=1.5` (`pyproject.toml:52`), which also admits PyJWT 1.x.

**Documented behaviour (not independently verified):** PyJWT rejects an expired `exp`, but accepts a token with no `exp` unless the claim is listed as required. PyJWT 1.x uses different option names from 2.x.

**Required behaviour from SEC-01 and the guide:** require `exp` and reject missing or expired values.

**Proposed B3 design:** enforce expiry inside the overridden `validate_jwt_signature()` (§6.9), so that it runs before any state or nonce is consumed and before anything is persisted. A check after `validate()` would be too late, because the library's `save_launch_data()` runs at the end of `validate()` (`message_launch.py:342`). Explicitly require and validate the relevant claims (proposed: `exp`, `iat`, `iss`, `aud`, `sub`, `nonce`), and pin a PyJWT 2.x release (OI-02).

**PyJWT advisory (checked 15 November 2026).** Source: the GitHub advisory record GHSA-75c5-xw7c-p5pm, read as data from GitHub's REST API (`gh api /advisories/GHSA-75c5-xw7c-p5pm`); the human-readable page is <https://github.com/advisories/GHSA-75c5-xw7c-p5pm>. The record gives: CVE-2024-53861; summary "PyJWT Issuer field partial matches allowed"; package `PyJWT` (pip); vulnerable range `= 2.10.0`; first patched version `2.10.1`; severity low (CVSS v4 score 2.1); published 2 December 2024. No other fact from the advisory is used here. It matters here because the §6.9 design passes `issuer` to `jwt.decode`.

**Follow-up check, 17 November 2026 (GitHub advisory database, `gh api 'advisories?ecosystem=pip&affects=pyjwt&per_page=100'`, re-run 17 November 2026; read as data):** the query returned 24 PyJWT advisories (an earlier run recorded 20 because of default paging; the highest first-patched version among them is 2.15.0, and the floor is left to the B3 owner and the guide at V3), most published in 2026, so CVE-2024-53861 is not the only one. Most are fixed in 2.14.0 or 2.15.0, one is rated critical for `<= 2.13.0` (GHSA-ffc3-869f-jxw9, asymmetric-PEM detection bypass), several are rated high, and GHSA-gvp8-978c-rx2q (CVE-2026-103001, range 2.11.0 to 2.13.0) is titled "options-dict mutation, silent claim-verification bypass on dict reuse" and records no patched version. The last one matters to this design: the library keeps one `_jwt_verify_options` dict and passes it to every `jwt.decode()` call (`message_launch.py:236`, `:754–759`, checked at the reviewed commit), and §6.9 relies on explicit options. At the reviewed commit, `message_launch.py` imports `jwt` and `jwcrypto.jwk.JWK` and does not mention `PyJWK` or `PyJWKClient`; other files were not searched, so which advisories actually apply to the library's code path is **not established**. **Not established:** whether the advisory list is complete or applies to the resolved version, and any general minimum version. The 17 November list does not settle the floor: the V3 scan of the resolved tree does (Appendix B). No PyJWT version is chosen here. The dependency floor is not set by this ADR: it is decided at pin time from the V3 advisory scan of the resolved tree (Appendix B), and it must also be a PyJWT version that PyLTI1p3Next works with, which has not been verified (it declares `pyjwt>=1.5`).

**Open until approved (OI-04):** the clock-skew leeway, any maximum token age based on `iat`, and the exact required-claim list.

### 6.3 Audience and authorized party

The inspected configuration defaults to `verify_aud: False`. The inspected `get_client_id()` returns the first value when `aud` is an array; the review did not find the required `azp` handling for multiple audience values.

**Source finding:** `get_client_id()` returns `aud[0]` when `aud` is a list (`message_launch.py:288–291`), and only that value is compared with the registration (`message_launch.py:740–743`). `azp` is not read anywhere in the inspected library.

**Documented behaviour (not independently verified):** with audience verification enabled but no `audience` argument, PyJWT rejects any token that carries `aud`. Setting the options through `set_jwt_verify_options()` alone therefore cannot enable correct audience checking.

**Required behaviour:** validate the expected client ID in `aud`; when multiple audience values are present, validate `azp` according to the OIDC requirement and the guide-approved rule. Reject invalid combinations.

**Proposed B3 design:** in the overridden `validate_jwt_signature()` (§6.9), pass the registered client ID as the expected audience (taken from the registration, not from `aud[0]`) and apply a LearnOps `azp` rule: when `aud` has more than one value, `azp` must be present and equal the client ID.

**Open until approved (OI-05):** whether an `azp` present alongside a single audience must also equal the client ID.

Do not rely on the inspected defaults to satisfy SEC-01.

### 6.4 Issuer and deployment

The library supports registration and deployment lookup.

LearnOps must verify that:

- `iss` matches the configured Moodle issuer.
- `deployment_id` matches the configured registration.
- Unknown or mismatched deployments are rejected.

### 6.5 LTI message type

The inspected library supports multiple LTI message types.

PRD B3 specifies `LtiResourceLinkRequest`, and Deep Linking is not required in v1.

The LearnOps boundary must reject other message types.

**Source finding:** the launch type definition lists `LtiResourceLinkRequest`, `LtiDeepLinkingRequest`, `DataPrivacyLaunchRequest`, and `LtiSubmissionReviewRequest` (`message_launch.py:142–146`), and `get_validators()` accepts all four (`message_validators/__init__.py:7–13`). The resource-link validator checks `sub`, `version == "1.3.0"`, the presence of a `roles` claim, and `resource_link.id` (`message_validators/resource_message.py:6–21`, `message_validators/abstract.py:16–25`). Nothing restricts the type by default.

**Proposed B3 design:** in an overridden `validate_message()` (§6.9), reject every type other than `LtiResourceLinkRequest` before calling the library validators. The check runs before any state or nonce is consumed and before anything is persisted or a session is created. Rejecting early is safe; acceptance is only meaningful after signature verification.

### 6.6 Public keys and JWKS caching

The inspected implementation retrieves keys through JWKS and selects them using `kid` and `alg`. The review observed that the code permits HTTP or HTTPS JWKS URLs and uses a default public-key cache lifetime of 7200 seconds.

LearnOps must:

- Require HTTPS for deployed Moodle and JWKS endpoints.
- Permit HTTP only for localhost development, as clarified by the guide.
- Validate signature and key selection.
- Document cache lifetime and key-rotation implications.
- Fail safely if a key cannot be verified.

The observed two-hour cache default is a library behaviour, not an independently approved LearnOps policy.

### 6.7 Nonce handling

The inspected `check_nonce()` path delegates to the configured storage. The reviewed session storage checks whether a nonce exists but does not demonstrate consuming it. The reviewed cache storage path also did not establish atomic single-use consumption.

**Source finding:**

- Login saves the nonce with the default 86400-second lifetime (`oidc_login.py:106–107`, `session.py:13`, `session.py:41–42`).
- `check_nonce()` only checks that the key exists and never deletes it (`session.py:44–46`; `launch_data_storage/cache.py:38–40`; `launch_data_storage/session.py`, `check_value`).
- The storage interface has no delete operation; it offers only `get_value`, `set_value`, `check_value`, and `can_set_keys_expiration` (`launch_data_storage/base.py:42–56`).
- `validate()` checks the nonce before the signature: state, JWT format, nonce, registration, signature, deployment, message, save (`message_launch.py:335–342`).

**Consequences:** a nonce is never consumed, so repeated and concurrent replays of the same token both pass the nonce check. If consumption were added at the library's current nonce step, a forged, unsigned token carrying a captured nonce could consume it before signature verification and block the legitimate launch.

**Required behaviour:** a successfully used nonce must not be accepted again. Concurrent replay attempts must not both succeed.

The storage operation must be atomic. The exact implementation and ordering relative to signature verification require an explicit design and test.

**Proposed B3 design:** keep the library's existence check as an early filter, and consume the nonce atomically only after signature and claim verification, together with the state (§6.8) and inside the launch transaction (§7.8).

### 6.8 State handling

**Source finding:**

- At login, state is `"state-" + uuid4` and is stored only as a five-minute cookie (`oidc_login.py:102–103`). It is stored server-side only when `pass_params_to_launch()` has been used (`oidc_login.py:108–109`, `oidc_login.py:197–202`, `session.py:48–49`).
- `validate_state()` first checks a server-side "state plus ID-token hash" record and falls back to comparing the state cookie only if that check fails (`message_launch.py:658–673`, `session.py:57–58`).
- After a successful launch, `save_launch_data()` writes that state and hash record (`message_launch.py:834`, `session.py:54–55`) with the default 86400-second lifetime (`session.py:13`, `session.py:30`).
- Nothing deletes state: the cookie interface offers only `get_cookie` and `set_cookie` (`cookie.py:9–17`), and the storage interface has no delete (`launch_data_storage/base.py:42–56`).

**Consequences:** state is not consumed. Within five minutes the cookie still matches; after a success, the same state and the same ID token pass through the stored hash for up to 24 hours, without the state cookie. Concurrent requests with the same state both pass. Combined with the unconsumed nonce (§6.7), a captured launch POST can be replayed.

A consumed nonce alone would stop replay of the same signed token, because the nonce is inside the token. State provides a separate guarantee, that the POST belongs to a login this browser started (CSRF protection), and the hash fallback weakens it.

**Proposed B3 design:**

- Make state browser-bound and server-side: always call `pass_params_to_launch()` so that login writes a server-side state record, keyed by the library's session ID (§8.7).
- In the overridden `validate_state()` (§6.9), require both the state cookie and the server-side record, and remove the ID-token-hash fallback.
- In the overridden `save_launch_data()` (§6.9), do not write the state and hash record, and delete the state cookie in the response.
- Consume state and nonce atomically, in one transaction, only after signature and claim verification (§7.8).

Retain state validation. Ensure OIDC login and message-launch validation use the same correctly configured storage so that state and nonce checks operate over the intended shared state.

**Open until approved (OI-03):** state, nonce, and login-record lifetimes.

### 6.9 Proposed extension points (subclassing)

**Source finding:** the per-step methods `validate_state`, `validate_jwt_format`, `validate_nonce`, `validate_registration`, `validate_jwt_signature`, `validate_deployment`, `validate_message`, and `save_launch_data` are public by name. The README documents only `get_launch_data`, `set_auto_validation().validate()`, `from_cache`, `get_launch_id`, `set_public_key_caching`, and the `launch_data_storage` argument (`README.rst:199`, `:208`, `:322`, `:330`, `:651`, `:597–635`). The per-step methods therefore carry no documented stability promise. Git history shows the `validate()` chain essentially unchanged since 2019; its last change (`8a00709`, 2024-07-05) concerned exception handling. That is evidence of stability, not a guarantee.

**Proposed B3 design:** subclass `MessageLaunch` in `libs/lti` and override four methods, without modifying third-party code:

| Override | Proposed responsibility |
|---|---|
| `validate_state` | Require the state cookie and the server-side state record; no ID-token-hash fallback (§6.8) |
| `validate_jwt_signature` | Decode with explicit audience, issuer, required claims, and leeway; apply the `azp` rule (§6.2, §6.3) |
| `validate_message` | Accept only `LtiResourceLinkRequest`, then run the library validators (§6.5) |
| `save_launch_data` | Within one transaction: consume state and nonce, apply claim and role decisions, persist normalized launch data only, and create the application session (§7.8); do not call the library's implementation, which saves the full JWT body and the state hash |

`validate_nonce` needs no override: its existence check is harmless once consumption moves to `save_launch_data`.

**Why not override `validate()`:** it would duplicate the library's eight-step chain (`message_launch.py:335–342`), and any step added upstream later would be silently skipped. This also follows §6.1: retain the library's automatic validation.

**Reliance on undocumented behaviour:** the design assumes that `save_launch_data()` is the last step and is only reached after every check (`message_launch.py:342`); that `_registration` is set before `validate_jwt_signature()` runs (`message_launch.py:724–737`, `:339`); and that the protected names `_get_id_token` and `_registration` keep their meaning. If a method were renamed upstream, its override would silently stop running; if a step were added after `save_launch_data()`, state and nonce would be consumed before that check; if the chain were reordered, signature verification could run before registration is set.

**Required safeguards (proposed):**

- Pin the exact PyLTI1p3Next version (OI-02).
- Startup compatibility checks that:
  - the four overridden methods (`validate_state`, `validate_jwt_signature`, `validate_message`, and `save_launch_data`) exist on the base `MessageLaunch` class;
  - `_get_id_token` remains available on the base class;
  - `_registration` remains declared in the base class's annotations, and is populated on the launch instance after `validate_registration()` executes.
  Fail at startup or in the validation-chain test if these compatibility expectations are not met.
- Validation-chain tests that record call order and assert that every override runs, with `save_launch_data` last.
- Behavioural security tests (§12) that fail if any override is bypassed.
- Review the upstream diff of `message_launch.py`, `oidc_login.py`, and `session.py` on every upgrade.

---

## 7. Launch-data storage and session security

### 7.1 Inspected defaults

The library's default launch-data storage uses framework request-session storage. The inspected implementation reads and writes values through the framework session and does not provide the server-side launch-data design required by the guide.

A signed client-side cookie may provide integrity, but it does not provide confidentiality. It is not an acceptable substitute for the required server-side storage.

The library also provides an optional cache-backed storage implementation. It supports expiry but must be explicitly configured.

**Source finding:**

- The library saves the whole JWT body as launch data (`message_launch.py:833`), which keeps more than SEC-06 permits.
- `from_cache(launch_id)` loads launch data by launch ID alone (`message_launch.py:294–324`).
- Storage keys get a per-browser session-ID prefix only when a session ID is set (`launch_data_storage/base.py:33–40`). The cache storage drops that prefix when the request is not secure (`launch_data_storage/cache.py:22–23`); its own docstring warns that anyone who knows a launch ID could then read the launch data (`launch_data_storage/cache.py:18`).
- `CacheDataStorage` stores values through whatever `_cache` object it is given, using `get` and `set` (`launch_data_storage/cache.py:9`, `:32`, `:36`).

### 7.2 Required server-side storage

Use server-side launch-data storage. Do not place sensitive launch data in a client-readable cookie.

Do not authorize access to launch data based solely on a launch ID. Every retrieval must be authorized through the authenticated server-side session and its identity binding.

The guide's clarified identity tuple is:

- `iss`
- `sub`
- Moodle context ID

The identity is `(iss, sub, context id)`, decided by the guide (OI-21), and PRD B3 is amended to match. The issuer is part of the identity so that identities from different Moodle issuers cannot collide.

**Proposed B3 design (not approved):**

- Persist normalized launch data only (the §10.1 fields), never the raw ID token or full JWT body. This replaces the library's `save_launch_data()` behaviour (§6.9).
- Implement one LearnOps `LaunchDataStorage` subclass backed by PostgreSQL, the only database in the fixed stack (PRD A10). It always requires a session ID (no unprefixed fallback), stores expiry timestamps, and adds an atomic consume operation for state and nonce.
- Keep two kinds of server-side record: short-lived login records (state and nonce, keyed by the library session ID) and application sessions with normalized launch data (keyed by an unguessable session ID, bound to the identity tuple above).
- Do not use `from_cache()` for authorization; downstream modules read the authenticated application session.

**Awaiting guide approval (OI-06, OI-07): storage ownership and migration responsibility.** Which PostgreSQL schema holds these tables, who owns the migrations (CLAUDE.md requires versioned, reversible ones), and the record lifetimes are not decided. This ADR does not assign them.

### 7.3 Shared storage for login and launch

The inspected `OIDCLogin` and `MessageLaunch` classes accept optional launch-data storage configuration. The same storage backend and compatible configuration must be supplied to both flows.

Different storage configurations can break state and nonce validation.

**Source finding:** both constructors accept an injected storage instance (`oidc_login.py:50`, `:92–93`; `message_launch.py:222`, `:250–251`). Login creates the library session-ID cookie if it is absent (`oidc_login.py:260–266`), and launch fails with "Missing cookie session-id" if it is not sent back (`message_launch.py:815–821`). Mismatched storage produces "Invalid Nonce." or "State not found" (`message_launch.py:707`, `:671`).

**Proposed B3 design:** one `libs/lti` factory builds the request, cookie, and storage adapters for both endpoints from a single configuration. Neither endpoint builds its own.

### 7.4 Storage expiry

The inspected library's default launch-data lifetime is 86400 seconds. The inspected session storage does not support per-key expiry through the library interface; cache storage supports expiry.

Do not inherit the library's 24-hour launch-data lifetime as the LearnOps application session policy. Select a server-side backend and expiry strategy that can enforce the approved two-hour idle policy.

The two-hour idle limit belongs to the application-session record, renewed by each authenticated request, and is independent of the lifetimes of state, nonce, and other login records. Those lifetimes are not yet set (OI-03, OI-07).

### 7.5 Two-hour idle session

The application session expires after two hours without an authenticated request. Every authenticated request, including upload-chunk requests, counts as activity.

After expiry, the user must relaunch the tool from Moodle.

Every authenticated request must also be authorized using the session's role and course context, as required by SEC-02.

### 7.6 Upload resume

An unfinished upload must be associated with stable user and course identity rather than a browser session ID. The same user in the same course must be able to resume an unfinished upload after relaunch, subject to the Video module's upload authorization.

The guide's clarified stable identity is `(iss, sub, context id)`. Communicate this requirement to the Video owner and agree how it is represented in the Video module's upload record.

### 7.7 Cross-session isolation

Acceptance tests must prove that:

- A launch ID from one authenticated session cannot be used to retrieve another session's launch data.
- A launch ID alone is insufficient to authorize retrieval.
- A session cannot access a different user's or course's launch data.
- Session expiry requires a new Moodle launch.

### 7.8 Launch transaction boundary

**Proposed B3 design (not approved):** after signature and claim verification, these steps must be transactionally consistent, in one PostgreSQL transaction:

1. Consume the state record and the nonce record; each must delete exactly one row.
2. Apply the claim decisions (for example, a missing `context.id`) and the role decision (§10.3).
3. Persist normalized launch data.
4. Create the application session bound to the identity tuple.

If the transaction fails, it rolls back completely: nothing is consumed and nothing is saved, and the user relaunches from Moodle. A launch that is refused by one of step 2's own decisions (no recognised role, Learner only, or a missing or invalid `context.id`) still commits the consumption of its state and nonce, so it cannot be retried. Nothing is consumed before signature verification, so a forged token cannot consume a legitimate user's state or nonce.

**Consumption boundary (proposed, not approved; §17.1a).** Everything that runs before `save_launch_data()` consumes nothing, and the launch may be retried: the state, JWT-format, nonce-existence and registration checks (an unknown `iss` fails here), the signature checks (including `exp`, `aud`, `azp` and `iss`), the deployment check, the message-type check, and the library's message validators. Those validators check certain claims, so a missing one of those claims is rejected before consumption; at the reviewed commit they are `sub`, the `roles` claim, `resource_link.id` and the LTI version claim (§6.5). Only the decisions inside the transaction (step 2 above) consume state and nonce when they refuse. Which claims the library checks before `save_launch_data()` depends on the pinned version and is confirmed by the startup and validation-chain tests (V4, LTI-29, LTI-30).

---

## 8. Cookies, CSRF, HTTPS, and reverse proxies

PRD SEC-09 requires CSRF protection on state-changing requests and secure, same-site cookies. The guide clarified the baseline cookie policy:

| Cookie | SameSite | Secure | HttpOnly | Behaviour |
|---|---|---|---|---|
| OIDC state cookie | `None` | Yes | Yes | Short-lived; delete after launch |
| Tool session cookie | `Lax` | Yes | Yes | Two-hour idle session |

### 8.1 OIDC state cookie

Use `SameSite=None; Secure; HttpOnly`, a short lifetime, and delete it after the launch completes.

### 8.2 Tool session cookie

Use `SameSite=Lax; Secure; HttpOnly`. Enforce the two-hour idle timeout server-side.

### 8.3 New-window launch baseline

Baseline tools open in a new browser window. Embedded launch is not part of the current baseline. If embedded launch is introduced later, revisit cookie, CSRF, and browser behaviour rather than assuming the baseline policy will remain sufficient.

### 8.4 HTTPS

HTTPS is mandatory for all deployed launches, including the lab. HTTP is permitted only for localhost development.

Do not interpret the library's ability to accept HTTP URLs as permission to use HTTP in deployed environments.

### 8.5 Reverse-proxy trust

Trust forwarded-protocol headers only from explicitly configured trusted proxies. Do not blindly trust client-supplied forwarded headers to determine whether a request is secure.

The guide owns provision of the lab certificate. The application deployment must have an explicit trusted-proxy configuration.

### 8.6 CSRF

Cookie attributes do not replace CSRF protection. State-changing application requests must have the CSRF protection required by SEC-09. The exact mechanism must be compatible with the new-window launch baseline and approved session design.

**Awaiting guide approval (OI-20): the CSRF mechanism is not decided.** This ADR proposes none. It must be chosen before any state-changing endpoint is built.

### 8.7 Library session-ID cookie (requires guide approval)

The candidate's cache storage needs a third cookie that the guide's cookie policy above does not cover. **Awaiting guide approval (OI-24): whether and how to handle this cookie, and its lifecycle. Nothing below about it is decided.**

**Source finding:**

- **Purpose:** it gives each browser its own section of the launch-data storage; every storage key is prefixed with its value (`launch_data_storage/base.py:33–40`). The README describes it as the library's own LTI 1.3 session ID cookie for use with the cache storage (`README.rst:582–586`).
- **Required:** by the cache storage on secure requests (`launch_data_storage/cache.py:22–24`). Launch fails with "Missing cookie session-id" if it is not sent (`message_launch.py:815–821`). The framework-session storage does not use it (`launch_data_storage/session.py:9–10`).
  - **Proposed B3 design:** the LearnOps PostgreSQL storage will always require this cookie's session ID, regardless of the underlying storage implementation; it will not permit unprefixed storage keys.
- **Created and read:** created at login with a random `uuid4` value if absent (`oidc_login.py:260–266`, `:78–79`); read at launch (`message_launch.py:817`).
- **Name:** `session-id` (`launch_data_storage/base.py:12`) with the adapters' `lti1p3` prefix (`cookie.py:7`, `contrib/flask/cookie.py:12–13`), giving `lti1p3-session-id`.
- **Attributes in the Flask reference adapter:** no expiry passed, so it lasts until the browser closes (`oidc_login.py:265`, `contrib/flask/cookie.py:26`); path `/` (`:28`); no domain, so host-only; `HttpOnly` always (`:29`); `Secure` (`:27`) and `SameSite=None; Partitioned` (`:32–34`) only when the request is secure.

**Documented behaviour (not independently verified):** the launch is a cross-site form POST from Moodle, and browsers do not send `SameSite=Lax` cookies on cross-site POSTs. The cookie therefore needs `SameSite=None`, which in turn requires `Secure`; `HttpOnly` is appropriate because no script needs it.

**Why existing cookies cannot replace it:** the tool session cookie (`SameSite=Lax`) is not sent on the cross-site POST and does not exist at login. The OIDC state cookie has a different name for each login, and the storage needs its session ID before state is generated (`oidc_login.py:92–93` runs before `:102`).

| Cookie | SameSite | Secure | HttpOnly | Behaviour | Status |
|---|---|---|---|---|---|
| OIDC state cookie | `None` | Yes | Yes | Short-lived; delete after launch | Guide decision (§8, [Issue #58](https://github.com/narenccode/learnops/issues/58)) |
| Tool session cookie | `Lax` | Yes | Yes | Two-hour idle session | Guide decision (§8, [Issue #58](https://github.com/narenccode/learnops/issues/58)) |
| Library session-ID cookie `lti1p3-session-id` | `None` (proposed) | Yes (proposed) | Yes (proposed) | Proposed: short-lived, deleted after launch, never reused as the application session | **Requires guide approval (OI-24)** |

**Proposed B3 design:** the LearnOps FastAPI cookie adapter sets these attributes; the attributes and lifetime are configurable without modifying the library, because the cookie adapter is LearnOps code (it implements `cookie.py:9–17`) and the storage subclass can rename the cookie (`launch_data_storage/base.py:21–22`). The application session always gets a new session ID, which also prevents session fixation through this cookie. The lifetime is not yet set.

---

## 9. FastAPI integration

The reviewed candidate includes Flask and Django adapters; no FastAPI adapter was identified.

LearnOps uses FastAPI. The proposed approach is a thin FastAPI integration layer in `libs/lti`, not the introduction of another web framework.

The adapter is expected to:

- Receive OIDC login and launch requests.
- Provide the request and session context required by the library.
- Load approved Moodle registration and deployment configuration.
- Configure the approved shared server-side storage.
- Retain the library's automatic validation, extended only through the four proposed overrides and safeguards in §6.9.
- Set cookie attributes for the OIDC state, library session-ID, and tool session cookies (§8, §8.7).
- Enforce LearnOps-specific claim and message-type requirements.
- Convert validated launch data into the normalized contract.
- Establish the authenticated application session.
- Return the approved refusal responses.

The inspected library uses synchronous `requests` calls. An asynchronous FastAPI handler must not block the event loop. The implementation should use an appropriate synchronous endpoint or a thread-pool strategy, subject to review.

This section records the proposed integration boundary; it does not authorize implementation.

---

## 10. Normalized launch contract and role mapping

### 10.1 Contract boundary

The library must expose a validated, normalized result to downstream modules. Modules must not parse raw ID tokens or independently interpret Moodle role claims.

Contract locations:

The guide confirmed in [Issue #58](https://github.com/narenccode/learnops/issues/58) (8 November 2026) that the B3 contract follows the same pattern as B4 and B7: Markdown documentation, a JSON Schema, and examples. This satisfies PRD §B.0, which requires a schema and at least one valid example.

| Item | Path | Status |
|---|---|---|
| Contract document | `contracts/lti-launch.v1.md` | Created in this change; listed in `contracts/CLAUDE.md` |
| JSON Schema (Draft 2020-12) | `contracts/lti-launch.v1.schema.json` | Created in this change; listed in `contracts/CLAUDE.md` |
| Valid examples | `contracts/examples/lti-launch.v1/` | Created in this change; valid examples only |

The contract is a draft until approved under PRD §B.0 rule 3. Before the Release 0 freeze, one owner of an affected module must approve the contract change. The guide approves the PRD text changed by this PR and reviews the complete contract set at the Release 0 gate. After the freeze, guide approval is also required for contract changes. The schema describes the normalised launch result, not the raw Moodle claims.

The normalized output contains:

| Field | Requirement |
|---|---|
| `iss` | Required |
| `sub` | Required |
| `deployment_id` | Required |
| `message_type` | Required; only `LtiResourceLinkRequest` |
| `role` | Required; `mentor` or `administrator` |
| `context.id` | Required; a positive integer written as a string (contract §3.1) |
| `context.title` | Optional |
| `resource_link.id` | Required |
| `name` | Optional, nullable |
| `email` | Optional, nullable |

**Corrections to the earlier draft of this table:** it listed a flat `resource_link_id`; the contract uses the nested `resource_link.id` (as instructed for this change, and consistent with the LTI claim). It also listed `learner` as a role value and omitted `message_type`.

`learner` is **not** a `role` value in the v1 schema. Baseline Learner launches are refused before a baseline session exists (PRD §B3, EXT-07), so the schema constrains `role` to `mentor` or `administrator`. Release 6 player access is a separate scope (§10.4); admitting `learner` later would widen the enum and is flagged for the guide as OI-25.

`name` and `email` are optional in incoming claims; absent values normalize to `null`. `context.title` is optional. Unknown claims are ignored. Unknown fields in the normalised result are allowed (PRD EXT-02).

Required incoming launch claims include `iss`, `sub`, `deployment_id`, `resource_link.id`, `context.id`, and at least one recognized role.

A missing `context.id`, or one that is not a positive integer in ASCII digits (contract §3.1), must be refused with guidance to open the tool from a course.

Signature, nonce, and expiry validation are responsibilities of `libs/lti` and its tests, not JSON Schema validation.

### 10.2 Moodle role URIs

The guide supplied these role identifiers:

- Instructor: `http://purl.imsglobal.org/vocab/lis/v2/membership#Instructor`
- Learner: `http://purl.imsglobal.org/vocab/lis/v2/membership#Learner`
- Institution administrator: `http://purl.imsglobal.org/vocab/lis/v2/institution/person#Administrator`
- System administrator: `http://purl.imsglobal.org/vocab/lis/v2/system/person#Administrator`

The guide's role URI observations are based on Moodle source; lab launch confirmation remains pending.

**Matching is exact (guide decision).** Only the URIs listed above count, compared as received. The short name `Instructor`, the `TeachingAssistant` sub-role (`…/membership/Instructor#TeachingAssistant`) and any alias, prefix, case or scheme variant are unlisted URIs, so they are ignored (contract §5). There is no alias or prefix matching.

**`mod/lti:admin` on the lab sites (OI-16, guide decision).** The capability `mod/lti:admin` must not be granted to anyone who is not a site administrator on the lab Moodle sites. The source observation in §10.3 (Moodle site administrators send the Instructor, institution administrator and system administrator URIs) remains **unverified** until the lab check below. The mapping does not depend on it: the institution administrator URI becomes `administrator`, and the system administrator URI is ignored.

#### 10.2a Lab verification checklist (OI-16, Appendix B V7): **PENDING**

**Not run.** No lab launch has been made for this checklist, and nothing in it is an observed result. Run it once on each lab site (Moodle 4.5 and 5.3) with test accounts only. Record only the role URIs from the `roles` claim; never record the ID token, the nonce, names, email addresses or any other claim. The results go in the release harness report (PRD E2), as Appendix B requires for V7.

| Persona | Account setup | `roles` claim sent, Moodle 4.5 | `roles` claim sent, Moodle 5.3 | Result under contract §5 | Status |
|---|---|---|---|---|---|
| a. Site administrator | A Moodle site administrator | PENDING | PENDING | PENDING (the unverified source observation predicts `administrator`) | Pending |
| b. Institution administrator | A user meant to act as an institution administrator; on the lab sites this account is not given `mod/lti:admin` unless it is a site administrator | PENDING | PENDING | PENDING | Pending |
| c. Instructor | A user enrolled in the course with the teacher role | PENDING | PENDING | PENDING | Pending |
| d. Learner | A user enrolled in the course with the student role | PENDING | PENDING | PENDING (a Learner-only launch is refused, EXT-07) | Pending |

Also record, for each site: the Moodle version and build, the date, who ran the check, and that no account other than a site administrator holds `mod/lti:admin`.

### 10.3 Role mapping

> **OI-22 is decided.** The guide decided that unlisted role URIs are ignored and a launch is refused only if no recognised role remains. PRD §A5 is amended in this change to say so, so the earlier conflict between the PRD wording and the guide's interpretation no longer exists. The two paragraphs and the table below are kept as the record of that conflict and its outcome.

**Earlier PRD wording (now amended).** PRD §A5 said: "a launch with any role not listed is refused with a clear message." Read literally, a launch containing **any** role URI outside the §B3 list would be refused, even if it also contained a listed role.

**Guide's decision.** Final: the guide's comment of 12 November 2026, Q2, [issuecomment-6826722256](https://github.com/narenccode/learnops/issues/58#issuecomment-6826722256) ("that is the authoritative behaviour, including for site administrators: ignore roles that B3 does not list, and refuse only when no recognised role remains"). Earlier, the 8 November comment, point 3, [issuecomment-6721370757](https://github.com/narenccode/learnops/issues/58#issuecomment-6721370757), set out the same reading and the Moodle role URIs. Moodle site administrators send Instructor, institution administrator, and system administrator URIs. Use the institution administrator URI as the Administrator marker and ignore the system administrator URI. Unlisted role URIs are ignored, and a launch is refused only if no recognized role remains.

The guide's interpretation applies these rules:

1. Collect all incoming role URIs.
2. Map recognized role URIs and ignore unlisted URIs.
3. Administrator takes precedence over Instructor.
4. Instructor maps to Mentor.
5. If no recognized role remains, refuse.
6. If the only recognized role is Learner, refuse for baseline tools.

**Combinations with an unlisted role URI (OI-22, decided):**

| Incoming role set | Earlier literal PRD reading | Decided result | Status |
|---|---|---|---|
| Unknown role only | Refuse | Refuse | Unchanged |
| Instructor + unknown role | Refuse (an unlisted role is present) | `mentor` (unknown role ignored) | Decided by the guide |
| Institution administrator + `…/system/person#Administrator` | Refuse (the system administrator URI is not listed) | `administrator` (system administrator URI ignored) | Decided by the guide |

The third row mattered most: if Moodle site administrators always send the system administrator URI, the literal reading would have refused every site-administrator launch. What Moodle actually sends is still to be confirmed in a lab launch (OI-16, Appendix B).

**Single roles and listed-role combinations:**

The PRD lists individual role mappings but does not define precedence for every combination; in [Issue #58](https://github.com/narenccode/learnops/issues/58), the guide clarified that Administrator takes precedence over Instructor (rule 3). A launch is refused for Learner only when Learner is the only recognized role (rule 6). Therefore, Instructor + Learner results in Mentor. This is a stated outcome, not a separately specified Instructor-over-Learner precedence rule.

| Incoming role set | Normalized result | Status |
|---|---|---|
| Instructor | Mentor | Agrees with PRD |
| Learner only | Refuse | Agrees with PRD |
| Institution administrator | Administrator | Agrees with PRD |
| Instructor + Learner | Mentor | Follows from guide rule 6 |
| Administrator + Instructor | Administrator | Guide-confirmed (Issue #58) |
| Administrator + Learner | Administrator | Guide-confirmed (Issue #58) |
| Unknown role only | Refuse | Agrees with PRD |
| No recognized role | Refuse | Agrees with PRD |

The guide clarified that Moodle's non-editing teacher, teacher, and manager roles arrive as Instructor for this integration and therefore map to Mentor in v1.

Moodle normally does not grant guests `mod/lti:view`, but a site can change that permission. If a guest launch reaches LearnOps as Learner, it is refused.

The five browser roles in PRD FR-C-06 are not the LTI role URIs and must not be confused with this mapping.

### 10.4 Release 6

**The current v1 normalized schema accepts only `mentor` and `administrator`.** It does not include `learner`. Baseline Learner-only launches are refused before a baseline session is created, so no normalized result with a Learner role exists in v1.

**Release 6 Learner support is unresolved (OI-25).** This ADR does not claim that the Release 6 player can accept Learner without a contract or schema change. Whether `learner` is admitted to the `role` enum, how, and when, is for the guide to decide. Until then:

- The v1 enum is not widened.
- Each tool still declares its accepted roles (§3.2); baseline tools accept Mentor and Administrator. A per-tool declaration cannot let a Learner through while the gateway refuses Learner-only launches and the schema has no Learner value.
- Learner must not become enabled globally.

Any future change to the normalized result must follow PRD §B.0 and its compatibility rules: after Release 0, additive and optional changes only; a breaking change needs a `v2` file; and the schema, examples, PRD text and every affected module's tests change in one pull request, with approvals required under PRD §B.0 rule 3. Whether adding an enum value counts as additive is part of OI-25.

---

## 11. Refusal behaviour and messages

### 11.1 Role refusal

For Learner-only, unknown-role-only, or no-recognized-role launches, the guide specified:

**HTTP 403**

> This tool is not available in this version. Use your course in Moodle.

Internal reason codes may include:

- `role_learner`
- `role_none`

### 11.2 Authentication and validation failure

For failed signature, nonce, expiry, or deployment validation, use:

> Your Moodle sign-in could not be verified. Open the tool again from your course.

### 11.3 Missing course context

If `context.id` is missing, or is not a positive integer in ASCII digits (contract §3.1), refuse the launch and explain that the user must open the tool from a course.

### 11.4 Centralized messages and logs

User-facing messages must follow PRD UI-05 and UI-07:

- UI-07 requires all user-facing strings to be kept in one place per module.
- UI-05 requires error messages in plain English that say what happened and what the user should do next.

User-facing messages must not expose sensitive validation details.

Logs must follow the repository's structured logging rules. Never log raw ID tokens, secrets, or sensitive authentication material. Use internal reason codes where appropriate.

---

## 12. Security acceptance tests

SEC-01, SEC-02, and SEC-09 are the principal PRD security references for the launch boundary. The following tests turn those requirements and the guide's clarifications into observable acceptance behaviour.

Each security requirement should have a failing test before its corresponding implementation is added.

**Every row below is a proposed Stage 2 acceptance test. None is approved** (§17.1a), and none exists yet, because `libs/lti` does not exist. Rows that depend on state and nonce use the consumption boundary in §7.8: a failure before `save_launch_data()` consumes nothing (LTI-01 to LTI-08, LTI-10, LTI-32); a refusal by the transaction's own decisions consumes them (LTI-11 to LTI-14, LTI-28); a failure of the transaction itself rolls everything back (LTI-27).

| Test ID | Requirement | Expected behaviour |
|---|---|---|
| LTI-01 | Invalid signature | Reject launch |
| LTI-02 | Missing `exp` | Reject launch |
| LTI-03 | Expired token | Reject launch |
| LTI-04 | Invalid or missing expected audience | Reject launch |
| LTI-05 | Multiple audiences with invalid or missing required `azp` | Reject launch |
| LTI-06 | Incorrect issuer | Reject launch |
| LTI-07 | Incorrect deployment ID | Reject launch |
| LTI-08 | Unsupported LTI message type | Reject launch |
| LTI-09 | Reused nonce | Reject launch |
| LTI-10 | Missing required launch claim that the library's validators check before `save_launch_data()` (at the reviewed commit: `sub`, the `roles` claim, `resource_link.id`, the LTI version claim; to be confirmed for the pinned version) | Reject launch; state and nonce stay unconsumed (as LTI-32) |
| LTI-11 | Learner-only role | HTTP 403; refused inside the launch transaction, so state and nonce are consumed (LTI-28) |
| LTI-12 | Unknown role only | HTTP 403; as LTI-11 |
| LTI-13 | No recognized role | HTTP 403; as LTI-11 |
| LTI-14 | Missing course context, or a `context.id` that is not a positive integer (zero, negative, non-numeric, leading zero, padded, non-ASCII digits, newline) | Refuse launch; refused inside the launch transaction, so state and nonce are consumed (LTI-28) |
| LTI-15 | Cross-session launch-data access | Reject access |
| LTI-16 | Launch-data access using launch ID alone | Reject access |
| LTI-17 | Expired application session | Require Moodle relaunch |
| LTI-18 | Untrusted forwarded-protocol header | Must not establish a secure request |
| LTI-19 | HTTP deployed endpoint outside localhost development | Reject configuration or launch |
| LTI-20 | Concurrent nonce replay | At most one validation succeeds |
| LTI-21 | State mismatch or state reuse | Reject login/launch |
| LTI-22 | State-changing request without valid CSRF protection | Reject request |
| LTI-23 | Request to a different course context | Reject access for Mentor; Administrator access follows the all-courses policy in PRD A5 |
| LTI-24 | Same state and same ID token posted again without the state cookie (the library's ID-token-hash path) | Reject launch |
| LTI-25 | Invalid signature carrying a legitimate state and nonce | Reject launch; the stored state and nonce records are still present and unconsumed (asserted on the stored rows, not only on the HTTP result); the legitimate launch still succeeds afterwards |
| LTI-26 | Missing library session-ID cookie at launch | Reject launch |
| LTI-27 | Failure inside the launch transaction | Roll back: nothing consumed, nothing saved |
| LTI-28 | Launch refused by LearnOps' own decision inside the launch transaction (§7.8 step 2): no recognised role or Learner only (LTI-11 to LTI-13), or a missing or invalid `context.id` (LTI-14); then retried | Retry rejected: state and nonce were consumed (asserted on the stored rows). Does not apply to failures before `save_launch_data()` (LTI-01 to LTI-08, LTI-10), which consume nothing (LTI-32) |
| LTI-29 | Validation-chain test | Every override in §6.9 runs, with `save_launch_data` last |
| LTI-30 | Base-class extension point missing (renamed upstream) | Startup compatibility check rejects an incompatible library version |
| LTI-31 | Stored launch data | Normalized fields only; no ID token or full JWT body |
| LTI-32 | Each failure covered by LTI-01 to LTI-08 and LTI-10 (signature, `exp`, audience, `azp`, issuer, deployment, message type, a claim the library's validators check) | Reject launch; the stored state and nonce records are unchanged and unconsumed (asserted on the stored rows). This does not change LTI-28 (a refusal by the transaction's own role or `context.id` decision still consumes them) or LTI-27 (a transaction failure rolls back) |

Final test names and file locations must follow repository conventions. Do not claim a test passes until it has actually been run and its output reviewed.

---

## 13. B4 course mapping and shared data

The guide clarified that Moodle's LTI context ID represents the Moodle course ID, supplied in Moodle source as:

`'context_id' => $course->id`

The combination of issuer and context ID identifies a course across Moodle platform registrations.

B4 should use `core_course_get_courses_by_field` with `field=id`.

The first successful launch should:

1. Confirm that the Moodle course exists.
2. Retrieve the course shortname for display.
3. Write the corresponding `shared.course_link` record.

The service-account visibility requirement remains a lab check.

**Decided by the guide:** `shared.course_link` is keyed by issuer (`iss`) plus context ID. B4 (Student 3) owns the columns and agrees them; B3 documents the key only and does not invent a schema or columns (OI-15).

**`context.id` at the B4 boundary (guide decision).** B3 hands `context.id` to modules as a decimal string: a positive integer in ASCII digits with no leading zero, and no upper bound or maximum length (contract §3.1; the schema is unchanged). B4 owns the form sent to Moodle and may pass the decimal string unchanged. A value that Moodle rejects must fail closed at the B4 call. B3 sets no numeric-conversion rule.

**B4 integration rule (confirmed by the B4 owner).** Harshitha, the B4 owner, has confirmed to the B3 owner that: `iss` must identify a registered platform; the platform configuration is resolved using the verified `iss`; B4 is called only through the client bound to the configuration that corresponds to the registered issuer; and there is never a fallback to another platform's configuration. No link to the confirmation is recorded here. The rule is written into the contract as §7.1.

**Added by B3 in the same section, not part of that confirmation:** the issuer is compared exactly (no trimming, case folding or trailing-slash normalisation), unknown issuers are refused, and the `iss` of an unverified token is used only to locate the candidate registered-platform configuration for signature verification; it is trusted only after the signature verifies. These need the reviewers' agreement with the rest of the contract.

**Approved by the guide (OI-15):** the gateway is approved as a consumer of B4 (guide decision, recorded 18 November 2026; source link to be added). The course-link identity key stays `(iss, context.id)`. **This approval does not approve or freeze the `shared.course_link` columns:** B4 owns them, and their approval is separate. B4 pull request #27 is merged; the columns are to be recorded in B4's follow-up #72, or in a decision record, once B4 agrees them. They are **not finalised**.

---

## 14. Downstream module implications

### 14.1 Studio and Checker

These modules consume the normalized launch contract and must enforce their declared accepted roles and course context. They must not independently parse or trust raw launch tokens.

### 14.2 Grading and B4

The launch supplies the course context. B4 resolves the Moodle course and maintains the shared course-link mapping. The gateway is approved as a B4 consumer (OI-15, §13). The B4 owner still has to agree and record the `shared.course_link` columns, which B4 owns, and confirm service-account visibility (OI-17).

### 14.3 Video

The Video owner must use stable user-and-course identity for unfinished upload records so an authenticated user can relaunch and resume an unfinished upload after session expiry. The guide's clarified identity is `(iss, sub, context id)`, not a browser session ID.

### 14.4 Release 6 player

Release 6 Learner support is unresolved (OI-25). The current v1 normalized schema accepts only `mentor` and `administrator`, and baseline Learner-only launches are refused (§10.4). Whether the player can accept Learner without a contract or schema change depends on the guide's decision on OI-25; any change follows PRD §B.0. Whatever is decided, Learner must not be enabled for baseline tools.

---

## 15. Maintenance, security, and supply-chain risks

### 15.1 Limited maintainer base

PyLTI1p3Next is a fork with a limited maintainer base. This creates maintenance and supply-chain risk.

Mitigations:

- Pin the approved release and record the reviewed commit.
- Keep the dependency behind `libs/lti`.
- Avoid exposing library-specific classes to downstream modules.
- Review future releases and dependency changes before upgrading.
- Keep the original PyLTI1p3 project documented as a possible fallback.

### 15.2 Dependency risk

Verify the complete dependency tree for licence compatibility and security advisories. Pin approved versions and scan dependencies in CI as required by SEC-08.

### 15.3 Unsafe defaults

Do not rely blindly on library defaults for expiry, audience, nonce replay prevention, state consumption, launch-data storage, HTTPS, or message-type restrictions. The adapter and acceptance tests must establish the LearnOps behaviour.

### 15.4 Fallback decision

If PyLTI1p3Next cannot satisfy an essential requirement or its dependency-policy issue cannot be resolved, reopen the library decision. Evaluate the original PyLTI1p3 or another candidate through a new documented review. Do not silently switch libraries or build a custom protocol implementation.

### 15.5 Extension-point risk

The proposed overrides (§6.9) rely on undocumented per-step methods and protected names. A future release could silently bypass an override or reorder the chain. The safeguards in §6.9 (exact version pin, startup compatibility checks, validation-chain tests, behavioural security tests, and upstream diff review on upgrades) must be in place before the adapter is accepted.

- Verify that `_registration` remains declared in the base class annotations and is populated on the launch instance after `validate_registration()`. Do not check it using `hasattr(MessageLaunch, "_registration")`, because it is an instance attribute populated during validation.

---

## 16. Outstanding items for guide and owner review

**The items below are unresolved. They are not approved implementation decisions.** The guide and affected owners must resolve them before the dependent work proceeds.

| ID | Outstanding item | Why it matters | Decision or confirmation needed | Priority |
|---|---|---|---|---|
| OI-01 | `typing_extensions` is PSF-2.0 licensed (verified for 4.16.0, §5.1), which the earlier C-11 wording did not list | Dependency licences must comply with policy | **Decided by the guide (§3.4):** new licence policy permits PSF-2.0 for all dependency types; no exception record needed. Policy documented in PRD C-11 and root `CLAUDE.md` by PR #60 (`f8f6e35`). Remaining: B3 records each licence beside its pin in `requirements.txt` (not yet created), checked by the reviewer | Decided; policy documented (PR #60); licence recording pending |
| OI-02 | Runtime dependency management convention was undefined | `requirements-dev.txt` existed, but no runtime dependency location | **Decided by the guide (§3.4):** root `requirements.txt` with exact `==` pins and licence comments, grouped by library or module; CI installs it with `requirements-dev.txt`. Remaining: add PyLTI1p3Next only after this ADR is approved | Decided; implementation pending |
| OI-03 | Neither nonce nor OIDC state is consumed by the inspected library, and the state/ID-token-hash record allows reuse (§6.7, §6.8) | Replay protection is required; a captured launch POST can currently be replayed | Guide/B3: approve browser-bound server-side state, removal of the hash fallback, atomic consumption of state and nonce after signature and claim verification, the launch transaction boundary (§7.8), and the state, nonce, and login-record lifetimes | **Blocking security design** |
| OI-04 | `exp` is not shown as mandatory by the inspected default (see §6.2) | SEC-01 requires expiry validation | Guide/B3: confirm mandatory expiry enforcement in the overridden signature step, the required-claim list, the clock-skew leeway, and any maximum token age | **Blocking security design** |
| OI-05 | Audience verification defaults to disabled; required `azp` handling was not identified | SEC-01 requires audience validation | Guide/B3: confirm strict `aud` against the registered client ID, `azp` required and matching when there are multiple audiences, and whether a present `azp` must match when there is a single audience | **Blocking security design** |
| OI-06 | Default launch-data storage is framework-session based, and the library saves the full JWT body | Does not meet the guide's server-side storage requirement or SEC-06 | Guide/B3: approve server-side storage of normalized launch data only, PostgreSQL-backed (proposed, §7.2), and the schema and migration ownership | **Blocking security design** |
| OI-07 | Cache storage is optional and requires explicit configuration | Incorrect configuration could expose launch data or break isolation | B3/guide: confirm backend, expiry, and configuration, including the record lifetimes | **Blocking security design** |
| OI-08 | OIDC login and message launch must share storage | Different storage configurations can break state and nonce validation | B3: specify one shared storage configuration through one `libs/lti` factory (§7.3) | **Blocking security design** |
| OI-09 | Library accepts multiple LTI message types | B3 v1 requires `LtiResourceLinkRequest` only | B3/guide: confirm enforcement in an overridden `validate_message()` before consumption and persistence (§6.5), and its tests | **Blocking security design** |
| OI-10 | JWKS cache defaults to 7200 seconds | Cache duration affects key-rotation behaviour | Guide/B3: confirm acceptable cache policy and document rotation behaviour | High |
| OI-11 | Library permits HTTP and HTTPS JWKS URLs | Deployed launches require HTTPS | Guide/B3: confirm HTTPS enforcement and localhost-only exception | **Blocking deployment security** |
| OI-12 | No FastAPI adapter was identified | LearnOps uses FastAPI | Guide: approve thin adapter and sync/thread-pool integration approach, including the four proposed `MessageLaunch` overrides and their safeguards (§6.9, §15.5) | High |
| OI-13 | Trusted-proxy configuration is not established by current setup documentation | Untrusted forwarded headers can undermine secure-request detection | Guide: confirm trusted proxy configuration and ownership | **Blocking deployment security** |
| OI-14 | Lab HTTPS certificate is pending | HTTPS is mandatory in the lab | Guide: confirm certificate provision and lab readiness | **Blocking lab acceptance** |
| OI-15 | `shared.course_link` columns are not yet agreed | B3 and B4 need a consistent course identity and record | B4 owner: confirm columns and issuer/context identity. **Update:** the B4 owner has confirmed the registered-issuer and B4-client binding rule (§13, contract §7.1). **Approved by the guide:** the gateway as a B4 consumer, with the identity key `(iss, context.id)` (§13). **Still pending:** the `shared.course_link` columns, which B4 owns; that approval is separate and not given. B4 #27 is merged; the columns are to be recorded in #72 or a decision record once B4 agrees them | High; consumer approved, columns pending (B4) |
| OI-16 | Moodle role URI observations still need lab confirmation | Source review is not a substitute for a real Moodle launch | Guide/B3: verify actual launch claims in lab. **Decided by the guide:** `mod/lti:admin` is not granted to non-site-administrators on the lab sites; the mapping stays (institution administrator → `administrator`; system administrator URI ignored). **Still pending:** the lab check of what Moodle sends for the four personas (§10.2a, Appendix B V7); the source observation stays unverified until then | High; lab check pending |
| OI-17 | Service-account course visibility remains unverified | B4 course lookup depends on visibility | Guide/B4: verify with lab test | High |
| OI-18 | Upload-resume identity must be confirmed with Video | Upload records must survive session expiry and relaunch | Video owner: confirm `(iss, sub, context id)` identity | High |
| OI-19 | Per-tool accepted-role declarations need downstream agreement | Learner must not become enabled globally | Module owners/guide: confirm each tool's accepted roles | High |
| OI-20 | CSRF mechanism must be explicit in the FastAPI/session design | SEC-09 requires CSRF protection on state-changing requests | **Awaiting guide approval.** Guide/B3: approve mechanism compatible with new-window launch | **Blocking security design** |
| OI-21 | PRD session identity and guide clarification differed in specificity | PRD B3 said `(sub, context id)`; guide says `(iss, sub, context id)` | **Decided by the guide:** `(iss, sub, context id)` ([12 Nov, Q1](https://github.com/narenccode/learnops/issues/58#issuecomment-6826722256); the closing paragraph after point 6 of the [8 Nov comment](https://github.com/narenccode/learnops/issues/58#issuecomment-6721370757) gave the reason: Moodle's `sub` and course ids repeat across sites). PRD B3 amended in this change | Decided; PRD amended (pending contract PR approval) |
| OI-22 | PRD §A5 "a launch with any role not listed is refused with a clear message" conflicted with the guide's reading that "refuse unlisted roles" means "refuse when no listed role is present" ([8 Nov, point 3](https://github.com/narenccode/learnops/issues/58#issuecomment-6721370757)) | The two readings differed for Instructor + unknown role and for institution administrator + system administrator URI (§10.3) | **Decided by the guide:** unlisted role URIs are ignored; refuse only if no recognised role remains ([12 Nov, Q2](https://github.com/narenccode/learnops/issues/58#issuecomment-6826722256)). PRD §A5 amended in this change | Decided; PRD amended (pending contract PR approval) |
| OI-23 | B3 contract format is confirmed (Markdown, JSON Schema, examples; [8 Nov, point 1](https://github.com/narenccode/learnops/issues/58#issuecomment-6721370757)); schema and example locations were not in the contract inventory | The normalized contract must have its schema and valid examples at agreed locations before contract approval | **Structure and paths decided by the guide ([12 Nov, Q3](https://github.com/narenccode/learnops/issues/58#issuecomment-6826722256)) and implemented in this draft:** `contracts/lti-launch.v1.md`, `contracts/lti-launch.v1.schema.json`, `contracts/examples/lti-launch.v1/` (Markdown documentation, JSON Schema, valid examples), and the B3 row in `contracts/CLAUDE.md`. **Still pending:** formal approval of the actual contract, schema and examples by one owner of an affected module under PRD §B.0 rule 3. The guide's approval of the PRD changes and Release 0 gate review remain outstanding. The PR has not been approved. | **Blocking contract approval** (structure decided; content awaiting PR approval) |
| OI-24 | The candidate's cache storage requires a third cookie, `lti1p3-session-id`, that the guide's cookie policy does not cover (§8.7) | It must be sent on Moodle's cross-site launch POST, which (by documented browser behaviour) needs `SameSite=None; Secure` | **Awaiting guide approval.** Guide: whether and how to handle the cookie, its attributes (`SameSite=None; Secure; HttpOnly` proposed), its lifetime, and deletion after launch | **Blocking security design** |
| OI-25 | The v1 schema constrains `role` to `mentor` or `administrator`, so Release 6 Learner support would need a guide-approved approach, such as an approved enum extension or a new contract version (§10.1, contract §9) | The original EXT-07 wording said Learner launches could be enabled without changing the gateway (historical; EXT-07 is amended in this change to make that conditional on OI-25); widening an enum is not obviously "additive, optional" under PRD B.0 | **Open.** Guide: decide whether `learner` is admitted now, added later as an additive change, or handled in a `v2` file, and when (contract §9). Until then the v1 enum is not widened and no Release 6 Learner support is claimed | High |
| OI-26 | Which artefact is pinned (release `2.0.2` or a Git commit), its full SHA, and the `jwcrypto` licence evidence are unverified (§4.1, §5.2) | Stage 1 approval needs a pinned, evidenced dependency record | B3 to verify (Appendix B); guide to review the `jwcrypto` LGPL disclosure under PRD C-11. **Update, 17 Nov 2026:** full SHAs recorded, the security-relevant source files are unchanged between tag `2.0.2` and the reviewed commit, and PyPI metadata agrees on the `jwcrypto` licence (§4.1, §5.2, Appendix C); the artefact choice, the download comparison, the Python 3.12 tree and licence files, and the advisory scan with version floors are still open | **Blocking Stage 1 approval** |

### 16.1 Resolution order

**Before dependency approval**
- OI-01: licence policy, decided by the guide (§3.4) and documented in PRD C-11 and root `CLAUDE.md` by PR #60 (`f8f6e35`); B3 still records each licence beside its pin.
- OI-02: runtime requirements convention, decided by the guide (§3.4); PyLTI1p3Next is added to `requirements.txt` only after this ADR is approved.

**Before security implementation**
- OI-03: atomic, single-use state and nonce, and the launch transaction boundary.
- OI-04: mandatory expiry, required claims, leeway, and maximum token age.
- OI-05: audience and authorized-party validation.
- OI-24: library session-ID cookie policy and lifecycle.
- OI-06, OI-07, OI-08: server-side launch-data storage and shared configuration.
- OI-09: message-type restriction.
- OI-11 and OI-13: HTTPS and trusted-proxy handling.
- OI-20: CSRF mechanism.
- OI-21 and OI-22: decided by the guide; PRD B3 and A5 amended in this change. They no longer block, once the contract PR is approved.

**Before contract approval**
- OI-23: The contract, schema and examples still need approval through the contract PR by one owner of an affected module under PRD §B.0 rule 3. The guide must approve the PRD changes and review the complete contract set at the Release 0 gate. These approvals have not yet happened.
- OI-25: open; how and when `learner` could be added to the `role` enum (the guide sets the timing).

**Before Stage 1 approval**
- OI-26: pinned artefact, full SHA and `jwcrypto` licence evidence.

**Before lab and downstream acceptance**
- OI-12: FastAPI adapter approach.
- OI-14 and OI-16: lab certificate, and the four-persona Moodle role-claim check (§10.2a); the `mod/lti:admin` restriction is decided.
- OI-15: the gateway is approved as a B4 consumer; the `shared.course_link` columns, which B4 owns, are still to be agreed and recorded (#72 or a decision record).
- OI-17: service-account course visibility.
- OI-18: Video upload-resume identity.
- OI-19: per-tool accepted-role declarations.

OI-10 must also be resolved and documented before the key-cache behaviour is accepted for deployment.

---

## 17. Proposed decision and approval conditions

### 17.1 Proposed decision

Select PyLTI1p3Next as the preferred candidate for LearnOps LTI 1.3 launch handling, conditional on the outstanding items in Section 16.

Encapsulate it behind `libs/lti`. Downstream modules consume the normalized launch contract and do not depend directly on PyLTI1p3Next internals.

### 17.1a Approval stages

| Stage | What the guide approves | Needed before | Status |
|---|---|---|---|
| **Stage 1** | The library choice (PyLTI1p3Next, behind `libs/lti`) and the pinned dependency and licence record, including the `jwcrypto` LGPL disclosure (§5.2) | Adding anything to `requirements.txt` | Not approved |
| **Stage 2** | The security design (§6 to §8, §12), including storage ownership and migrations (OI-06, OI-07), the CSRF mechanism (OI-20) and the `lti1p3-session-id` cookie (OI-24) | Any `libs/lti` implementation | Not approved |

Stage 2 does not follow automatically from Stage 1, and neither stage is approved by this contract PR. The contract PR approves the contract only (PRD §B.0).

### 17.2 Before dependency installation (Stage 1)

PyLTI1p3Next is the preferred candidate, not an approved dependency. It is not installed and not pinned anywhere. Do not install or add the runtime dependency until:

1. The licence policy is decided. **Done:** decided by the guide (§3.4, OI-01).
2. The runtime dependency location is decided. **Done:** root `requirements.txt` (§3.4, OI-02).
3. The guide approves this ADR.
4. The resolved dependency tree, versions, and licence evidence are reviewed.
5. PyLTI1p3Next and its dependencies are then added to `requirements.txt` with exact `==` pins and a licence comment beside each.

### 17.3 Before implementation (Stage 2) and before launch integration is accepted

No `libs/lti` code is written until Stage 2 is approved. Once it is, the implementation must demonstrate:

1. Server-side launch-data storage.
2. Shared storage configuration for OIDC login and message launch.
3. Single-use state and nonce enforcement, including concurrent replay, consumed only after signature and claim verification within one launch transaction.
4. Mandatory expiry and correct audience/authorized-party validation.
5. Issuer and deployment checks.
6. `LtiResourceLinkRequest` restriction.
7. Required claim validation and normalized contract output.
8. Cross-session and cross-course launch-data isolation.
9. Two-hour idle session expiry.
10. HTTPS, trusted-proxy, secure-cookie, and CSRF behaviour.
11. Correct role mapping and refusal behaviour.
12. Approved behaviour of the library session-ID cookie (OI-24).
13. The extension-point safeguards in §6.9: exact version pin, startup compatibility checks, and validation-chain tests.
14. Runtime dependencies installed from the root `requirements.txt`, with exact `==` pins and recorded licences (§3.4), and CI installing it together with `requirements-dev.txt`.

### 17.4 Before downstream adoption

Before B4, Video, Studio, Checker, or Grading relies on the LTI boundary:

- The normalized contract must be reviewed through the required `/contract-change` process if it changes a frozen contract.
- B4 must agree and record the `shared.course_link` columns, which it owns. The identity key `(iss, context.id)` is decided and the gateway is approved as a B4 consumer (OI-15).
- Video must confirm upload-resume identity.
- Each tool must declare accepted roles.
- User-facing messages must follow the centralized UI requirements.

### 17.5 Approval status

This ADR is **Proposed**. The guide alone sets the final Approved status under the repository workflow.

Approval of PyLTI1p3Next as the preferred candidate does not itself approve the implementation design or installation. Those items require their own explicit resolution. The licence policy and runtime requirements convention have been decided by the guide (§3.4, OI-01, OI-02); they do not by themselves approve this ADR.

---

## 18. References and evidence

### 18.1 LearnOps repository sources

- `CLAUDE.md` — repository rules, dependency licence policy, workflow, and decision-record location.
- `SETUP.md` — environment and setup instructions.
- `docs/PRD.md`:
  - A5 — roles and permissions.
  - C-11 — dependency licence policy (as updated by PR #60, `f8f6e35`; §3.4).
  - A10 — technology stack and LTI library selection.
  - B3 — LTI 1.3 launch requirements.
  - SEC-01 — launch validation.
  - SEC-02 — authorization per request.
  - SEC-06 — personal-data constraint.
  - SEC-09 — CSRF and secure-cookie requirements.
  - EXT-07 — baseline Learner refusal and future extension.
  - EXT-09 — shared libraries.
  - FR-C-06 — Moodle browser role tests.
  - C6 / FR-X-01 — Release 6 Learner launch.
- `docs/traceability.md` — requirement-to-test traceability.

### 18.2 Candidate sources

- PyLTI1p3Next repository: <https://github.com/pymsglobal/pylti1p3next>
- PyLTI1p3Next reviewed commit: `0595282`.
- PyLTI1p3Next reviewed release: `2.0.2`.
- Original PyLTI1p3 repository: <https://github.com/dmitry-viskov/pylti1p3>

### 18.3 Candidate source areas inspected

The static review covered:

- `message_launch.py`
- `oidc_login.py`
- `session.py`
- `launch_data_storage/session.py`
- `launch_data_storage/cache.py`
- `launch_data_storage/base.py`
- `cookie.py`
- `message_validators/` (`__init__.py`, `abstract.py`, `resource_message.py`)
- `README.rst` (storage, cookie, and documented API sections)
- Git history of `validate()` in `message_launch.py`
- Cookie and framework adapter implementations.
- Package metadata and dependency declarations.
- Licence file and Git history.

The candidate's code and tests were not executed. The findings describe the inspected commit and must be rechecked if the candidate version changes.

### 18.4 Evidence limitations

The Moodle role URI observations are based on Moodle source and guide clarification; lab launch confirmation is pending.

The service-account visibility and lab HTTPS certificate are also pending lab confirmation.

Statements about PyJWT behaviour and browser cookie rules (§6.2, §6.3, §8.7) come from their documentation. PyJWT was not available locally and no code was run, so they were not independently verified from source.

Before this ADR is marked Approved, every external source cited in it must be opened and checked. Repository requirement references must be verified against the B3 review baseline at commit `f8f6e35` (PR #60); any subsequent changes to those requirements must be reviewed before approval.

---

## 19. Review checklist

- [ ] Guide approves PyLTI1p3Next as the preferred candidate.
- [x] Guide decides the dependency licence policy (OI-01; decision received, §3.4).
- [x] Guide decides the runtime dependency convention (OI-02; decision received, §3.4).
- [x] Location of the guide's OI-01/OI-02 response is cited in §3.4.
- [x] Guide updates PRD C-11 and root `CLAUDE.md` to the new licence policy (PR #60, `f8f6e35`).
- [ ] Complete direct and transitive dependency tree has been reviewed for licence compatibility and security advisories.
- [ ] Exact approved dependency versions and licence evidence are recorded.
- [ ] After ADR approval, PyLTI1p3Next and its dependencies are added to `requirements.txt` with exact `==` pins and licence comments.
- [ ] Guide approves the server-side launch-data storage approach.
- [ ] Guide approves the atomic single-use state and nonce strategy and the launch transaction boundary (OI-03).
- [ ] Guide approves mandatory expiry and audience/authorized-party enforcement, including the claim policy, leeway, and maximum token age (OI-04, OI-05).
- [ ] Guide approves or rejects the library session-ID cookie and its lifecycle (OI-24).
- [ ] Guide approves the FastAPI integration approach, including the four proposed overrides and their safeguards.
- [ ] HTTPS, CSRF, and trusted-proxy responsibilities are confirmed.
- [x] Guide answers OI-22: unlisted role URIs are ignored; refuse only if no recognised role remains (decision recorded in §3.2; PRD §A5 amended in this change).
- [x] Guide decides OI-21: session identity `(iss, sub, context id)` (PRD B3 amended in this change).
- [x] B3 contract structure and paths decided by the guide and implemented in this draft (OI-23): Markdown contract, schema, valid examples, and the `contracts/CLAUDE.md` row.
- [ ] One owner of an affected module formally approves the contract, schema and examples through the contract PR (PRD §B.0 rule 3).
- [ ] The guide formally approves the PRD changes in the contract PR.
- [ ] The guide reviews the complete contract set at the Release 0 gate.
- [ ] Guide decides OI-25 (open): how and when `learner` could be admitted to the `role` enum for Release 6. Until then no Release 6 Learner support without a contract change is claimed.
- [ ] B3 verifies OI-26: pinned artefact, full SHA, and `jwcrypto` licence evidence; guide reviews the `jwcrypto` LGPL disclosure.
- [ ] Guide approves Stage 1 (library choice and pinned dependency and licence record).
- [ ] Guide approves Stage 2 (security design), including storage ownership and migrations, the CSRF mechanism, and the `lti1p3-session-id` cookie.
- [x] Guide decides OI-16's lab rule: `mod/lti:admin` is not granted to non-site-administrators on the lab sites.
- [ ] Moodle role URIs are confirmed through a lab launch: the four-persona checklist (§10.2a) is run on Moodle 4.5 and 5.3 and recorded in the release harness report.
- [x] Guide approves the gateway as a B4 consumer, with the identity key `(iss, context.id)` (OI-15).
- [ ] B4 agrees and records the `shared.course_link` columns, which it owns (#72 or a decision record).
- [ ] B4 confirms service-account course visibility.
- [ ] Video confirms upload-resume identity.
- [ ] Each module confirms its accepted roles.
- [ ] Contract changes, if any, receive `/contract-change` review.
- [ ] All references are opened and verified.
- [ ] Guide grants final ADR approval.

**Final status: Proposed — pending guide review and approval (Stage 1 and Stage 2). No dependency installation or LTI implementation is authorized by this ADR.**

---

## Appendix A. One-page approval summary

**What is being decided:** whether LearnOps uses **PyLTI1p3Next** (distribution `pylti1p3next`, import `pylti1p3`, MIT) behind `libs/lti` for LTI 1.3 launch handling. It is the preferred candidate, **not** an approved dependency. It is not installed and not pinned.

**Candidate record.** Reviewed commit `0595282` (22 August 2026; short hash only), latest release `2.0.2` (2 June 2026). Static source review only; nothing was executed. The pinned artefact and full SHA are **not yet chosen** (§4.1, OI-26).

**Findings the design must close** (static review, §6 to §8): launch data is stored in the framework session by default; nonce and state are never consumed, so a captured launch POST can be replayed; `exp` is not mandatory; `aud` is not verified and `azp` is not read; all LTI message types are accepted; an extra `lti1p3-session-id` cookie is required; no FastAPI adapter exists. The proposed fix is a thin `libs/lti` adapter that overrides four `MessageLaunch` methods (§6.9), with tests (§12).

**Licence disclosure for the guide (PRD C-11).**

| Dependency | Licence | Evidence status |
|---|---|---|
| PyLTI1p3Next | MIT | Project licence file read at the reviewed commit |
| `typing_extensions` | PSF-2.0 | Verified for version 4.16.0 only (§5.1) |
| **`jwcrypto`** (`~=1.5`, direct) | **LGPL-3.0-or-later (weak copyleft)** | Guide-reported; PyPI metadata for 1.6.1 agrees (17 Nov 2026). Licence file and pinned version not checked. Allowed only unmodified (§5.2) |
| `certifi` (via `requests`) | MPL-2.0 | Verified for the versions inspected on Python 3.14, not on 3.12 (§5.3); PyPI metadata agrees for 2026.10.23 |
| `pyjwt`, `requests`, and the rest of the tree | MIT, Apache-2.0 and permissive, as declared | PyPI metadata only (§5.3 table); not verified on Python 3.12 or from licence files |
| Security advisories | — | PyJWT has 24 records in the GitHub advisory database (query in §6.2, 17 Nov 2026), so the PyJWT version floor matters (§6.2); not a resolved-tree scan (V3) |

**Decided by the guide:** see §1.1 (identity, course-link key, role mapping, accepted message type, cookies, validation list, proxy trust, new-window launch).

**Awaiting your approval.**

1. **Stage 1:** the library choice and pinned dependency and licence record, including `jwcrypto`.
2. **Stage 2:** the security design before any `libs/lti` code, including:
   - storage ownership and migration responsibility (OI-06, OI-07);
   - the CSRF mechanism (OI-20);
   - whether and how to handle the `lti1p3-session-id` cookie and its lifecycle (OI-24).
3. Contract-level, through the contract PR (PRD §B.0): formal approval of the contract, schema, examples and PRD changes (OI-23; the structure and paths are already decided), and OI-25 (open: whether and how `learner` joins the role enum; no Release 6 Learner support is claimed until decided).

**What this change does not do:** no `libs/lti`, no dependency install, no `requirements.txt` entry, no Moodle compatibility claim.

---

## Appendix B. Verification plan

This plan lives here, not in `docs/testing`. It lists what must be checked, by whom, and where the result is recorded. Nothing below has been run yet unless Appendix C says so.

| # | Check | Method | Result recorded in |
|---|---|---|---|
| V1 | Pinned artefact: PyPI release `2.0.2` versus a Git commit; full SHA; that the pinned code matches the reviewed code | Compare the published artefact with commit `0595282`; re-review the differences if any | Appendix C |
| V2 | Licence of every direct and transitive dependency, on **Python 3.12**, including `jwcrypto` | Read each package's own metadata and licence file in a throwaway Python 3.12 environment (not the project's); compare with PRD C-11 | Appendix C; then the comment beside each pin in `requirements.txt` |
| V3 | Security advisories for the resolved tree (SEC-08), including PyJWT (§6.2: CVE-2024-53861 affects 2.10.0 only) | Run the CI dependency scan on the resolved set; the PyJWT floor is set from this result | Appendix C |
| V4 | The extension points in §6.9 exist in the pinned version | Run the startup compatibility checks (LTI-30) | Test report |
| V5 | Security acceptance tests LTI-01 to LTI-32 (§12) | Automated tests in `tests/`, written failing first | Test report; `docs/traceability.md` |
| V6 | The normalised result and the examples meet the schema | Validate every file in `contracts/examples/lti-launch.v1/` against the schema; negative cases live in tests or a vectors file, never in the examples folder | CI (contract validation) |
| V7 | Moodle role URIs actually sent (OI-16), including what site administrators send | A real launch from each lab Moodle (4.5 and 5.3) with Instructor, Learner, institution administrator and site-administrator accounts, claims inspected in the lab only, using the checklist in §10.2a; also confirm that no account other than a site administrator holds `mod/lti:admin` | **Release harness report (PRD E2)** |
| V8 | Launch works on Moodle 4.5 and 5.3, new-window launch, cookies and CSRF behave as designed | Harness run on fresh 4.5 and 5.3 sites | **Release harness report (PRD E2)** |
| V9 | `context.id` equals the Moodle course id, and service-account course visibility (OI-17) | Lab launch plus a B4 course lookup | Release harness report (PRD E2) |
| V10 | Lab HTTPS certificate and trusted-proxy configuration (OI-13, OI-14) | Launch over HTTPS through the lab proxy; test an untrusted forwarded header (LTI-18) | Release harness report (PRD E2) |

Rules: V1 to V6 results go in Appendix C of this ADR. **Moodle compatibility results (V7 to V10) go in the release harness report under PRD E2, not in this ADR.** Never claim a check passed until it has run and its output has been read.

---

## Appendix C. Verification record (PRD App-C)

PRD App-C asks that Release 0 verification results are recorded in `docs/decisions/`. This appendix is that record for the B3 items. It is not the PRD's own Appendix C.

**PRD App-C item 6 — the LTI 1.3 library choice and its licence.**

| Plan item | Status as of 15 November 2026 (V1 to V3 updated 17 November 2026) | Evidence |
|---|---|---|
| V1 Pinned artefact and full SHA | **Partly done, 17 Nov 2026 (follow-up review, PR for `contracts/b3-library-security-review`).** Full SHAs recorded; GitHub compare shows the security-relevant source files unchanged between tag `2.0.2` and the reviewed commit. **Not done:** the artefact is not chosen, and the PyPI wheel and sdist were not downloaded or compared with the tag | §4.1 (GitHub REST API compare; PyPI JSON API) |
| V2 Dependency licences on Python 3.12 | **Partly done, still not complete.** Declared licences from PyPI metadata for the likely tree, 17 Nov 2026 (§5.3 table), including `jwcrypto` (LGPL-3.0-or-later, declared for 1.6.1). **Not done:** the resolved Python 3.12 tree, the pinned versions, and the licence files. `typing_extensions` 4.16.0 (PSF-2.0) and `certifi` 2026.5.20 (MPL-2.0) were inspected earlier in other environments (§5.1, §5.3) | §5.1, §5.2, §5.3 |
| V3 Advisory scan | **Partly done, still not complete, 17 Nov 2026.** GitHub advisory database queried for `pyjwt` (24 records) and `jwcrypto` (5 records) only (§5.2, §6.2). **Not done:** the CI dependency scan of the resolved tree, and the other packages (`requests`, `urllib3`, `cryptography` and the rest). No version floor is set | §5.2, §6.2 |
| V4 to V5 Extension points and security tests | **Not done**; no `libs/lti` exists | None |
| V6 Schema and examples | **Done for this change, 16 Nov 2026:** `python -m pytest -q libs/contracts` under Python 3.12.16 (Unicode 15.0.0) with the pinned `requirements-dev.txt`: 1842 passed, 0 failed, of which 358 are in `libs/contracts/tests/test_lti_launch_v1.py`. The schema passes the Draft 2020-12 meta-check and the three examples validate. `context.id` behaviour is covered by `test_positive_integer_context_ids_are_accepted`, by the `context-id-…`, `empty-context-id` and `numeric-context-id` cases of `test_invalid_launch_result_is_rejected_at_the_right_place`, and by the drift guard `test_contract_markdown_quotes_the_schema_context_id_pattern`. The same pattern was checked once in JavaScript (Node 20, with and without the `u` flag); that check is not a repository test. The optional-claim rule (contract §3.2) is covered by the shared vectors `contracts/test-vectors/lti-launch-optional-claims.v1.json` and by `test_claim_vectors_are_well_formed`, `test_claim_vectors_cover_every_row_of_section_3_2`, `test_claim_vector_agrees_with_section_3_2`, `test_expected_result_for_every_claim_vector_is_schema_valid`, `test_schema_alone_accepts_a_white_space_only_string`, the White_Space tests (`test_python_unicode_database_is_unicode_15_0`, `test_vectors_file_lists_exactly_unicode_white_space`, `test_white_space_rule_is_not_python_isspace`, `test_each_white_space_character_alone_is_absent`, `test_isspace_only_character_is_preserved`) and the drift guard `test_contract_section_3_2_names_the_vectors_file` | `libs/contracts/tests/test_lti_launch_v1.py`; the output above. Contract checks only: they do not cover signature, nonce, session or Moodle behaviour. The §3.2 tests check the vectors and schema conformance only; **no runtime normaliser exists** (`libs/lti` is not created), so normalisation at the boundary is neither implemented nor tested. `libs/lti` must pass the same vectors (V5) |
| V7 to V10 Moodle compatibility | **Not done.** No Moodle compatibility is claimed. Results belong in the release harness report (PRD E2) | None |

Update this table when each check runs, with the date, the person, the command or method, and the evidence.
