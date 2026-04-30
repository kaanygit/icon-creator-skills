# Shared module: `quality_validator`

Determines whether a generated image meets the bar for being a "usable icon." Checks readability, contrast, centering, transparency, and other necessary conditions. Used by `icon-creator` and `icon-set-creator` for accept-or-regenerate decisions.

## Responsibilities

- Verify transparent background where expected
- Verify square aspect ratio
- Verify subject is centered (within tolerance)
- Verify image is readable at 16×16 (smallest required size)
- Verify contrast meets a minimum threshold
- Verify content is not empty / nearly-empty
- Verify no text/letters got hallucinated

Returns structured per-check results plus a combined pass/fail.

## Public API

```python
from shared.quality_validator import QualityValidator

qv = QualityValidator()

result = qv.validate(image_path, profile="app-icon")
# QualityResult(
#   passed=True,
#   checks={
#     "transparent_bg": Check(passed=True, score=1.0, message="alpha present, edges clean"),
#     "square_aspect": Check(passed=True, score=1.0),
#     "centered": Check(passed=True, score=0.93, message="subject within 5% of center"),
#     "readable_at_16px": Check(passed=True, score=0.88),
#     "contrast": Check(passed=True, score=0.81),
#     "non_empty": Check(passed=True, score=0.95),
#     "no_text_artifacts": Check(passed=True, score=0.92, message="0 text-like glyphs detected"),
#   },
#   combined_score=0.93,
# )

# pick best from N candidates
best, all_results = qv.pick_best(candidate_paths, profile="app-icon")
```

## Profiles

Different skill outputs need different validators. A profile selects the relevant subset.

```yaml
profiles:
  app-icon:
    required: [transparent_bg, square_aspect, centered, readable_at_16px, contrast, non_empty]
    optional: [no_text_artifacts]
  ui-icon:
    required: [transparent_bg, square_aspect, centered, readable_at_16px, non_empty]
    optional: [contrast, no_text_artifacts]
  favicon:
    required: [transparent_bg, square_aspect, readable_at_16px, contrast, non_empty]
  logo-mark:
    required: [non_empty, no_text_artifacts]
    optional: [transparent_bg, square_aspect]
  mascot-master:
    required: [non_empty]
    optional: [transparent_bg]
```

## Per-check details

### `transparent_bg`

- Detect alpha channel
- Compute corner-pixel alpha; if four corners have alpha < 0.1, score 1.0
- If only some corners are transparent, score 0.5 (suggests a border or partial bg)
- If no alpha, score 0.0 — fail

### `square_aspect`

- Hard pass / fail; score is binary

### `centered`

- Compute subject bounding box (alpha > threshold)
- Compute distance from bbox center to canvas center, normalized by canvas dimension
- Score: `max(0, 1 - 4 * distance_normalized)` — within 5% of center → ≥0.80

### `readable_at_16px`

- Downsample image to 16×16 with lanczos
- Upsample back to 256×256 with nearest-neighbor (preserves pixel art look)
- Compute Sobel-edge density on the upsampled
- Compare to a reference baseline of "still has structure" — score ∈ [0, 1]
- Pass threshold: 0.70

### `contrast`

- Convert to grayscale luminance
- Compute std deviation of luminance over the subject region
- Normalize to expected range — high std = high contrast
- Pass threshold: contrast standard deviation > 40 (out of 255)

### `non_empty`

- Subject bounding box area > 5% of canvas
- Catches cases where the model produced an almost-blank image

### `no_text_artifacts`

- Run a lightweight OCR (Tesseract or PaddleOCR-quick) on the image
- If detected text > 1 character, fail (icons should not have hallucinated text)
- Note: stylized fake-text is hard to disambiguate from real text. Threshold tunable.

## `pick_best` strategy

Given N candidates from a multi-shot run:

1. Validate all
2. Filter to those that pass required checks
3. If any pass: return the one with highest `combined_score`
4. If none pass: return the one with the highest combined_score regardless, marked as `passed=False`, and emit a warning so the skill knows to surface "best attempt; consider regenerating"

## Error model

```python
class QualityValidatorError(IconSkillsError):
    code: str   # 'image-load-failed', 'profile-unknown', 'ocr-missing', 'unknown'
```

## Configuration

```yaml
quality_validator:
  ocr_backend: tesseract        # tesseract | paddleocr | none
  contrast_min: 40
  centered_tolerance: 0.05      # within 5% of center
  readable_at_16px_threshold: 0.70
  text_artifacts_max_chars: 1
```

## Testing

- Synthetic fixtures: known-good and known-bad icons (programmatically constructed) for each check
- Sample a hand-curated reference set of "definitely good" and "definitely bad" generated icons; run validator and confirm classifications match human judgment
- Threshold tuning: as we accumulate real generated outputs, fine-tune thresholds via held-out validation
- OCR check tested with known text/no-text images and stylized fake-text edge cases
