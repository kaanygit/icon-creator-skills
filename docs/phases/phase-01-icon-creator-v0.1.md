# Phase 01: `icon-creator` v0.1

The first real skill. Single-shot icon generation, no presets, no reference image, no validation, no packaging. The minimum viable icon producer.

## Goal

`> /icon-creator "minimalist mountain"` produces a usable PNG icon. The skill installs and runs in Claude Code AND in OpenCode.

## Deliverables

### Skill folder

```
skills/icon-creator/
├── SKILL.md                    # frontmatter + instructions for the agent
├── scripts/
│   └── generate.py             # the actual Python entrypoint
└── tests/
    └── test_generate.py
```

### `SKILL.md` (Claude Code format)

```markdown
---
name: icon-creator
description: Generate a single icon (app icon, favicon, UI icon) from a text description.
---

# icon-creator

Use this skill when the user asks to create an icon, app icon, favicon, or logo-mark.

## How to invoke
Call `python skills/icon-creator/scripts/generate.py --description "<user's description>"`.

The script prints the path to the generated master.png on the last line of stdout.
```

(Add `model:` frontmatter if needed for Claude Code's spec; minimal here.)

### `generate.py`

A small CLI that:
1. Parses args (`--description`, `--output-dir`, `--model`)
2. Builds a basic prompt: `"{description}, app icon, centered, transparent background, square, no text"`
3. Calls `shared.openrouter_client.generate(...)`
4. Saves the result to `output/{slug}-{ts}/master.png`
5. Writes minimal `metadata.json`
6. Prints the master path

No presets, no variants, no validation, no retries beyond the transport-level retries inherited from `openrouter_client`.

## Implementation steps

1. Create `skills/icon-creator/` folder structure
2. Write SKILL.md (Claude Code format)
3. Write `generate.py`:
   - argparse for inputs
   - Basic prompt assembly (hardcoded template, no Jinja yet)
   - Slug from description (hyphenated, ≤30 chars)
   - Call `openrouter_client.generate(model="google/gemini-3-pro-image-preview", prompt=..., n=1)`
   - Save image, write metadata.json, print master path
4. Add a smoke test in `skills/icon-creator/tests/`
5. Manually test in Claude Code
6. Manually test in OpenCode (verify SKILL.md format compatibility)

## Acceptance criteria

### Automated
- `python skills/icon-creator/scripts/generate.py --description "fox"` exits 0
- Output file exists, is PNG, is square ≥ 1024×1024
- `metadata.json` exists with required fields

### Manual / by-eye
- Run `> /icon-creator "minimalist mountain"` in Claude Code
- Run `> /icon-creator "minimalist mountain"` in OpenCode (or equivalent invocation)
- Both produce a recognizable icon
- Output paths printed to chat correctly

### Documentation
- README of `skills/icon-creator/` (mini, ~30 lines) explaining how to invoke

## Test in OpenCode

Procedure:

1. Install the skill in OpenCode following its skill-install convention (we'll document the exact command in `docs/install.md`)
2. In an OpenCode chat: `/icon-creator "cute fox"`
3. Confirm the agent ran the skill, the script executed, an icon was produced
4. Confirm the icon file path printed in the response is real and openable

If any step fails, capture exact error and we fix before phase 02.

## Out of scope for phase 01

- Style presets (phase 02)
- Reference image input (phase 02)
- Multi-shot variants (phase 03)
- Quality validator (phase 03)
- Iteration / refinement (phase 03)
- Packaging (phase 04)
- Vectorization (phase 06)

## Risks for this phase

- **R-006**: We must verify the API key is read from env, not exposed in args or logs (already enforced by `openrouter_client`)
- **R-012**: SKILL.md format compatibility between Claude Code and OpenCode — this phase explicitly tests both

## Dependencies on prior work

- Phase 00 must be complete (`openrouter_client` exists and works)
