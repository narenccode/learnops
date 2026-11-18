"""The gateway's HTTP endpoints (FastAPI).

GET  /health                  the gateway is running
GET  /lti/jwks                the gateway's public keyset
GET|POST /lti/login           OIDC login from Moodle, handed to the verifier
POST /lti/launch/{tool}       verified launch -> session cookie -> redirect to the tool
GET  /lti/session             the current session, for the Video and Grading applications

Run it with:  uvicorn --app-dir libs --factory lti.gateway.app:app_from_env
"""

from __future__ import annotations

import json
import logging
import os
import time
from collections.abc import Callable, Mapping
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse, Response
from pydantic import ValidationError

from lti.gateway import messages
from lti.gateway.config import GatewayConfig, config_from_env
from lti.gateway.jwks import load_keyset
from lti.gateway.routing import Tool, parse_tool, role_allowed
from lti.gateway.sessions import (
    IDLE_LIMIT_SECONDS,
    InMemorySessionStore,
    SessionRefused,
    SessionStore,
    authorise,
)
from lti.gateway.verifier import LaunchRefused, LaunchResult, LaunchVerifier

# __Host- makes the browser insist on Secure, Path=/ and no Domain (B3 §6; ADR 0001 §8.2).
SESSION_COOKIE = "__Host-learnops-session"

log = logging.getLogger("lti.gateway")

_REFUSALS: dict[str, tuple[int, str]] = {
    "auth": (401, messages.AUTH_FAILED),
    "context": (400, messages.CONTEXT_INVALID),
    "role": (403, messages.ROLE_REFUSED),
}
_SESSION_REFUSALS: dict[str, tuple[int, str]] = {
    "ended": (401, messages.SESSION_ENDED),
    "other_course": (403, messages.OTHER_COURSE),
    "wrong_tool": (403, messages.WRONG_TOOL),
}


def _log(event: str, **fields: str) -> None:
    """Structured JSON (PRD OPS-04). Never pass a token, name or email here (B3 §10)."""
    log.info(json.dumps({"event": event, **fields}, sort_keys=True))


