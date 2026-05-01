# OpenRouter model matrix

Central model-selection reference for v1. Style preset docs describe creative intent; this file owns model IDs, fallback candidates, and capabilities.

Status values:

- `selected`: allowed in default preset mappings after Phase 00 implements YAML.
- `candidate`: useful model to evaluate, but do not make it a default until tested.
- `retired`: do not use in default mappings unless availability changes.

## Selected for v1 implementation

| Model ID | Status | Intended use | Capability notes |
|---|---|---|---|
| `google/gemini-3-pro-image-preview` | selected | Default general-purpose image model for icons and mascot masters | Supports image input and image output on OpenRouter. Use `modalities: ["image", "text"]`. |
| `black-forest-labs/flux.2-pro` | selected | High-quality icon styles, 3D, glass, mascot consistency, image editing/reference-heavy flows | Current Black Forest Labs image model family on OpenRouter. Evaluate for both text-to-image and editing. |
| `black-forest-labs/flux.2-flex` | candidate | Fine-detail, typography-sensitive, and multi-reference editing tests | Promising for reference-heavy workflows; keep as candidate until Phase 02/09 tests prove value. |

## Retired from default mappings

| Model ID | Reason |
|---|---|
| `openai/dall-e-3` | OpenRouter currently reports this model as unavailable. Do not use as a default fallback. |
| `black-forest-labs/flux-1.1-pro` | Older model ID in planning docs. Replace defaults with current `flux.2-*` candidates. |
| `black-forest-labs/flux-redux` | Do not assume this exact ID exists. Use OpenRouter model discovery before adding image-to-image defaults. |
| `stability-ai/stable-diffusion-3.5` | Not selected for v1 defaults until OpenRouter image-output availability and pricing are explicitly verified. |

## Initial preset mapping

This is the starting point for `shared/presets/icon_styles.yaml` in Phase 00/02. It can change after live visual tests.

| Preset | Primary | Fallback |
|---|---|---|
| `flat` | `google/gemini-3-pro-image-preview` | `black-forest-labs/flux.2-pro` |
| `gradient` | `google/gemini-3-pro-image-preview` | `black-forest-labs/flux.2-pro` |
| `glass-morphism` | `black-forest-labs/flux.2-pro` | `google/gemini-3-pro-image-preview` |
| `outline` | `google/gemini-3-pro-image-preview` | `black-forest-labs/flux.2-pro` |
| `3d-isometric` | `black-forest-labs/flux.2-pro` | `google/gemini-3-pro-image-preview` |
| `skeuomorphic` | `black-forest-labs/flux.2-pro` | `google/gemini-3-pro-image-preview` |
| `neumorphic` | `google/gemini-3-pro-image-preview` | `black-forest-labs/flux.2-pro` |
| `material` | `google/gemini-3-pro-image-preview` | `black-forest-labs/flux.2-pro` |
| `ios-style` | `black-forest-labs/flux.2-pro` | `google/gemini-3-pro-image-preview` |

## Phase 00 YAML target

Phase 00 should create `shared/presets/openrouter_models.yaml` with this shape:

```yaml
models:
  google/gemini-3-pro-image-preview:
    status: selected
    provider: google
    output_modalities: [text, image]
    default_modalities: [image, text]
    supports_text_to_image: true
    supports_image_input: true
    supports_image_edit: true
    pricing_basis: tokens
    notes: "Token-priced model; use response usage when available."

  black-forest-labs/flux.2-pro:
    status: selected
    provider: black-forest-labs
    output_modalities: [image]
    default_modalities: [image]
    supports_text_to_image: true
    supports_image_input: true
    supports_image_edit: true
    pricing_basis: megapixel
    notes: "Use for high-quality and reference-heavy flows after smoke tests."
```

## Verification cadence

- Re-check this matrix before implementing Phase 00.
- Re-check it again before Phase 02 presets, Phase 08 mascot presets, and Phase 17 release.
- Any unavailable default model is a release blocker unless a fallback is already selected and tested.
