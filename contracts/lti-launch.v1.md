# B3 — LTI 1.3 launch contract (v1)

| Item | Value |
|---|---|
| Contract | B3 LTI 1.3 launch (PRD §B3) |
| Version | v1 |
| Owner | Student 2 (as integration lead) |
| Consumers | Module 1 Studio, Module 2 Checker, Module 3 Grading, Module 4 Video; the Release 6 player later (see §9) |
| Schema | `contracts/lti-launch.v1.schema.json` (JSON Schema Draft 2020-12) |
| Examples | `contracts/examples/lti-launch.v1/` (valid examples only) |
| Implemented by | `libs/lti` (not yet created; this document is the contract it must meet) |
| Background | `docs/decisions/0001-lti-library.md` |

If this document conflicts with `docs/PRD.md`, the PRD wins (root `CLAUDE.md`).

## 1. Purpose

Moodle launches each LearnOps tool with LTI 1.3. This contract defines what a module receives
after `libs/lti` has validated the launch: one **normalised launch result**. Modules read that
result only. They never parse an ID token, read raw Moodle claims, or work out roles themselves.

The JSON Schema describes the normalised result, **not** the incoming Moodle claims.

## 2. Accepted message type

Only `LtiResourceLinkRequest` is accepted in v1. Deep Linking is not required. Any other
message type is refused before any state or nonce is consumed and before a session exists.

## 3. Incoming claims

These are the claims `libs/lti` reads from the validated ID token. Moodle supplies the context
id as the Moodle course id.

| Incoming claim | Required | Becomes |
|---|---|---|
| `iss` | Yes | `iss` |
| `sub` | Yes | `sub` |
| `aud`, `azp` | Yes (`azp` when `aud` has several values) | Checked only; never passed on |
| `exp`, `nonce` | Yes | Checked only; never passed on |
| `https://purl.imsglobal.org/spec/lti/claim/deployment_id` | Yes | `deployment_id` |
| `https://purl.imsglobal.org/spec/lti/claim/message_type` | Yes | `message_type` |
| `https://purl.imsglobal.org/spec/lti/claim/roles` | Yes, with at least one recognised role | `role` (§5) |
| `https://purl.imsglobal.org/spec/lti/claim/context` | Yes (`id`); `title` optional | `context.id` (§3.1), `context.title` (§3.2) |
| `https://purl.imsglobal.org/spec/lti/claim/resource_link` | Yes (`id`) | `resource_link.id` |
| `name` | No | `name`, or `null` (§3.2) |
| `email` | No | `email`, or `null` (§3.2) |

Unknown claims are ignored.

### 3.1 `context.id` is a positive Moodle course id

Moodle supplies its course id as the LTI context id, and B4 uses it as the course id. It is therefore
a **positive integer written as a string**, in ASCII digits only. These are refused (§8):

- zero and negative values (`"0"`, `"-5"`);
- non-numeric values, including a sign, a decimal point or an exponent (`"abc"`, `"+5"`, `"4.2"`, `"1e3"`);
- a leading zero (`"007"`);
- any whitespace, before, after or inside (`" 42"`, `"42 "`);
- non-ASCII digits (for example Arabic-Indic or full-width digits);
- a newline anywhere, including a final one (`"42\n"`).

No upper bound is set. The schema enforces the format with the pattern `^[1-9][0-9]*(?!\n)$`; the
`(?!\n)` part is needed because `$` alone would also accept a final newline in Python's `re`.

Portability: a lookahead is outside the regular-expression subset that the JSON Schema specification
recommends (core §6.4, "SHOULD limit themselves"). The pattern is tested in Python `jsonschema`
(the repository tests) and was also checked once in JavaScript (Node 20, with and without the `u`
flag; not a repository test), the two languages of this project's stack. A validator without
lookahead support must express the same rule another way, for example `^[1-9][0-9]*$` together with
a `not` of `pattern` `\n`; in Python `jsonschema` 4.26.0 that rejects the same values.

### 3.2 Optional claims: absent, null and empty values

`libs/lti` normalises these **once, at the boundary**: when it reads the validated claims and
before it builds the result. Modules receive the result already normalised and never normalise
these fields again.

| Incoming value | `name`, `email` | `context.title` |
|---|---|---|
| Claim absent | `null` | omitted |
| `null` | `null` | omitted |
| Empty string | `null` | omitted |
| Whitespace-only string | `null` | omitted |
| Not a string (a number, boolean, object or array) | `null` | omitted |
| Any other string | the string, unchanged | the string, unchanged |

