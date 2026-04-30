# Phase 02: `icon-creator` v0.2

Add the 9 style presets and reference-image input. Brings prompt construction up to production-quality and lets users steer the result with a reference.

## Goal

Every style preset declared in [docs/presets/icon-styles.md](../presets/icon-styles.md) produces visibly distinct, on-style outputs. Reference-image input measurably influences the result.

## Deliverables

### New shared modules

- `shared/prompt_builder.py` (per [docs/shared/prompt-builder.md](../shared/prompt-builder.md))
- `shared/vision_analyzer.py` partial: palette extraction + style-hint LLM call (full feature set in later phases)

### Preset content

- `shared/presets/icon_styles.yaml` — all 9 presets with primary/fallback models, style phrases, negative extras
- `shared/presets/prompt_templates/icon-creator/` — Jinja templates for each preset and `_default.j2`

### Updated skill

- `generate.py` accepts `--style-preset`, `--colors`, `--reference-image`
- Uses `prompt_builder` instead of hardcoded prompt
- Uses `vision_analyzer.analyze_style()` when reference image provided

## Implementation steps

1. Implement `prompt_builder` with Jinja-based template loading
2. Author all 9 templates (`flat`, `gradient`, `glass-morphism`, `outline`, `3d-isometric`, `skeuomorphic`, `neumorphic`, `material`, `ios-style`)
3. Snapshot tests for every (skill, preset) combo
4. Implement `vision_analyzer` partial:
   - `extract_palette` (local, k-means in LAB)
   - `analyze_style` (LLM call — multimodal)
5. Wire `generate.py` to use prompt_builder; thread reference hints into the prompt context
6. Per-preset visual review: generate one icon per preset for the same description, lay out side-by-side, confirm each looks distinctly on-style

## Acceptance criteria

### Automated
- All snapshot tests pass
- For each preset, smoke test generates a non-empty PNG
- `--reference-image` does not crash; vision_analyzer returns palette + descriptor

### Manual / by-eye
- 9 reference comparison sheets, one per preset, generated for the same input description ("a mountain")
- Each preset is **visibly different** from the others
- Each preset matches its catalog description (e.g. `flat` is flat, `glass-morphism` looks glassy)
- Reference-image test: provide an image with strong palette/style, confirm output palette aligns

### Documentation
- Update SKILL.md to mention preset and reference-image arguments
- Add example invocations to `skills/icon-creator/README.md`

## Test in OpenCode

```
> /icon-creator "rocket" --style-preset 3d-isometric
```

Confirm:
- Output is isometric-3D-look, not flat
- Generated path printed, file openable

```
> /icon-creator "lighthouse" --reference-image ./brand/style-ref.png
```

Confirm:
- Output palette overlaps the reference's palette
- Output art-style is in the spirit of the reference

## Out of scope for phase 02

- Multi-shot (phase 03)
- Quality validator (phase 03)
- Iteration / `--refine` (phase 03)
- Cost estimation prompts (phase 03 introduces basic; phase 14 polishes)
- `vision_analyzer` brand-similarity warnings (phase 14)

## Risks

- **Snapshot tests need re-baselining when templates change.** Document this in CONTRIBUTING.
- **Vision LLM cost on every reference call.** Cache by file hash within a session.
- **Some presets may not work well with the chosen primary model.** Adjust model assignments after by-eye review.
