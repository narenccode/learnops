# Command-line tools: the `--config` file and the order of settings

**Status:** decided by the guide, [PR #118, comment 7053353807](https://github.com/narenccode/learnops/pull/118#issuecomment-7053353807)
(20 November 2026, answer 3). Written down here once, as the guide asked, so that other command-line tools follow it.
**Number:** 0020, the next free number when this was written (`main` has 0001 to 0019). It is taken again at
merge if another record has merged first.

## Decision

PRD OPS-02 (environment-based configuration) and OPS-05 (every CLI has `--config <file>`) fit together:
the environment is for deployment settings and secrets; `--config` is for non-secret options.

- **Format:** YAML (PyYAML is already a pinned dependency), read with `safe_load`.
- **Keys:** the option names. A tool documents them in its help text and its demo or README.
- **Unknown key or wrong type:** refused with a clear message that says what to write instead, exit code `2`.
- **Order, strongest first:** the command-line flag, then the `--config` file, then the environment variable,
  then the default.
- **No secrets:** a config file never holds a secret (PRD C-06). Secrets stay in the environment.

## Where it is applied first

The D2 demo, `scripts/demos/demo_d2_course_package_checker.py` (`checker check <package> --json`). Its keys are
`package`, `json`, `dry-run` and `check`. D2 reads no environment variable, so the environment step of the
order has nothing to apply there. A flag can only switch an option on, so a missing flag leaves the config
value (or the default, off) in place. `--dry-run` and `--check` together, from any source, are refused (exit `2`).
`package:` in a config file is relative to the repository root; a package named on the command line is
relative to the current folder.

## Cost and limits

- A boolean flag cannot switch an option off when the config file switched it on. Tools that need that add a
  `--no-<option>` flag, as a separate change.
- The D5 demo (`--config` with the single key `package`) predates this record and is not changed here.

## Where it was decided

- Guide, [PR #118, comment 7053353807](https://github.com/narenccode/learnops/pull/118#issuecomment-7053353807), 20 November 2026.
