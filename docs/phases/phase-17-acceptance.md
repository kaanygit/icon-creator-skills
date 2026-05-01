# Phase 17 acceptance

## Phase

- Phase: 17
- Commit: this commit
- Date: 2026-05-01
- Reviewer: kaanygit / Codex
- Environment: macOS, zsh, Python 3.14.4 in local `.venv`

## Scope completed

- [x] `pyproject.toml` version bumped to `1.0.0`.
- [x] `icon-skills` console script registered.
- [x] Package data includes JSON schema files.
- [x] GitHub issue and PR templates added.
- [x] `ROADMAP.md` added for post-v1 work.
- [x] Release changelog added.
- [x] No PyPI publish was attempted from this agent session.

## Automated checks

```bash
.venv/bin/python -m pytest
# result: 52 passed
```

```bash
.venv/bin/python -m ruff check .
# result: All checks passed
```

## Release note

This is a repo-level v1.0.0 release candidate. Actual PyPI publishing, GitHub Release creation, and marketplace submissions remain manual owner actions.

## Sign-off

- [x] Phase implementation accepted
- [x] v1.0.0 release candidate ready
