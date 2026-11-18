"""Shared LTI 1.3 library (PRD §B3, contracts/lti-launch.v1.md).

`lti.gateway` holds the gateway: configuration, server-side sessions and tool routing. Launch
validation (signature, claims, state and nonce) is plugged into the gateway through
`lti.gateway.verifier.LaunchVerifier`.
"""
