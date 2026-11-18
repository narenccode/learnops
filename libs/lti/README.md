# `libs/lti`: LTI 1.3 gateway

Moodle launches the Video and Grading tools through this gateway (PRD §B3,
`contracts/lti-launch.v1.md`). The gateway turns a **verified** launch into a server-side
session and sends the user to the right tool. It does not check ID tokens itself: launch
validation (signature, claims, state, nonce; PRD SEC-01) is plugged in through
`lti.gateway.verifier.LaunchVerifier`.

## Endpoints

| Method and path | What it does |
|---|---|
| `GET /health` | `{"status": "ok"}` while the gateway runs |
| `GET /lti/jwks` | The gateway's public keyset (empty when `LTI_PUBLIC_KEY_PATH` is not set) |
| `GET` or `POST /lti/login` | OIDC login from Moodle. `target_link_uri` must be exactly one of the launch URLs below; the verifier builds Moodle's auth redirect |
| `POST /lti/launch/video`, `POST /lti/launch/grading` | Verified launch → session cookie → `303` to `VIDEO_APP_URL` or `GRADING_APP_URL` |
| `GET /lti/session[?tool=video\|grading][&context_id=42]` | For the tools: the current session's tool and B3 launch result, or `401`/`403`. Counts as activity |

## Moodle tool registration

Register one tool in Moodle (Site administration → Plugins → Manage tools) with:

- Tool URL / initiate login URL: `<GATEWAY_BASE_URL>/lti/login`
- Redirection URI(s): `<GATEWAY_BASE_URL>/lti/launch/video` and `<GATEWAY_BASE_URL>/lti/launch/grading`
- Public key type: Keyset URL `<GATEWAY_BASE_URL>/lti/jwks` (only if the tool key pair is set up)
- Launch container: **new window**. The session cookie is `SameSite=Lax` (ADR 0001 §8.2), which
  browsers do not send inside a Moodle iframe.

Each activity's launch URL picks the tool: `/lti/launch/video` or `/lti/launch/grading`.

## Rules the gateway enforces

- The tool comes from the launch path and is matched exactly against a fixed list; the
  destination comes only from configuration. The browser cannot choose a redirect address.
- An unknown tool is refused before the verifier runs, so no state or nonce is used up.
- The verifier's result is checked against the B3 v1 model before a session exists. Only
  `mentor` and `administrator` get a session; Learner is refused (PRD EXT-07).
- The session is bound to `(iss, sub, context.id)` and ends after two hours idle (B3 §6). The
  cookie `__Host-learnops-session` is `Secure; HttpOnly; SameSite=Lax; Path=/`. A new launch ends
  the earlier session.
- Login sets the OIDC state cookie `__Host-lti-state` (`Secure; HttpOnly; SameSite=None`,
  ten minutes; ADR 0001 §8.1). A launch whose form `state` does not match it is refused before
  the verifier runs, and the cookie is deleted after every launch attempt.
- `/lti/session` refuses a request for the other tool, and a mentor's request for another
  course (PRD SEC-02, A5).
- The raw ID token, nonce and state never reach a tool or a log; `name` and `email` are never
  logged (B3 §10).
- Without a verifier, login and launch answer `503`: the gateway never creates a session from an
  unverified launch.

## Run it

```bash
uvicorn --app-dir libs --factory lti.gateway.app:app_from_env --host 0.0.0.0 --port 8000
```

Put it behind the HTTPS reverse proxy that also serves the Video and Grading applications, so
the `__Host-` cookie reaches them. Run **one** worker: sessions are in memory.

## Open items (guide)

- Session storage backend and migrations (ADR 0001 OI-06, OI-07). Until then
  `InMemorySessionStore`; a database store implements the same `SessionStore` protocol.
- CSRF mechanism for later state-changing requests (OI-20).
- The launch verifier itself (Peer 1) and ADR 0001 Stage 1 and 2 approval.

## Undo

Remove `libs/lti/gateway`, the gateway lines in `requirements*.txt` and `.env.example`, and the
Moodle tool registration. No database or Moodle data is changed.
