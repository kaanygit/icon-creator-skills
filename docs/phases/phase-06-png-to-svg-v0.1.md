# Phase 06: `png-to-svg` v0.1

First vectorization phase. `vtracer` integration only, focused on flat / icon-friendly inputs. Produces a usable SVG with a similarity score back to the original.

## Goal

```
> /png-to-svg --input output/fox-icon-{ts}/master.png
```

produces a clean SVG, a side-by-side comparison PNG, and a stats JSON. For flat-style icons, similarity ≥ 0.90.

## Deliverables

### Skill folder

```
skills/png-to-svg/
├── SKILL.md
├── scripts/
│   └── vectorize.py
└── tests/
    └── test_vectorize.py
```

### New shared utilities

- `shared/image_utils.rasterize_svg` — already added in phase 04, used here for similarity check
- New: `shared/image_utils.compare_perceptual_similarity(a, b) -> float`

### Dependencies

- `vtracer` (Python binding via `vtracer-py`)
- `svgo` (Node, optional) or `scour` (pure-Python fallback) for optimization

## Implementation steps

1. Add `vtracer-py` and `scour` to pyproject (declare `svgo` as optional with fallback to `scour`)
2. Implement `image_utils.compare_perceptual_similarity` (perceptual hash + pixel diff blend)
3. Write `vectorize.py`:
   - Parse args: `--input`, `--output`, `--color-count`, `--simplify`, `--optimize`, `--comparison`
   - Load image, run basic suitability check (not as strict as phase 07; just refuse if it's clearly a photo by file metadata or extreme color count)
   - Preprocess: ensure alpha; mild noise reduction; optional color quantization to `--color-count`
   - Call `vtracer` with sensible defaults (gradient mode, layered, segment_length=4.0, etc.)
   - Apply `scour` (or `svgo` if available) for optimization
   - Render SVG back to PNG via `rasterize_svg`
   - Compute similarity score
   - Write outputs: SVG, comparison PNG (side-by-side), stats.json
4. Tests with synthetic inputs: known-flat icon → similarity ≥ 0.90; known-photo → either refused or low similarity warning

## Acceptance criteria

### Automated
- Test synthetic flat icon → SVG produced, similarity ≥ 0.90, file size smaller than input PNG
- Test simple 2-color icon → SVG with single path or few paths
- Test photo input → either refused (with `--force` not given) or proceeds with low similarity warning logged
- Output `stats.json` has all required fields

### Manual / by-eye
- Run on real outputs from `icon-creator` (flat, outline, gradient presets) — eyeball that the SVG looks like the original
- Open the SVG in a browser and compare to the original — pixel-level glitches are acceptable; major shape distortions are not
- Confirm the comparison.png shows side-by-side with no obvious distortions

### Documentation
- SKILL.md with all flags
- README explains when to use vs not (suitability hints)

## Test in OpenCode

```
> /icon-creator "diamond shape" --style-preset flat
... output/diamond-{ts}/master.png

> /png-to-svg --input output/diamond-{ts}/master.png
```

Confirm:
- SVG produced
- Comparison PNG shows close visual match
- stats.json shows similarity ≥ 0.85

## Out of scope for phase 06

- `potrace` algorithm (phase 07)
- `imagetracer` algorithm (phase 07)
- `algorithm: auto` (phase 07)
- Full suitability check (phase 07)
- Multi-pass / region-based vectorization (post-v1)

## Risks

- **vtracer's gradient handling is approximate.** Gradient-style icons may not vectorize cleanly. Document known weakness; phase 07 adds imagetracer for these.
- **`vtracer-py` install issues on some platforms.** Prebuilt wheels exist on PyPI for major OS/arch combos; fallback to source build documented.
- **SVG file size sometimes larger than PNG.** For complex inputs, this is expected; warn in stats.

## Dependencies on prior work

- Phase 00 (config, errors)
- `image_utils.rasterize_svg` from phase 04