def _error(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse({"error": code, "message": message}, status_code=status)


def create_app(
    config: GatewayConfig,
    *,
    verifier: LaunchVerifier | None = None,
    store: SessionStore | None = None,
    clock: Callable[[], float] = time.time,
) -> FastAPI:
    """Build the gateway. Without a verifier every login and launch is refused (503): the
    gateway never creates a session from an unverified launch."""
    sessions: SessionStore = store if store is not None else InMemorySessionStore(clock)
    keyset = load_keyset(
        config.public_key_path
    )  # fail at start-up, not on first request
    # redirect_slashes=False: paths match exactly; a 307 would re-post the launch elsewhere.
    app = FastAPI(
        title="LearnOps LTI gateway",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
        redirect_slashes=False,
    )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/lti/jwks")
    def jwks() -> dict[str, Any]:
        return keyset

    @app.api_route("/lti/login", methods=["GET", "POST"])
    async def login(request: Request) -> Response:
        params: dict[str, str] = {k: v for k, v in request.query_params.items()}
        if request.method == "POST":
            form = await request.form()
            params.update({k: v for k, v in form.items() if isinstance(v, str)})
        tool = _tool_from_target(config, params.get("target_link_uri", ""))
        if tool is None:
            _log("login_refused", reason="tool_unknown")
            return _error(404, "tool_unknown", messages.UNKNOWN_TOOL)
        if verifier is None:
            return _error(503, "not_set_up", messages.NOT_SET_UP)
        try:
            auth_url = verifier.login_redirect(params, config.launch_url(tool))
        except LaunchRefused as refused:
            return _refuse(refused, tool)
        return RedirectResponse(auth_url, status_code=302)

    @app.post("/lti/launch/{tool_name}")
    async def launch(tool_name: str, request: Request) -> Response:
        # The tool is checked before the verifier runs, so an unknown tool uses up no state
        # or nonce.
        tool = parse_tool(tool_name)
        if tool is None:
            _log("launch_refused", reason="tool_unknown")
            return _error(404, "tool_unknown", messages.UNKNOWN_TOOL)
        if verifier is None:
            return _error(503, "not_set_up", messages.NOT_SET_UP)
        form = await request.form()
        id_token, state = form.get("id_token"), form.get("state")
        if not isinstance(id_token, str) or not isinstance(state, str):
            return _refuse(LaunchRefused("auth", "form_incomplete"), tool)
        try:
            result = _validated(verifier.launch(id_token, state))
        except LaunchRefused as refused:
            return _refuse(refused, tool)
        if not role_allowed(tool, result.role):
            return _refuse(LaunchRefused("role", "role_not_allowed"), tool)

        old_token = request.cookies.get(SESSION_COOKIE)
        if old_token:
            sessions.end(old_token)  # a new launch replaces any earlier session
        token = sessions.create(result, tool)
        _log(
            "launch_accepted",
            tool=tool.value,
            role=result.role,
            sub=result.sub,
            context_id=result.context.id,
        )
        response = RedirectResponse(config.destinations[tool], status_code=303)
        response.set_cookie(
            SESSION_COOKIE,
            token,
            max_age=IDLE_LIMIT_SECONDS,
            path="/",
            secure=True,
            httponly=True,
            samesite="lax",
        )
        return response

    @app.get("/lti/session")
    def session(
        request: Request, tool: str | None = None, context_id: str | None = None
    ) -> Response:
        token = request.cookies.get(SESSION_COOKIE)
        wanted_tool = None
        if tool is not None:
            wanted_tool = parse_tool(tool)
            if wanted_tool is None:
                return _error(404, "tool_unknown", messages.UNKNOWN_TOOL)
        try:
            if not token:
                raise SessionRefused("ended")
            current = sessions.use(token)
            authorise(current, tool=wanted_tool, context_id=context_id)
        except SessionRefused as refused:
            status, message = _SESSION_REFUSALS[refused.kind]
            return _error(status, f"session_{refused.kind}", message)
        launch_view = current.launch.model_dump(mode="json")
        if launch_view["context"]["title"] is None:
            del launch_view["context"]["title"]  # B3 §3.2: omitted, never null
        body = {
            "tool": current.tool.value,
            "launch": launch_view,
            "idle_limit_seconds": IDLE_LIMIT_SECONDS,
        }
        response = JSONResponse(body)
        # Every authenticated request is activity (B3 §6), so the cookie lifetime moves too.
        response.set_cookie(
            SESSION_COOKIE,
            token,
            max_age=IDLE_LIMIT_SECONDS,
            path="/",
            secure=True,
            httponly=True,
            samesite="lax",
        )
        response.headers["Cache-Control"] = "no-store"
        return response

    return app


def _tool_from_target(config: GatewayConfig, target_link_uri: str) -> Tool | None:
    """Match Moodle's target link exactly against the configured launch URLs."""
    for tool in Tool:
        if target_link_uri == config.launch_url(tool):
            return tool
    return None


def _validated(raw: Mapping[str, Any]) -> LaunchResult:
    try:
        return LaunchResult.model_validate(dict(raw))
    except ValidationError as error:
        context_bad = any(err["loc"][:1] == ("context",) for err in error.errors())
        if context_bad:
            raise LaunchRefused("context", "context_invalid") from error
        raise LaunchRefused("auth", "result_invalid") from error


def _refuse(refused: LaunchRefused, tool: Tool) -> JSONResponse:
    _log("launch_refused", tool=tool.value, reason=refused.reason)
    status, message = _REFUSALS[refused.kind]
    return _error(status, f"launch_{refused.kind}", message)


def app_from_env(env: Mapping[str, str] | None = None) -> FastAPI:
    """Entry point for uvicorn. Launches answer 503 until the launch verifier is plugged in."""
    return create_app(config_from_env(os.environ if env is None else env))
