# Phase 14 acceptance

## Phase

- Phase: 14
- Commit: this commit
- Date: 2026-05-01
- Reviewer: kaanygit / Codex
- Environment: macOS, zsh, Python 3.14.4 in local `.venv`

## Scope completed

- [x] `.iconrc.json` discovery added alongside `.iconrc.yaml`.
- [x] Lightweight `.iconrc.json` validation added.
- [x] `icon-skills` CLI entrypoint added.
- [x] Style memory store added under `~/.icon-skills/styles/`.
- [x] `icon-skills styles save/list/show/remove` added.
- [x] Generation CLIs support `--style <name>` recall.
- [x] `icon-skills replay` added for supported local packaging runs.
- [x] Cost decision helper added for threshold and hard-cap checks.
- [x] README documents brand kits and style memory.

## Automated checks

```bash
.venv/bin/python -m pytest
# result: 52 passed
```

```bash
.venv/bin/python -m ruff check .
# result: All checks passed
```

## Known limits

- Replay is intentionally conservative. It automates local packaging-style runs first and refuses unsupported generation replay instead of spending credits unexpectedly.
- Full interactive cost prompts are represented by `shared.cost.evaluate_cost`; broad prompt UX remains intentionally conservative.

## Sign-off

- [x] Phase implementation accepted
- [x] Safe to continue to Phase 15
