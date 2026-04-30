# Phase 10: `mascot-creator` v0.3 — poses + expressions

The hardest phase. Add pose and expression variant generation. Character consistency must hold across pose changes and facial-expression changes simultaneously.

## Goal

```
--poses idle,waving,thinking,celebrating
--expressions happy,sad,surprised,angry
```

produces:
- Four pose variants (each: same character, different pose, neutral expression)
- Four expression variants (each: same character, idle pose, different expression)

All recognizable as the same character. Consistency check threshold: 0.85.

## Deliverables

### New prompt templates

Per preset, add:
- `pose-variant.j2`
- `expression-variant.j2`

That's 17 × 2 = **34 new templates**.

### Skill updates

- `generate.py` accepts `--poses` and `--expressions` lists
- After master + view phase, runs pose loop, then expression loop
- Each variant uses image-to-image with master as reference (where supported)
- Each variant validated via consistency_checker (threshold 0.85, higher than views)
- Best-of-N retry for failures (default N=3, overridable via `--best-of-n`)

### New: best-of-N module

A small wrapper inside `generate.py`:
```python
def best_of_n(generate_fn, validate_fn, n=3, threshold=0.85):
    candidates = [generate_fn() for _ in range(n)]
    scored = [(c, validate_fn(c)) for c in candidates]
    scored.sort(key=lambda x: x[1].combined_score, reverse=True)
    if scored[0][1].combined_score >= threshold:
        return scored[0]
    # surface best with warning
    return scored[0]
```

## Implementation steps

1. Author 34 templates (pose-variant and expression-variant per preset)
2. Snapshot tests for all 34
3. Update `generate.py`:
   - After views complete (phase 09 path), run pose loop
   - For each pose: build prompt with `anchor_traits.anchor_text` + variant_kind=pose + variant_value=pose_name
   - Call openrouter with i2i + master image
   - Apply consistency_checker
   - Best-of-N if first fails, up to 3 attempts
   - Save to `poses/{pose-name}.png`
4. Same flow for expressions, save to `expressions/{expression-name}.png`
5. Update metadata.json schema to record per-variant scores and retry counts
6. Visual review: 3+ end-to-end runs with full pose+expression sets, manually rate consistency

## Acceptance criteria

### Automated
- 34 snapshot tests pass
- End-to-end: master + 4 poses + 4 expressions = 9 image files all exist
- Per-variant consistency scores logged
- At least 70% of pose/expression variants pass on first attempt across the test corpus

### Manual / by-eye

This is the most important phase for human review.

For 5 different mascots, generate 4 poses + 4 expressions each. For each:

1. **Identity preservation**: subject is recognizably the same character as the master
2. **Pose accuracy**: the pose label is what the image shows (waving = visible wave gesture)
3. **Expression clarity**: the expression label matches the face (happy = visible smile)
4. **No drift**: palette, proportions, distinguishing features (glasses, accessories) preserved

Score each axis 1-5; aim for average ≥ 4.0 across the corpus.

If less than 4.0:
- Tune anchor_text construction
- Tune consistency_checker weights (face_similarity may need higher weight)
- Tune retry strategies

### Documentation
- SKILL.md complete with all variant args
- README has a worked example with output preview

## Test in OpenCode

```
> /mascot-creator "wise old owl, professor, glasses" \
                  --type stylized --preset 3d-toon \
                  --poses idle,waving,thinking,celebrating \
                  --expressions happy,sad,surprised
```

Confirm:
- Output directory has master + views/ (if also requested) + poses/ + expressions/
- Every pose/expression variant recognizably the same owl
- Glasses persist across all variants
- Consistency report logs scores per variant

## Out of scope for phase 10

- Outfit variants (phase 11)
- Pose × expression matrix (phase 11)
- Style-guide.md output (phase 11)
- Adding new variants to existing mascot (post-v1)

## Risks

- **R-001: This phase is where the hard consistency problem lives.** If the working 0.85 threshold is hit by < 60% of variants on first attempt, we have a quality problem and may need:
  - Different model for variant generation (e.g. switch to Flux Redux specifically for variants)
  - Stronger anchor descriptions
  - Longer retry chains
  - Honest user-facing message: "consistency is hard, here are best attempts"
- **Cost balloons here.** 4 poses × 4 expressions × 3 best-of-N candidates = up to 48 calls per master. Mandatory pre-run cost confirmation; the user should see "this run will cost ~$1.50" before it starts.
- **OpenRouter image-to-image availability shifts.** Track per-model capability in `openrouter_models.yaml`.

## Dependencies on prior work

- Phase 09 (extract_character_traits, consistency_checker, view-variant templates as the pattern)
- Phase 03 (multi-shot, validation, retry patterns)