- **Whitespace-only** means the string contains no character except Unicode White_Space characters
  (for example space, tab, newline and the no-break space U+00A0): the 25 code points of the
  Unicode 15.0.0 White_Space property, listed in the vectors file below. This is **not** Python's
  `str.isspace()` (or `str.strip()`, or `\s` in `re`), which also count U+001C to U+001F as white
  space; a string of those characters is kept. Characters that look empty but are not
  White_Space, such as the zero-width space U+200B and U+FEFF, are kept too.
- **Unchanged** means no trimming: a string that has any other character is passed on exactly as
  received, character for character, including white space before, after or inside it.
- **Not a string:** these claims are optional display data and never decide access (PRD SEC-06), so a
  value of the wrong type is treated as absent. It does not refuse the launch.
- `context.title` is omitted, never `null`, because the schema does not allow `null` there.
- The schema keeps rejecting an empty string, and any non-string value, for all three (§4), so a
  result that kept one would fail validation (§11). The schema does not reject a whitespace-only
  string; turning it into `null` or omitting it is the job of `libs/lti`.
- **Test vectors:** `contracts/test-vectors/lti-launch-optional-claims.v1.json` holds the cases of
  this table (each applies to all three claims). The shared contract tests check that the vectors
  cover every row and agree with this section, and that each expected result is schema-valid.
  **No normaliser exists yet:** `libs/lti` has not been created. When it is added it must pass the
  same vectors.

## 4. Normalised launch result

| Field | Type | Required | Meaning |
|---|---|---|---|
| `iss` | string, non-empty | Yes | Moodle platform issuer. Part of the session identity and of the `shared.course_link` key. |
| `sub` | string, non-empty | Yes | User identifier, unique only within `iss`. |
| `deployment_id` | string, non-empty | Yes | Deployment of the launch, already checked against the configured registration. |
| `message_type` | `"LtiResourceLinkRequest"` | Yes | The accepted message type. |
| `role` | `"mentor"` or `"administrator"` | Yes | The single resolved role (§5). |
| `context.id` | string, positive integer in ASCII digits, no leading zero (§3.1) | Yes | LTI context id (the Moodle course id). The course the user launched from. |
| `context.title` | string, non-empty | No | Course title for display. Omitted when empty (§3.2). |
| `resource_link.id` | string, non-empty | Yes | The launched tool placement. |
| `name` | string, non-empty, or `null` | No | Display name if shared, otherwise `null` (§3.2, PRD SEC-06). |
| `email` | string, non-empty, or `null` | No | Email if shared, otherwise `null` (§3.2, PRD SEC-06). |

Unknown fields are allowed. Readers ignore fields they do not know (PRD EXT-02, B.0).

## 5. Role mapping and precedence

`libs/lti` reads every role URI in the `roles` claim, maps the recognised ones and ignores all
others (including the system administrator role).

| Role URI | Normalised role |
|---|---|
| `http://purl.imsglobal.org/vocab/lis/v2/membership#Instructor` | `mentor` |
| `http://purl.imsglobal.org/vocab/lis/v2/institution/person#Administrator` | `administrator` |
| `http://purl.imsglobal.org/vocab/lis/v2/membership#Learner` | Learner: refused by baseline tools (PRD EXT-07) |
| Any other URI, including `http://purl.imsglobal.org/vocab/lis/v2/system/person#Administrator` | Ignored |

Rules:

1. Administrator takes precedence if both administrator and instructor are present.
2. Instructor plus Learner resolves to `mentor` for baseline tools.
3. Learner counts only when it is the only recognised role; the launch is then refused.
4. If no recognised role remains, the launch is refused.
5. An unlisted role never causes a refusal when a recognised role is also present.

Because Learner is refused before a baseline session is created, `learner` is not a value of
`role` in v1. Learner support for a later tool (the Release 6 player) is unresolved (ADR 0001,
OI-25). It requires a guide-approved contract and gateway compatibility approach, which may be an
approved extension of the v1 enum or a new contract version, made under PRD §B.0 (§9). Until
then no Learner support is claimed.

## 6. Session identity and expiry

- The server-side session is bound to **(`iss`, `sub`, context id)**.
- The session expires after **two hours idle**. Every authenticated request counts as activity.
- After expiry the user relaunches from Moodle.
- Launch data is read only through the authenticated server-side session. A launch id or any
  other identifier alone never authorises access.

