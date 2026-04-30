# Phase 03: `icon-creator` v0.3

Multi-shot generation, quality validator, retry logic with prompt augmentation, iteration mode. Brings `icon-creator` to production-grade reliability.

## Goal

Three things must work together:
1. Each call defaults to producing 3 variants and auto-picks the best
2. The quality validator gates results and triggers smart retries on failure
3. `--refine path/to/master.png` runs an image-to-image-or-equivalent refinement on a previous output

## Deliverables

### New shared modules

- `shared/quality_validator.py` (per [docs/shared/quality-validator.md](../shared/quality-validator.md))
- `shared/openrouter_client` extended with `n` parameter (multi-shot batching) and image-to-image where the model supports it

### Updated skill

- `generate.py` defaults `variants=3`, supports `--variants N`, `--refine path`, `--seed N`
- `metadata.json` records all variants, validation results per variant, picked variant
- `preview.png` grid auto-generated showing all variants

## Implementation steps

1. Implement `quality_validator` with all profile checks (transparent_bg, square_aspect, centered, readable_at_16px, contrast, non_empty, no_text_artifacts)
2. Tune thresholds with a hand-curated set of "good" and "bad" outputs (collect during phases 01 and 02)
3. Extend `openrouter_client` to:
   - Generate N images in one call (where the model API supports it; otherwise loop)
   - Support image-to-image when the chosen model exposes it
4. Wire `generate.py` to:
   - Generate `variants` candidates
   - Validate each
   - Pick best (highest combined score that passes required checks; fallback to highest score)
   - If no variant passes, run augmented-prompt retry (see [retry-validation.md](../quality/retry-validation.md))
   - Save all variants to `variants/`, copy best to `master.png`
   - Generate `preview.png` grid via `image_utils.compose_grid`
5. Implement `--refine`:
   - Load metadata.json from the referenced run (sibling to the path)
   - Reconstruct the prompt
   - If `--description` also provided, append as refinement instruction
   - Run image-to-image with the chosen variant as reference
   - Output to a new run dir tagged as refinement-of
6. Tests: validator unit tests, end-to-end multi-shot test, refinement test

## Acceptance criteria

### Automated
- Validator unit tests cover every check with synthetic positive and negative fixtures
- End-to-end test: generate 3 variants for "fox", validate, pick, verify `master.png` exists and passes all required checks (or marked best-attempt with warning)
- Refinement test: refine a known-good master, confirm output run dir created with `refinement_of` field set

### Manual / by-eye
- Generate 5 different icons across presets, eyeball that auto-pick chose the visually-best variant in each case (validator score correlates with human judgment)
- Force a failure case (e.g. ask for an icon with text in the description, validator should catch the text artifact)
- Run `--refine` on a previous output with a description like "more minimal" and confirm the result is a recognizable variation of the original

### Documentation
- Update SKILL.md with new arguments
- Add `--variants`, `--refine`, `--seed` examples to README

## Test in OpenCode

```
> /icon-creator "fox" --variants 3
```

Confirm:
- Three variants visible in `variants/` directory
- `preview.png` grid showing all three
- One of them promoted to `master.png` based on validation score
- Output path of master + variants directory printed

```
> /icon-creator --refine output/fox-{prev-ts}/master.png "more geometric"
```

Confirm:
- New run dir created
- `refinement_of` field set in metadata.json
- Output is recognizably a variation of the original, with the requested change applied

## Out of scope for phase 03

- Cost-estimate confirmation prompts (phase 14)
- Multi-shot for `icon-set-creator` (phase 13)
- Multi-shot for `mascot-creator` (phases 08-11)
- `--interactive` mode for user-driven variant selection (phase 14)

## Risks

- **Validator thresholds may need tuning after first real-world use.** Document threshold values in `defaults.yaml`; iterate based on user feedback.
- **Models with no native image-to-image** force prompt-only refinement. Document this limitation; auto-detect from `openrouter_models.yaml`.
- **Augmented-prompt retries can occasionally make things worse** (over-correction). Cap retries at the documented limits.

## Dependencies on prior work

- Phase 00 (openrouter_client, image_utils, config)
- Phase 01 (skill scaffold)
- Phase 02 (prompt_builder, presets, vision_analyzer partial)
