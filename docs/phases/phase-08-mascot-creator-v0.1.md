# Phase 08: `mascot-creator` v0.1

Master mascot generation only. Type/preset taxonomy fully working. No variants yet.

## Goal

`> /mascot-creator "wise old owl, professor" --type stylized --preset 3d-toon` produces a clean master image of the character. Each type/preset combo is visually distinct and on-style.

## Deliverables

### Skill folder

```
skills/mascot-creator/
├── SKILL.md
├── scripts/
│   └── generate.py
└── tests/
    └── test_generate.py
```

### Preset content

```
shared/presets/mascot_styles.yaml          # full type × preset matrix
shared/presets/prompt_templates/mascot-creator/
├── _default.j2
├── stylized/
│   ├── flat-vector/master.j2
│   ├── cartoon-2d/master.j2
│   ├── chibi-kawaii/master.j2
│   ├── 3d-toon/master.j2
│   ├── mascot-corporate/master.j2
│   ├── sticker-style/master.j2
│   └── low-poly/master.j2
├── realistic/
│   ├── photoreal-2d/master.j2
│   ├── photoreal-3d/master.j2
│   ├── hyperreal/master.j2
│   ├── documentary/master.j2
│   └── portrait/master.j2
└── artistic/
    ├── watercolor/master.j2
    ├── pencil-sketch/master.j2
    ├── pixel-art/master.j2
    ├── painterly/master.j2
    ├── line-art/master.j2
    ├── ink-wash/master.j2
    └── chalk/master.j2
```

(17 preset templates total)

### `generate.py`

- Args: `--description`, `--type`, `--preset`, `--personality`, `--variants`, `--model`, `--seed`
- AskUserQuestion (or stdin prompt) when `--type` missing — "Stylized, realistic, or artistic?"
- Builds prompt from preset template
- Calls `openrouter_client` with the preset's primary model
- Multi-shot (default 3 variants)
- Quality validator with `mascot-master` profile (looser than `app-icon` profile)
- Picks best, saves master + variants

## Implementation steps

1. Author `mascot_styles.yaml` with all 17 presets and their model assignments (per [docs/presets/mascot-types.md](../presets/mascot-types.md))
2. Author all 17 master prompt templates
3. Snapshot tests for every preset
4. Implement `generate.py`:
   - Input parsing with type-required check
   - AskUserQuestion fallback for missing type
   - Use prompt_builder
   - Use openrouter_client with multi-shot
   - Use quality_validator with mascot-master profile (just non-empty + transparent_bg, looser than icon profiles)
5. Per-preset by-eye review: 17 mascots, same description ("a fox character"), one per preset, side-by-side

## Acceptance criteria

### Automated
- All 17 snapshot tests pass
- For each preset: smoke test produces valid PNG, validator passes
- Missing-type case raises `InputError` (or invokes AskUserQuestion in interactive contexts)

### Manual / by-eye
- 17-mascot comparison sheet for the same description
- Each preset visibly distinct from others
- Each preset matches its description in [mascot-types.md](../presets/mascot-types.md)
- Specifically:
  - `stylized/3d-toon` is clearly Pixar-like 3D, not photoreal
  - `realistic/photoreal-3d` is clearly CGI, not 2D
  - `artistic/watercolor` shows visible washes and texture
  - `artistic/pixel-art` is blocky 8-bit / 16-bit
- No prompt overlaps so much that two distinct presets produce indistinguishable output

### Documentation
- SKILL.md complete
- README explains type/preset choice with examples

## Test in OpenCode

```
> /mascot-creator "a curious otter holding a flower" --type stylized --preset chibi-kawaii
```

Confirm:
- Output is chibi style (oversized head, pastel)
- Subject is recognizably an otter holding a flower
- Master + variants produced

```
> /mascot-creator "wise dragon"
... should ask: Stylized, realistic, or artistic?
> stylized
... should ask preset (or use default flat-vector)
> mascot-corporate
```

Confirm interactive flow works.

## Out of scope for phase 08

- Multi-view / character sheet (phase 09)
- Pose / expression variants (phase 10)
- Outfit variants (phase 11)
- Style-guide.md generation (phase 11)
- Reference image input (planned but pushed; basic vision_analyzer.analyze_style is available, but trait extraction for character anchoring comes in phase 09-10)

## Risks

- **Some presets may underperform on chosen primary model.** If `realistic/hyperreal` looks weak on Flux, we re-check the model assignment after by-eye review.
- **17 templates is a lot of snapshot tests.** Authored carefully; CI has reasonable runtime.
- **AskUserQuestion availability varies by harness.** Provide stdin fallback for non-interactive environments.

## Dependencies on prior work

- Phases 00–02 (shared infra, prompt builder, vision analyzer, presets)
- Phase 03 (multi-shot + validator pattern)
