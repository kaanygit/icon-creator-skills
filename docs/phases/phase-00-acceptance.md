# Phase 00 acceptance

## Phase

- Phase: 00
- Commit: 17873e7
- Date: 2026-05-01
- Reviewer: kaanygit / Codex
- Environment: macOS, zsh, Python 3.14.4 in local `.venv`

## Scope completed

- [x] `pyproject.toml` added with runtime and dev dependencies.
- [x] `pytest.ini` added.
- [x] GitHub Actions CI stub added.
- [x] `shared/` package created.
- [x] `shared/errors.py` created with the project exception hierarchy.
- [x] `shared/config.py` created with defaults/user/project/override merge logic.
- [x] `shared/logging_setup.py` created with structured JSONL logging.
- [x] `shared/image_utils.py` created with load/save/resize/crop/pad/alpha helpers.
- [x] `shared/openrouter_client.py` created with current image response parsing, retries, fallback handling, capability checks, and cost logging.
- [x] `shared/smoke_test.py` created.
- [x] `shared/presets/defaults.yaml` created.
- [x] `shared/presets/openrouter_models.yaml` created with selected, candidate, and retired model records.
- [x] `shared/presets/openrouter_pricing.yaml` created.
- [x] Unit tests added under `shared/tests/`.
- [x] README and CLAUDE context updated to reflect Phase 00 code existence.

## Automated checks

```bash
.venv/bin/python -m pytest
# result: 9 passed
```

```bash
.venv/bin/python -m ruff check .
# result: All checks passed
```

## Manual checks

- [x] Verified `OPENROUTER_API_KEY` is not present in the shell environment.
- [x] Verified no `.env` file exists in the repo.
- [x] Live smoke test intentionally not run because no OpenRouter key is configured.

## OpenCode / harness check

- Required for this phase: no
- Command or invocation: n/a
- Result: n/a
- Notes: Phase 00 has no skill and is terminal-only.

## Known issues

- `python -m shared.smoke_test "fox"` still needs to be run manually after setting `OPENROUTER_API_KEY`.
- Smoke-test visual quality and cost-log verification remain manual because they require a real OpenRouter call.
- Pricing values are planning estimates and must be rechecked before release.

## Sign-off

- [x] Phase implementation accepted
- [ ] Live OpenRouter smoke test accepted
- [x] Safe to start Phase 01 after live smoke test is run or explicitly deferred
