# Phase 07: `png-to-svg` v0.2

Add `potrace` and `imagetracer`, implement `algorithm: auto` selection, harden the suitability check.

## Goal

`> /png-to-svg --input some.png` (with no `--algorithm` argument) picks the right algorithm based on the input characteristics. Photo inputs get refused unless `--force` is passed. Each algorithm produces output that is best-in-class for its input type.

## Deliverables

### Updated skill

- `vectorize.py` adds `--algorithm potrace|imagetracer|auto`
- Algorithm-specific subroutines for each
- Full suitability check producing `{good, marginal, poor}` classification

### Dependencies

- `pypotrace` or `potrace` system binary (auto-detect)
- `imagetracerpy` (Python port of imagetracer)

## Implementation steps

1. Add `pypotrace` and `imagetracerpy` to pyproject (with fallbacks documented for native potrace install)
2. Implement potrace pipeline:
   - For multi-color inputs, posterize to N colors and trace each color layer with potrace, then merge as layered SVG paths
   - For monochrome inputs, single trace
3. Implement imagetracer pipeline:
   - Designed for complex inputs with subtle gradients
   - Configurable detail level
4. Implement full suitability analyzer:
   - Color count estimate (k-means elbow detection)
   - Edge density (Sobel)
   - Gradient prevalence (low-frequency Fourier energy ratio)
   - Classification: `good | marginal | poor`
5. Implement `algorithm: auto`:
   - Use the rules from [docs/skills/png-to-svg.md](../skills/png-to-svg.md)
6. Update tests:
   - Each algorithm tested with appropriate fixtures
   - Auto-select correctly chooses for synthetic inputs of each type
   - Suitability classifier tested against labeled fixtures

## Acceptance criteria

### Automated
- All three algorithms produce non-empty SVGs on appropriate fixtures
- Auto-select chooses potrace for 2-color, vtracer for moderate-color, imagetracer for gradient-heavy
- Photo input with no `--force` raises `InputError` with suitability=poor message
- Marginal classification proceeds with warning logged
- Stats.json includes `algorithm_used` and `suitability` fields

### Manual / by-eye
- Run all three algorithms on the same input, compare similarity scores and visual quality
- Auto-select decisions correlate with human judgment ("this looks like a job for potrace" / "this needs imagetracer")
- Photo refusal message is helpful (suggests actions: convert to a flat icon first, use `--force` to proceed)

### Documentation
- SKILL.md mentions all algorithms and the auto rule
- README has a "When to use which" table

## Test in OpenCode

```
> /png-to-svg --input flat-icon.png      # auto → vtracer or potrace
> /png-to-svg --input outlined-icon.png  # auto → potrace
> /png-to-svg --input mascot.png         # auto → imagetracer or refuse
> /png-to-svg --input photo.jpg          # refused unless --force
```

Each case logs the chosen algorithm and the suitability classification.

## Out of scope for phase 07

- Manual touch-up suggestions (post-v1)
- SVG-to-CSS variable extraction (post-v1)
- Multi-pass region-based tracing (post-v1)
- SVGO (Node-based optimizer) integration (we keep `scour` Python fallback as default)

## Risks

- **`pypotrace` install can be tricky** on some platforms (needs `libpotrace`). Auto-detect a `potrace` binary on PATH as a fallback; if neither, raise DependencyMissingError with platform-specific install hints.
- **`imagetracerpy` is slower** than vtracer / potrace. Document the speed difference; for batch use the user can pin algorithm.
- **Suitability classifier false positives/negatives.** Tune thresholds against the growing fixture set as we collect feedback.

## Dependencies on prior work

- Phase 06 (vtracer pipeline, similarity check, stats.json)
