# Phase 16: Documentation

Comprehensive user-facing documentation. By the end of this phase, a new user can install, run their first skill, and ship to App Store / Play Store / web without leaving the docs.

## Goal

Documentation that gets a new user from zero to first useful icon in under 5 minutes, and supports them through the harder workflows (mascot consistency, brand kits, custom presets) without dropping into source code.

## Workstreams

### 1. README at repo root

Already exists (created in phase 0 of the plan docs); this phase polishes it:
- Quick start (5-minute path)
- Install instructions per OS
- The 6 skills with one-line descriptions and links
- Environment setup (`OPENROUTER_API_KEY`)
- Link to docs/

### 2. Per-skill README

Each `skills/<skill>/README.md`:
- One-paragraph what-it-does
- All inputs with types and defaults
- 3 worked examples (basic, intermediate, advanced)
- Common gotchas
- Cost expectations
- Link to spec doc

### 3. `docs/install.md`

- Python version requirement
- pyproject install (`pip install .` from clone, OR `pip install icon-creator-skills` once published)
- Native deps per platform (Cairo, potrace, optional)
- `rembg` model download note (lazy, first use)
- Skill installation in Claude Code
- Skill installation in OpenCode
- Verification: `icon-skills doctor`

### 4. `docs/getting-started.md`

A walkthrough of the first ten minutes:
1. Install (link to install.md)
2. Set OPENROUTER_API_KEY
3. Generate your first icon
4. Generate variants
5. Package for iOS
6. (optional) Set up `.iconrc.json`
7. Generate your first mascot

Each step has the exact command and expected output.

### 5. `docs/troubleshooting.md`

Common issues:
- "OPENROUTER_API_KEY not set" — fix
- "Model not found" — fallback / model migration
- "rembg model download failed" — manual download instructions
- "cairo library not found" — platform install commands
- "Mascot variants don't look like the master" — see consistency tuning advice
- "App Store rejected my icon" — common causes (alpha on marketing icon, wrong sizes)
- "Adaptive icon clipping" — safe-zone explanation

### 6. `docs/recipes.md`

Cookbook patterns:
- "Generate a coherent 12-icon navigation set"
- "Build a brand mascot with full pose and expression coverage"
- "Replace an existing app icon end-to-end"
- "Add a new icon to a previously generated set"
- "Iterate on a mascot's outfit without re-generating poses"
- "Reuse a saved style across multiple projects"

### 7. Visual examples

A `docs/examples/` directory (mostly markdown + linked image assets):
- 5+ complete worked examples with their prompts, settings, and output previews
- Side-by-side preset comparisons (1 description × 9 icon presets, 1 description × 17 mascot presets)
- A "before / after" showing pre-skill and post-skill cost / time

### 8. Contributing guide

`CONTRIBUTING.md`:
- Development setup
- Running tests
- Snapshot test workflow (templates)
- Submitting a new preset
- Code style (ruff)
- PR review expectations

### 9. Changelog

`CHANGELOG.md` starting at 0.1.0 documenting the journey through phase 0–17.

## Implementation steps

1. Polish root README.md (verify all links, add Quick Start)
2. Write `docs/install.md` (verified against the cross-platform CI matrix in phase 15)
3. Write `docs/getting-started.md` walkthrough
4. Write `docs/troubleshooting.md` with all known errors and fixes
5. Write `docs/recipes.md` with 6+ patterns
6. Generate visual examples (run skills against curated prompts; commit outputs as small PNGs)
7. Write `CONTRIBUTING.md`
8. Write `CHANGELOG.md`
9. Per-skill README review and rewrite where needed

## Acceptance criteria

### Automated
- All in-doc links resolve
- All commands shown in docs are real (tested in CI smoke tests where possible)

### Manual
- A non-author runs through `getting-started.md` from a clean machine; reaches "first packaged icon" without consulting source code
- The "1 description × 9 icon presets" comparison sheet is visible and on-style for each preset
- The mascot 17-preset comparison sheet is visible and on-style for each preset
- Contributing guide gets a non-author through "submit a new preset PR" workflow

### Documentation completeness
- Every flag mentioned in any SKILL.md is documented in the corresponding skill README
- Every shared module has a doc in `docs/shared/`
- Every preset is in the catalog
- Every phase document references its predecessor and successor

## Test in OpenCode

The docs themselves don't need OpenCode testing, but the recipes do — every recipe should be runnable in OpenCode end-to-end. Phase 16 acceptance includes running each recipe in OpenCode and confirming the documented commands and outputs match reality.

## Out of scope for phase 16

- Video tutorials / GIFs (post-v1; nice-to-have)
- Localized docs (post-v1)
- Hosted docs site (we ship as repo markdown initially; GitHub Pages or Read the Docs is post-v1)

## Dependencies on prior work

- Phases 1–14 (every feature documented must exist)
- Phase 15 (troubleshooting needs the doctor command and tuned error messages)
