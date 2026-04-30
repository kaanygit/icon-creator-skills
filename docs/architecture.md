# Architecture

This document describes the high-level system design: how skills compose, how shared modules fit in, where data flows, and what each layer is responsible for.

## Top-down view

```
┌────────────────────────────────────────────────────────────────────────┐
│                       Agent harness (Claude Code / OpenCode)           │
│                                                                        │
│   user prompt ──▶ skill router ──▶ chosen skill SKILL.md               │
└────────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌────────────────────────────────────────────────────────────────────────┐
│                            Skill layer (6 skills)                      │
│                                                                        │
│   icon-creator ─┐                                                      │
│   icon-set-creator ─┐                                                  │
│   mascot-creator ─┼──── orchestrate flows, own user-facing UX ──┐      │
│   png-to-svg ──────┤                                            │      │
│   app-icon-pack ───┤                                            │      │
│   mascot-pack ─────┘                                            │      │
└─────────────────────────────────────────────────────────────────│──────┘
                                                                  │
                                  ┌───────────────────────────────┘
                                  ▼
┌────────────────────────────────────────────────────────────────────────┐
│                          Shared module layer                           │
│                                                                        │
│   openrouter_client     vision_analyzer     prompt_builder             │
│   image_utils           consistency_checker quality_validator          │
└────────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌────────────────────────────────────────────────────────────────────────┐
│         External: OpenRouter API   ·   local image processing libs     │
└────────────────────────────────────────────────────────────────────────┘
```

## Layer responsibilities

### Skill layer

Each skill is a self-contained unit with:

- A `SKILL.md` (frontmatter + instructions for the agent)
- A small Python entrypoint script
- Knowledge of its own user-facing flow (what to ask, what to return)
- **No direct dependencies on other skills** — composition happens through the agent layer or by importing shared modules, never by importing another skill's internals

A skill can call another skill as a downstream step (e.g. `icon-creator` finishes a master, then invokes `app-icon-pack` if the user asked for assets). The mechanism is the agent invoking the next skill, not Python imports across skill boundaries.

### Shared module layer

Pure Python. No skill UX. No prompt strings. Just primitives:

- `openrouter_client` — single source of truth for talking to OpenRouter, retry logic, cost tracking
- `vision_analyzer` — wraps a vision model call to extract style / palette / composition from a reference image
- `prompt_builder` — template engine, preset injection, negative-prompt assembly
- `image_utils` — resize, crop, padding, background removal, format conversions
- `consistency_checker` — compare two images for stylistic similarity (color histogram, edge density, perceptual hash)
- `quality_validator` — readability at small sizes, contrast checks, centering checks

Every skill imports from `shared/`. There is no copy-pasted utility code.

### Presets

Stored as YAML in `shared/presets/`. Editable without touching Python. Schema is documented in [docs/presets/](presets/).

- `icon_styles.yaml` — flat, gradient, glass-morphism, outline, 3d-isometric, skeuomorphic, neumorphic, material, ios-style
- `mascot_styles.yaml` — three-tier: type (stylized / realistic / artistic) → preset (~17 total)
- `prompt_templates/` — Jinja-style templates per skill × preset combination

## Data flow: a single icon-creator call

```
user prompt
  │
  ▼
parse inputs, fill defaults via AskUserQuestion if needed
  │
  ▼
[reference image present?] ───yes───▶ vision_analyzer ─▶ style hints
  │ no                                                       │
  └──────────────────┬────────────────────────────────────────┘
                     ▼
prompt_builder.build(type, preset, hints, description)
  │
  ▼
openrouter_client.generate(model, prompt, n=variants)
  │
  ▼
image_utils: bg removal → auto-crop → square + pad
  │
  ▼
quality_validator: pass / retry / hand back
  │
  ▼
write output/{slug}/master.png + variants/ + metadata.json
  │
  ▼
[user opted into packaging?] ───yes───▶ invoke app-icon-pack
```

Every step is observable. Every step writes to disk before the next one starts, so partial failures are recoverable and the user can see intermediate state.

## Storage layout (per run)

```
output/
└── {slug}-{YYYYMMDD-HHMMSS}/
    ├── master.png
    ├── master.svg                # if png-to-svg ran
    ├── variants/
    │   ├── 1.png
    │   ├── 2.png
    │   └── 3.png
    ├── metadata.json              # prompt, model, seed, cost, timestamp
    ├── prompt-debug.txt           # full prompt + negative prompt for inspection
    └── logs/
        ├── openrouter.log
        └── validator.log
```

Mascot runs add `character-sheet.png`, `poses/`, `expressions/`, `outfits/`. Pack runs add platform subdirectories.

## Configuration

Three layers, in increasing priority:

1. **Skill defaults** — hardcoded sensible defaults
2. **User config** — `~/.icon-skills/config.yaml` (default model, default style, OpenRouter key location)
3. **Project config** — `.iconrc.json` in project root (brand palette, default style, default platforms)
4. **Per-call args** — anything the user passes overrides everything

OpenRouter API key is **never** stored in any of these files. It comes from `OPENROUTER_API_KEY` env var or, optionally, a path in user config that points to a key file.

## Extensibility points

- **New style preset** — add to YAML, write a prompt template, no Python changes
- **New platform** — add to `docs/platforms/{platform}.md`, drop a size table in `shared/presets/platforms/{platform}.yaml`, register in `app-icon-pack`
- **New image-gen backend** — implement the `ImageBackend` protocol next to `openrouter_client`. Out of scope for v1 but the seam is intentional.
- **New skill** — drop a folder under `skills/`, follow the SKILL.md contract, import from `shared/`

## What is intentionally not abstracted

- **The skill ↔ harness contract**. We use Claude Code's SKILL.md format directly. If OpenCode (or any other harness) needs adjustments, those are skill-specific tweaks, not a portability layer.
- **The prompt templates**. They're versioned files, not generated. Designer prompts are the product.
- **The asset size tables**. Hardcoded YAML. Apple changes these maybe once a year; tracking upstream is a release-cadence problem, not a runtime problem.
