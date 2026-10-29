"""User-facing messages of the model interface (PRD UI-05: what happened, then what to do next).

config.py keeps its own messages next to the rule they explain. No message here may contain
inputs, prompts or model output (PRD B5.3, OPS-04): only task names, versions and schema paths.
"""

from __future__ import annotations

from typing import Final

UNREGISTERED_TASK: Final = "Task '{task}' is not registered. Register it with register_task() before calling run()."
DUPLICATE_TASK: Final = "Task '{task}' is already registered. Task names are unique across LearnOps; pick another."
BAD_TASK_NAME: Final = (
    "Task name '{task}' is not allowed. Use lowercase letters, digits and underscores, "
    "starting with a letter."
)
BAD_TASK_SCHEMA: Final = (
    "The {which} schema of task '{task}' is not a valid JSON Schema ({detail}). Fix the schema "
    "before registering the task."
)
SCHEMA_MISMATCH: Final = (
    "run() was called for task '{task}' with an output_schema that is not the one registered "
    "for it. Pass the registered schema (get_task('{task}').output_schema)."
)
INVALID_INPUT: Final = (
    "The inputs for task '{task}' do not match its input schema ({detail}). Fix the inputs; "
    "nothing was sent to the model."
)
INVALID_OUTPUT: Final = (
    "Task '{task}' returned output that does not match its output schema on both attempts "
    "(last problem: {detail}). Nothing was returned. Try again later or report the prompt "
    "version {prompt_version}."
)
INVALID_META: Final = (
    "The provider '{provider}' produced call metadata that does not match the B5 contract "
    "({detail}). Nothing was returned. This is a bug in the provider code."
)
NO_PROMPT: Final = (
    "No prompt file for task '{task}' in {folder}. Add {folder}/v1.md with a 'prompt_version' "
    "header."
)
BAD_PROMPT_FILE: Final = (
    "Prompt file {path} is not valid: {detail}. Each file starts with a '---' header that "
    "contains 'prompt_version: <task>/v<N>', matching its folder and file name."
)
LOCAL_UNREACHABLE: Final = (
    "The local model endpoint did not answer ({detail}). Check that the lab model service is "
    "running and MODEL_LOCAL_URL is right, then try again."
)
LOCAL_NOT_INTEGRATED: Final = (
    "The local provider has no transport yet: the lab endpoint's protocol is not decided "
    "(design Q19). Pass a transport to create_provider() in tests."
)
HOSTED_NOT_IMPLEMENTED: Final = (
    "The hosted provider is not implemented yet: the provider and SDK are not chosen "
    "(design Q19). Use MODEL_PROVIDER=local."
)
MISSING_SETTING: Final = (
    "{variable} is not set. Set it in the environment (see .env.example)."
)
FAKE_NOT_SELECTED: Final = (
    "The fake provider was requested but MODEL_PROVIDER is '{value}'. Set MODEL_PROVIDER=fake "
    "in the test run."
)
FAKE_NO_FIXTURE: Final = (
    "The fake provider has no response for task '{task}' with these inputs. Add one with "
    "add_response() in the test."
)
