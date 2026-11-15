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
| `https://purl.imsglobal.org/spec/lti/claim/context` | Yes (`id`); `title` optional | `context.id`, `context.title` |
| `https://purl.imsglobal.org/spec/lti/claim/resource_link` | Yes (`id`) | `resource_link.id` |
| `name` | No | `name`, or `null` when absent |
| `email` | No | `email`, or `null` when absent |

Unknown claims are ignored.

## 4. Normalised launch result

| Field | Type | Required | Meaning |
|---|---|---|---|
| `iss` | string, non-empty | Yes | Moodle platform issuer. Part of the session identity and of the `shared.course_link` key. |
| `sub` | string, non-empty | Yes | User identifier, unique only within `iss`. |
| `deployment_id` | string, non-empty | Yes | Deployment of the launch, already checked against the configured registration. |
| `message_type` | `"LtiResourceLinkRequest"` | Yes | The accepted message type. |
| `role` | `"mentor"` or `"administrator"` | Yes | The single resolved role (§5). |
| `context.id` | string, non-empty | Yes | LTI context id (the Moodle course id). The course the user launched from. |
| `context.title` | string, non-empty | No | Course title for display. |
| `resource_link.id` | string, non-empty | Yes | The launched tool placement. |
| `name` | string, non-empty, or `null` | No | Display name if shared (PRD SEC-06). |
| `email` | string, non-empty, or `null` | No | Email if shared (PRD SEC-06). |

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

## 8. Refusal conditions

A launch is refused, and no normalised result or session is created, when any of these holds:

| Condition | Class |
|---|---|
| Signature, `exp`, `aud` (against the configured client id), `azp` (for several audiences), `iss`, `deployment_id`, message type or single-use nonce check fails, or state is invalid | Authentication: "Your Moodle sign-in could not be verified. Open the tool again from your course." |
| A required claim is missing (`sub`, `deployment_id`, `resource_link.id`, …) | Authentication |
| `context.id` is missing | Refused with guidance to open the tool from a course |
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
