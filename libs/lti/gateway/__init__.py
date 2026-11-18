"""LTI gateway: turns a verified Moodle launch into a server-side session and sends the user to
the right LearnOps tool (PRD §B3; contract sections cited as "B3 §n")."""

from lti.gateway.app import create_app
from lti.gateway.config import GatewayConfig, GatewayConfigError, config_from_env
from lti.gateway.routing import Tool
from lti.gateway.sessions import (
    InMemorySessionStore,
    Session,
    SessionRefused,
    SessionStore,
)
from lti.gateway.verifier import LaunchRefused, LaunchResult, LaunchVerifier

__all__ = [
    "GatewayConfig",
    "GatewayConfigError",
    "InMemorySessionStore",
    "LaunchRefused",
    "LaunchResult",
    "LaunchVerifier",
    "Session",
    "SessionRefused",
    "SessionStore",
    "Tool",
    "config_from_env",
    "create_app",
]
