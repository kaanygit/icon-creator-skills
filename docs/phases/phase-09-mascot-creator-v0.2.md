# Phase 09: `mascot-creator` v0.2 — character sheet (multi-view)

Add multi-view character sheet generation: front, side, three-quarter, back. First real consistency challenge — the same character must look the same from different angles.

## Goal

`--views front,side,3-quarter,back` produces four images of the same character from those angles, with a composed `character-sheet.png` showing them in a grid. Visual identity (palette, proportions, distinguishing features) preserved across all views.

## Deliverables

### New shared functionality

- `shared/vision_analyzer.extract_character_traits` — vision LLM call that produces a structured `CharacterTraits` (palette, distinguishing features, accessories, art-style descriptor, anchor_text)
- `shared/consistency_checker` — first real use; gates view variants

### New prompt templates

For every preset, add a `view-variant.j2` template:

```
shared/presets/prompt_templates/mascot-creator/{type}/{preset}/view-variant.j2
```

Total: 17 new templates.

### Updated skill

- `generate.py` accepts `--views`
- After master picked, runs trait extraction
- For each view, runs prompt with `anchor_traits.anchor_text` prepended; uses image-to-image where the model supports it
- Validates each view with `consistency_checker` against the master
- Composes `character-sheet.png` grid
- Saves views to `views/{view-name}.png`

## Implementation steps

1. Implement `vision_analyzer.extract_character_traits` (LLM call with structured output schema)
2. Implement `consistency_checker` per [docs/shared/consistency-checker.md](../shared/consistency-checker.md):
   - Color palette histogram similarity
   - Edge density similarity
   - Perceptual hash distance
   - Subject overlap
   - Face-region similarity (when faces detected)
3. Author 17 view-variant templates (using anchor injection pattern)
4. Update `generate.py`:
   - After master selection: call `extract_character_traits`
   - For each view: build prompt with anchor, call openrouter_client with i2i if supported
   - Validate each via consistency_checker (threshold 0.80)
   - Retry up to 3 per view
5. Implement grid composition (`image_utils.compose_grid` with labels)
6. Tests with synthetic / real fixtures: confirm character traits extraction produces sensible output, view variants pass consistency thresholds at acceptance rates ≥ 70% on first attempt

## Acceptance criteria

### Automated
- Snapshot tests for all 17 view-variant templates
- End-to-end: generate a master + 4 views, all view-files exist, character-sheet.png composed correctly
- Consistency checker scores logged per view; if all variants for a view fail after 3 retries, surface clearly

### Manual / by-eye
- 5+ end-to-end runs across different presets
- For each: confirm side / 3-quarter / back are recognizably the same character as the front master
- Specific failure modes to catch:
  - Color drift (palette changed)
  - Proportion drift (different body shape)
  - Feature drift (lost/added accessory)
- Acceptable: minor stylistic variation; the character is clearly the same person/animal/thing
- Unacceptable: looks like a different character

### Documentation
- SKILL.md mentions `--views` argument and what views are valid
- README example showing character sheet output

## Test in OpenCode

```
> /mascot-creator "wise old owl, professor, glasses" \
                  --type stylized --preset 3d-toon \
                  --views front,side,3-quarter,back
```

Confirm:
- Four view files in `views/`
- `character-sheet.png` composed grid
- All four show recognizably the same owl with glasses
- Glasses persist across views (not just on the front)

## Out of scope for phase 09

- Pose variants (phase 10)
- Expression variants (phase 10)
- Outfit variants (phase 11)
- Pose × expression matrix (phase 11)
- Style-guide.md generation (phase 11)

## Risks

- **R-001: Character consistency is the hard problem.** 70% first-attempt pass rate is the working target; below that, variants need manual user picks, which is a UX issue we'll tune in phase 10.
- **`extract_character_traits` LLM call may produce inconsistent output.** Use structured-output mode (JSON schema) to constrain.
- **Image-to-image not available on every model.** Fallback strategy: detailed text-only prompt with anchor_text + locked seed. Quality is lower but still useful.

## Dependencies on prior work

- Phase 08 (mascot-creator master)
- Phase 02 (vision_analyzer partial; phase 09 extends it)
