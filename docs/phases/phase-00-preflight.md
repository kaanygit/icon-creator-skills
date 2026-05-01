# Phase 00-preflight: API and model reality check

This is a short documentation-only phase before implementation starts. Its job is to prevent Phase 00 from building against stale OpenRouter assumptions.

## Goal

Before writing the Python package skeleton, confirm the current OpenRouter image-generation contract and model matrix, then update the phase plan so implementation agents have one clear source of truth.

## Why this phase exists

Image-generation APIs and model availability change faster than the rest of this project. The planning docs originally used model examples that may drift, such as unavailable fallback models or older Flux model names. Phase 00-preflight catches that before any code is written.

## Deliverables

- `docs/presets/model-matrix.md` documents the currently selected v1 model candidates and retired model IDs.
- `docs/shared/openrouter-client.md` reflects the current OpenRouter image-generation request / response shape.
- `docs/phases/phase-00-skeleton.md` explicitly depends on this preflight and states what Phase 00 must implement.
- `docs/phases/phase-acceptance-template.md` provides the acceptance record format for every phase.

## OpenRouter checks

Verify these against official OpenRouter pages before implementation:

1. Image generation uses `/api/v1/chat/completions` with `modalities`.
2. Models that return both text and images use `modalities: ["image", "text"]`.
3. Image-only models use `modalities: ["image"]`.
4. Generated images are read from `choices[*].message.images[*].image_url.url`.
5. Returned image URLs are usually base64 data URLs.
6. Model discovery can filter `/api/v1/models?output_modalities=image`.
7. Each selected model has `image` in `output_modalities`.
8. Any reference-image / image-editing flow is represented in the model matrix before a skill depends on it.

Official references:

- OpenRouter image generation docs: `https://openrouter.ai/docs/guides/overview/multimodal/image-generation`
- OpenRouter model list API: `https://openrouter.ai/api/v1/models?output_modalities=image`
- Sourceful Riverflow image model page: `https://openrouter.ai/sourceful/riverflow-v2-fast-preview`
- Black Forest Labs provider page: `https://openrouter.ai/black-forest-labs`

## Model cleanup rules

- Remove unavailable models from default fallback chains.
- Do not use `openai/dall-e-3` as a v1 fallback unless OpenRouter shows it as available again.
- Prefer current model families with explicit image output support.
- Store model capabilities separately from style presets:
  - `supports_text_to_image`
  - `supports_image_input`
  - `supports_image_edit`
  - `output_modalities`
  - `default_modalities`
  - `pricing_basis`
- Keep style presets focused on creative intent; they should reference model IDs from the central matrix.

## Acceptance criteria

### Documentation

- `docs/presets/model-matrix.md` exists and lists selected, candidate, and retired model IDs.
- `docs/shared/openrouter-client.md` shows the current request payload and response parsing shape.
- Phase index includes this preflight before Phase 00.
- Phase 00 skeleton doc says it consumes the preflight model matrix.

### Manual verification

- Official OpenRouter docs were checked on the acceptance date.
- Each selected model was verified to appear in OpenRouter model discovery or on an official OpenRouter model/provider page.
- Any model whose availability is uncertain is marked `candidate`, not `selected`.

## Test in OpenCode

No OpenCode test. This phase has no skill and no executable code.

## Out of scope

- Writing Python code.
- Running live OpenRouter generation.
- Final visual-quality decisions per preset.
- Implementing `shared/presets/openrouter_models.yaml`; that happens in Phase 00.
