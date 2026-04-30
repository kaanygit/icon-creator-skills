# Shared module: `consistency_checker`

Compares two images and produces a similarity score across multiple stylistic dimensions. Critical for `icon-set-creator` (set members vs anchor) and `mascot-creator` (variant vs master).

## Responsibilities

- Color histogram similarity (palette consistency)
- Edge density similarity (stroke weight / detail level consistency)
- Perceptual hash distance (overall stylistic similarity)
- Subject-segmentation overlap (composition consistency)
- Face-region similarity when faces are detectable (mascot character consistency)
- Combined score via weighted blend, returned alongside per-dimension scores

## Public API

```python
from shared.consistency_checker import ConsistencyChecker

cc = ConsistencyChecker()

score = cc.score(candidate_path, anchor_path)
# ConsistencyScore(
#   combined=0.84,
#   palette_similarity=0.91,
#   edge_density_similarity=0.78,
#   perceptual_hash_similarity=0.82,
#   subject_overlap=0.86,
#   face_similarity=None,             # None = no face in either; float = similarity
#   passed=True,                      # combined >= threshold
#   threshold_used=0.80,
# )

# threshold can be passed explicitly
score = cc.score(candidate, anchor, threshold=0.85)

# batch comparison
scores = cc.score_batch(candidates=[...], anchor=anchor_path)
```

## Per-dimension methods

### Palette histogram similarity

- Quantize both images to a common 16-color palette in LAB color space
- Compute histogram intersection
- Range: [0, 1], higher = more similar palette

### Edge density similarity

- Sobel magnitude > threshold percentage on both images
- Compute `1 - abs(density_a - density_b) / max(density_a, density_b)`
- Captures whether two icons have similar stroke / detail weight

### Perceptual hash distance

- pHash (DCT-based) of both images
- Hamming distance between hashes, normalized to [0, 1] similarity
- Captures overall structural / stylistic similarity

### Subject-segmentation overlap

- Threshold alpha on both (with bg removal if no alpha)
- Compute IOU of subject masks after centering both at canvas center
- Useful for icon-set-creator: are subjects taking up similar canvas area?

### Face-region similarity (mascot only)

- Run face detector (MediaPipe or OpenCV) on both
- If faces detected on both, crop to face region and compare via embedding model (small CLIP variant)
- Returns embedding cosine similarity

## Combined score

```
combined = weighted_sum({
  palette: 0.30,
  edge_density: 0.20,
  perceptual_hash: 0.25,
  subject_overlap: 0.15,
  face_similarity: 0.10,    # only when both faces detected
})
```

If face is missing on one or both images, weight is redistributed to other dimensions.

Default threshold: 0.80. Override per call. Skills choose appropriate thresholds:
- `icon-set-creator`: 0.80 default
- `mascot-creator` for views: 0.80
- `mascot-creator` for poses/expressions: 0.85 (higher because character identity matters)

## Internal mechanics

- All comparisons are run on resized 256×256 versions for speed
- Computed on a thread pool when batched
- Cached by image hash within a session

## Error model

```python
class ConsistencyCheckerError(IconSkillsError):
    code: str   # 'image-load-failed', 'face-detector-missing', 'unknown'
```

## Configuration

```yaml
consistency_checker:
  default_threshold: 0.80
  weights:
    palette: 0.30
    edge_density: 0.20
    perceptual_hash: 0.25
    subject_overlap: 0.15
    face_similarity: 0.10
  face_detector: mediapipe
  face_embedding_model: openai/clip-vit-base-patch32
```

## Testing

- Synthetic fixtures: known-similar pairs (programmatically generated style-matching pairs) and known-different pairs
- Per-dimension tests with hand-crafted edge cases (e.g. inverted palette, scaled subject)
- Combined-score regression test: a fixture set of candidate-anchor pairs with hand-labeled "should pass" / "should fail"
- Continuous tuning: as we collect real-world output pairs, threshold and weights tuned via held-out validation set
