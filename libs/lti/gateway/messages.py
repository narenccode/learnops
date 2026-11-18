"""Every message the gateway shows a user, in one place (PRD UI-05: what happened, what to do).

The B3 refusal texts are quoted from contracts/lti-launch.v1.md §8.
"""

AUTH_FAILED = (
    "Your Moodle sign-in could not be verified. Open the tool again from your course."
)
CONTEXT_INVALID = (
    "This tool must be opened from inside a course. Open your course in Moodle and select "
    "the tool there."
)
ROLE_REFUSED = "This tool is not available in this version. Use your course in Moodle."
UNKNOWN_TOOL = (
    "This tool link is not recognised. Ask your course administrator to check the tool's "
    "launch link in Moodle."
)
SESSION_ENDED = "Your session has ended or was not found. Open the tool again from your course in Moodle."
OTHER_COURSE = "Your session is for a different course. Open the tool again from that course in Moodle."
WRONG_TOOL = (
    "Your session was opened for a different tool. Open this tool again from your course in "
    "Moodle."
)
NOT_SET_UP = (
    "Moodle sign-in is not set up on this server yet. Ask the LearnOps administrator to "
    "finish the LTI setup."
)
