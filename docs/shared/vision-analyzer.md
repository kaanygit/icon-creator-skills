# Shared module: `vision_analyzer`

Analyzes a reference or generated image and extracts structured information about it: palette, style hints, character traits, brand-similarity warnings.

## Responsibilities

- Extract palette from an image (dominant colors with relative weights)
- Estimate visual-style attributes (flat / 3d, illustrated / realistic, stroke weight, gradient prevalence)
- For mascots: extract character traits (proportions, accessories, distinguishing features) into a text descriptor that can be appended to prompts
- Detect potential brand/logo similarity (lightweight; not a trademark search)
- Detect identifiable-person concerns when a real photo is supplied as reference

This module wraps two distinct backends:

1. **Local CV** (Pillow + scikit-image + scikit-learn) for things we can compute deterministically: palette, edge density, gradient prevalence
2. **Vision LLM via OpenRouter** for things requiring semantic understanding: character traits, style descriptor, brand-like detection

The vision-LLM choice is configurable; default is a fast, cheap multimodal model.

## Public API

```python
from shared.vision_analyzer import VisionAnalyzer

va = VisionAnalyzer()

# palette extraction (local, deterministic)
palette = va.extract_palette(image_path, n_colors=5)
# → [Color(hex="#2563EB", weight=0.42), ...]

# style hints (local + LLM hybrid)
hints = va.analyze_style(image_path)
# StyleHints(
#   palette=[...],
#   gradient_prevalence=0.12,    # 0..1
#   edge_density=0.08,            # 0..1
#   stroke_weight_estimate="regular",  # thin | regular | bold | none
#   art_style="flat-vector",     # LLM-suggested closest preset
#   descriptor="A flat-style icon of a mountain with two peaks ..."   # LLM
# )

# character traits (mascot-specific, LLM)
traits = va.extract_character_traits(image_path)
# CharacterTraits(
#   subject="owl",
#   colors=["brown", "cream", "gold"],
#   proportions="standard",
#   distinguishing_features=["round wire-rim glasses", "tufted ears"],
#   accessories=["glasses"],
#   art_style_descriptor="3D toon, soft shading, rounded forms",
#   anchor_text="A 3D-toon-style owl with brown and cream feathers, round wire-rim glasses ..."
# )

# brand similarity warning (lightweight, advisory)
warning = va.check_brand_similarity(image_path)
# BrandSimilarityWarning(detected=True, reason="appears to be the Twitter/X bird logo")
# or detected=False
```

## Internal mechanics

### Palette extraction

- Resize to 256×256 for speed
- k-means clustering in LAB color space (more perceptually uniform than RGB)
- Sort clusters by relative weight
- Return top-N hex codes + weights

### Style attribute estimation

- **Edge density**: Sobel magnitude > threshold, percentage of pixels above
- **Gradient prevalence**: smooth-region detector (low-frequency Fourier energy ratio)
- **Stroke weight**: edge-detector + skeleton thickness statistics — only meaningful for line/outline styles, returns "none" for filled
- **Art style classification**: LLM call with a constrained-output prompt asking the model to map to one of the known presets

### Character trait extraction

- Single LLM call with a structured-output prompt:
  ```
  You are analyzing a character illustration to enable consistent regeneration in different
  poses and expressions. Describe:
  - Primary subject (animal, robot, human, etc.)
  - Color palette
  - Distinguishing features (accessories, markings, proportions)
  - Art style descriptor
  Respond with JSON matching this schema: { ... }
  ```
- Output JSON parsed and wrapped in `CharacterTraits`

### Brand similarity detection

Heuristic, not a guarantee:

- Compare image hash + embedding against a small embedded database of known major brand logos (Twitter, Apple, Google, Microsoft, common fintech, common SaaS)
- LLM follow-up: "Does this image strongly resemble any known company's logo? If yes, which one? Respond with JSON {match: boolean, name: string|null, confidence: 0-1}"
- Threshold for warning: 0.6

We are not preventing generation; we are surfacing a "you might want to reconsider" message. The user is responsible for their reference images.

### Identifiable-person detection

If the reference is a photograph of a real person (face detection + photo classification), warn user. Implementation: face detector (OpenCV haar cascade or MediaPipe) + photo-likelihood classifier. Threshold tuned to avoid false positives on illustrated faces.

## Cost considerations

- Local CV operations are free
- LLM-based style classification is ~$0.001 per image (cheap multimodal)
- LLM-based trait extraction is ~$0.003 per image
- Brand similarity LLM call is ~$0.001 per image

Cached per file path within a session (same reference image → cached result) to avoid re-paying.

## Error model

```python
class VisionAnalyzerError(IconSkillsError):
    code: str   # 'unsupported-format', 'image-too-small', 'llm-call-failed', 'unknown'
```

Falls back gracefully where possible: if the LLM is unavailable, palette and edge density still work; only LLM-derived fields are missing from the result.

## Configuration

```yaml
vision_analyzer:
  llm_model: openai/gpt-4o-mini
  llm_fallback_models:
    - anthropic/claude-haiku-4-5
  palette_n_default: 5
  cache_results: true
  brand_similarity_threshold: 0.6
```

## Testing

- Local CV tested with synthetic fixtures (programmatically generated images of known palette / style)
- LLM calls mocked in unit tests
- Brand similarity tested with public-domain logo references
