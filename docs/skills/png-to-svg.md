# Skill: `png-to-svg`

Convert a bitmap (PNG/JPG) into an optimized SVG. Used both as a downstream step inside `icon-creator` and `mascot-creator` (when appropriate) and as a standalone vectorizer for users with existing artwork.

## Purpose

Vectorization is hard, and the quality varies wildly with the input. This skill packages the best vectorizer per input type, runs suitability checks before committing to a slow trace, and ships a result with honest quality reporting (similarity score vs original, file size, path count).

## Inputs

| Name | Required | Type | Default | Description |
|---|---|---|---|---|
| `input-path` | yes | path | — | Path to PNG or JPG |
| `algorithm` | no | enum | `auto` | `auto` \| `vtracer` \| `potrace` \| `imagetracer` |
| `color-count` | no | int | auto-detect | How many quantized colors to keep |
| `simplify` | no | int (0-100) | 50 | Path simplification tolerance — higher = fewer points, less fidelity |
| `optimize` | no | bool | true | Run SVGO post-process to compress |
| `output-path` | no | path | derived from input | Where to write the SVG |
| `force` | no | bool | false | Skip suitability check and proceed anyway |
| `comparison` | no | bool | true | Also write a side-by-side comparison PNG |

## Output

```
output/{input-stem}-svg-{timestamp}/
├── {input-stem}.svg              # the vectorized result
├── {input-stem}-comparison.png   # original vs rendered SVG side-by-side
├── {input-stem}-stats.json       # path count, file size, similarity score
└── logs/
    └── trace.log
```

### `stats.json` schema

```json
{
  "skill": "png-to-svg",
  "version": "0.2.0",
  "run_id": "...",
  "input": {
    "path": "icon.png",
    "size_bytes": 18432,
    "dimensions": [1024, 1024],
    "color_count_estimate": 6,
    "edge_density_estimate": 0.12,
    "suitability": "good"
  },
  "settings": {
    "algorithm": "vtracer",
    "color-count": 6,
    "simplify": 50,
    "optimize": true
  },
  "output": {
    "path": "icon.svg",
    "size_bytes": 4128,
    "size_ratio": 0.224,
    "path_count": 14,
    "render_similarity": 0.93
  },
  "warnings": []
}
```

## Suitability check

Before tracing, estimate:

| Metric | Computation | Suitability impact |
|---|---|---|
| Color count | k-means cluster count where elbow occurs | Many distinct colors → vtracer; 2 colors → potrace; > 64 → photo, refuse unless `force` |
| Edge density | Sobel edge percentage | Very low → likely already simple; very high → likely photo, warn |
| Gradient prevalence | Smooth-region detection | High gradient → vtracer with high color count; otherwise potrace |
| Transparency | Alpha channel presence | If absent, suggest running through `image_utils.bg_remove` first |

Result: `{good, marginal, poor}`. `poor` blocks the run unless `force=true`.

## Algorithm selection (auto mode)

```
if color_count <= 2 and edge_density low:
    algorithm = potrace
elif color_count <= 16 and gradient_prevalence < 0.3:
    algorithm = vtracer
elif gradient_prevalence >= 0.3 or color_count > 16:
    algorithm = imagetracer
else:
    algorithm = vtracer  # safe default
```

## Algorithm details

### `potrace`
- Best for: 2-color flat icons, line art, monochrome logos
- Output: clean, minimal paths
- Caveats: monochrome only; we run it color-by-color when called on multi-color input via posterize-and-merge

### `vtracer`
- Best for: flat to moderately-shaded illustrations, modern flat-style icons
- Output: filled paths with quantized colors
- Caveats: gradient handling is approximate

### `imagetracer`
- Best for: complex illustrations with subtle gradients
- Output: many paths, larger files
- Caveats: slower, output can be over-detailed

## Internal flow

```
1. validate_input(path)              # exists, is image, size sane
2. analyze(image)                    # color count, edge density, gradient, suitability
3. if suitability == 'poor' and not force: refuse with explanation
4. preprocess(image):
     - bg removal if no alpha
     - color quantization to color-count
     - mild noise reduction
5. algorithm = pick_algorithm() if auto else user choice
6. raw_svg = trace(algorithm, preprocessed)
7. simplified_svg = path_simplify(raw_svg, simplify)
8. if optimize: optimized_svg = svgo(simplified_svg)
9. rendered = render_svg_to_png(optimized_svg, dimensions)
10. similarity = perceptual_similarity(rendered, original)
11. write svg + stats.json + comparison.png
12. if similarity < 0.85: emit warning in stats + log
```

## Edge cases

- **PNG has alpha but content extends to edge.** Tracer handles alpha as background; result is correct.
- **PNG is a gradient-heavy mascot.** Suitability returns `poor`; user gets a clear "this looks like a complex render — vectorization will produce a large messy SVG, recommend skipping" message.
- **Very small input (< 256px).** Up-resolved internally before tracing for path quality, output retains original dimension hint via SVG `viewBox`.
- **Input is grayscale.** Treated as 2-color; potrace path.
- **Input has hard JPEG artifacts.** Quality check warns; user should provide PNG when possible.

## Dependencies

- `vtracer-py` (Python binding)
- `pypotrace` or `potrace` binary (auto-detect)
- `imagetracerpy` or equivalent
- `cairosvg` or `resvg-py` for SVG → PNG re-render (similarity check)
- `svgo` (Node, optional; pure-Python fallback `scour`)
- `image_utils` from shared

## Acceptance criteria

- **Phase 6** (v0.1): `vtracer` integration only. Flat icon input produces clean SVG with similarity ≥ 0.90.
- **Phase 7** (v0.2): All three algorithms available, auto-select working. Suitability check correctly refuses photo inputs. Stats and comparison rendered.

## Future work (not in v1)

- Manual touch-up suggestions (highlight low-fidelity regions)
- Multi-pass tracing (different algorithm per region)
- SVG-to-CSS color-variable extraction (themeable SVG output)
- Animation hints (separate paths into named groups for easy CSS animation)
