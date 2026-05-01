# Phase 10 acceptance

## Phase

- Phase: 10
- Commit: this commit
- Date: 2026-05-01
- Reviewer: kaanygit / Codex
- Environment: macOS, zsh, Python 3.14.4 in local `.venv`

## Scope completed

- [x] Pose-variant prompt templates added for all mascot presets.
- [x] Expression-variant prompt templates added for all mascot presets.
- [x] `--poses` and `--expressions` CLI support added.
- [x] Pose outputs saved under `poses/`.
- [x] Expression outputs saved under `expressions/`.
- [x] `--best-of-n` retry selection added.
- [x] Per-variant consistency scores, attempts, and pass/fail state recorded in `metadata.json`.

## Automated checks

```bash
.venv/bin/python -m pytest skills/mascot-creator/tests/test_generate.py shared/tests/test_vision_analyzer.py
# result: 7 passed
```

```bash
.venv/bin/python -m ruff check skills/mascot-creator shared
# result: All checks passed
```

## Cost control

- [x] Tests use a fake image client.
- [x] Live smoke testing should use `--variants 1 --best-of-n 1` unless the user approves broader fan-out.

## Sign-off

- [x] Phase implementation accepted
- [x] Safe to continue to Phase 11