## 7. Course-context isolation and course link

- A user sees only data for the course (LTI context) they launched from, except administrators
  (PRD A5). Every request is authorised from the session's role and course context (PRD SEC-02).
- `shared.course_link` is keyed by **`iss` plus context id**. The columns are agreed between
  Student 2 and Student 3 (B4 owner); this contract does not define them.

### 7.1 `iss` must identify a registered platform

- A launch is accepted only if its `iss` identifies a registered platform. Matching is **exact**:
  the `iss` string is compared as received, with no trimming, no case folding and no trailing-slash
  or other normalisation. A launch from an unknown issuer is refused (§8); no result and no session
  are created.
- The `iss` in an incoming token is **untrusted** until the signature has been verified. It may be
  used only to locate the candidate registered-platform configuration whose keys verify that
  signature. The issuer is trusted only after the signature has been verified successfully against
  that configuration.
- B4 is called **only through the client bound to the configuration that corresponds to the
  registered issuer**. A course id from one registered platform is never resolved against another
  platform's client. There is **never a fallback** to another platform's B4 client, or to a default
  one: if no client is bound for the verified `iss`, the B4 call is refused.
- Formal approval by the guide of the gateway as a consumer of B4 is still pending (ADR 0001,
  OI-15). This section states the B3 rule; it does not claim that approval.

## 8. Refusal conditions

A launch is refused, and no normalised result or session is created, when any of these holds:

| Condition | Class |
|---|---|
| Signature, `exp`, `aud` (against the configured client id), `azp` (for several audiences), `iss`, `deployment_id`, message type or single-use nonce check fails, or state is invalid | Authentication: "Your Moodle sign-in could not be verified. Open the tool again from your course." |
| `iss` does not exactly match a registered platform (§7.1) | Authentication |
| A required claim is missing (`sub`, `deployment_id`, `resource_link.id`, …) | Authentication |
| `context.id` is missing, or is not a positive integer in ASCII digits (§3.1) | Refused with guidance to open the tool from a course |
| No recognised role remains | Authorisation: HTTP 403, "This tool is not available in this version. Use your course in Moodle." |
| Learner is the only recognised role | Authorisation: HTTP 403, same message |

After the session exists, a request for another course context is refused for a mentor.
Administrator access follows the all-courses rule in PRD A5. Learner refusal (PRD EXT-07) must not
be removed.

## 9. Compatibility and change

- v1 is frozen after Release 0. Afterwards only additive, optional fields are allowed (PRD B.0).
- **Open point:** the `role` enum has two values. Adding `learner` for the Release 6 player would
  widen that enum. Whether that is "additive" or needs a `v2` file is for the guide to decide when
  Release 6 is planned; it is not decided here.

## 10. Must never reach a consuming module

The normalised result and every module interface must not contain, and logs must not record:

- the raw ID token or any other raw JWT, or the full set of claims;
- the `nonce` or the OIDC `state`;
- private key material, client secrets or tokens;
- library-specific objects.

### 10.1 Personal data in logs

`name` and `email` are personal data that the result carries to every module (PRD SEC-06). They are
**never written to logs**.

This section sets no other logging rule. What else a log line contains stays as PRD OPS-04 and each
module's own rules say. For diagnostics the guide asked for distinct internal reason codes in the log
only, for example `role_learner` and `role_none` (the guide's comment of 8 November 2026 on Issue
\#58, point 5:
<https://github.com/narenccode/learnops/issues/58#issuecomment-6721370757>).

## 11. Schema validation expectations

- `libs/lti` validates every normalised result against `lti-launch.v1.schema.json` before handing
  it to a module (PRD B.0 rule 4).
- Modules validate a result they read, and reject an invalid one with a clear error.
- The schema checks structure only. Signature, `exp`, `aud`, `azp`, `iss`, deployment, nonce, state,
  role mapping, session and isolation rules are enforced and tested in `libs/lti`, not by the schema.
- `contracts/examples/lti-launch.v1/` holds **valid examples only**. Invalid cases (no recognised
  role, Learner-only, missing context, wrong deployment) belong in tests or a vectors file, never
  in that folder.
- CI validates every example against the schema.
- **Tests (PRD B.0 rule 3).** In Release 0 the shared contract tests cover this contract:
  `libs/contracts/tests/test_lti_launch_v1.py`, with the optional-claim vectors of §3.2. A
  consuming module adds its tests when its code that reads the contract exists; before that,
  the shared contract tests cover the change.
