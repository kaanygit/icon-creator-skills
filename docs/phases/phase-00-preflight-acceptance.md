# Phase 00-preflight acceptance

## Phase

- Phase: 00-preflight
- Commit: pending at time of writing
- Date: 2026-05-01
- Reviewer: kaanygit / Codex
- Environment: local docs repository, macOS, zsh

## Scope completed

- [x] Preflight phase doc added.
- [x] Model matrix added under `docs/presets/model-matrix.md`.
- [x] OpenRouter client spec updated with current image-generation request/response shape.
- [x] Phase 00 skeleton doc now depends on preflight and defines model YAML expectations.
- [x] Acceptance template added for later phases.
- [x] Stale default fallback references removed from regular docs; retired references remain only in the model matrix/preflight warning.

## Automated checks

```bash
rg -n "openai/dall-e-3|flux-1\.1-pro|flux-redux|stability-ai/stable-diffusion-3\.5" docs README.md CLAUDE.md
# result: only intentional retired/unavailable references remain in phase-00-preflight.md and model-matrix.md
```

```bash
git status --short
# result: documentation changes pending commit
```

## Manual checks

- [x] Official OpenRouter image-generation documentation checked.
- [x] OpenRouter model matrix now points implementation to model discovery instead of stale hardcoded assumptions.
- [x] Phase index includes preflight before implementation Phase 00.

## OpenCode / harness check

- Required for this phase: no
- Command or invocation: n/a
- Result: n/a
- Notes: no executable skill exists yet.

## Known issues

- Final pricing values are not locked in this phase. Phase 00 must create the pricing YAML from current OpenRouter data and mark unknown pricing explicitly.
- `black-forest-labs/flux.2-flex` remains a candidate until live visual tests prove value.

## Sign-off

- [x] Phase accepted
- [x] Safe to start Phase 00
