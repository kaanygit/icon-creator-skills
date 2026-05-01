# Phase 18 Acceptance: Multi-provider Image Backends

Date: 2026-05-01

## Scope

Phase 18 adds configurable image providers after the v1.0 release:

- OpenRouter remains the default provider.
- OpenAI Images API can be selected with `--provider openai`.
- Google Gemini image generation can be selected with `--provider google` or `--provider gemini`.
- Provider and model defaults can be set in `~/.icon-skills/config.yaml`.

## Configuration

```yaml
image_generation:
  provider: openrouter

openrouter:
  api_key_file: ~/.icon-skills/openrouter.key
  model: google/gemini-2.5-flash-image

openai:
  api_key_file: ~/.icon-skills/openai.key
  model: gpt-image-1

google:
  api_key_file: ~/.icon-skills/google.key
  model: gemini-2.5-flash-image
```

CLI overrides still win:

```bash
python skills/icon-creator/scripts/generate.py \
  --description "minimal fox" \
  --provider openrouter \
  --model google/gemini-2.5-flash-image
```

## Acceptance Checklist

- [x] Shared provider factory resolves `openrouter`, `openai`, `google`, and aliases.
- [x] OpenRouter model can be set from config or overridden with `--model`.
- [x] OpenAI client supports text-to-image and image-edit style calls.
- [x] Google client supports text-to-image and reference-image calls.
- [x] `icon-creator`, `mascot-creator`, `icon-set-creator`, and `shared.smoke_test` accept provider/model selection.
- [x] README and install docs explain provider API key and model configuration.
- [x] Offline tests cover provider resolution and mocked provider HTTP calls.
- [x] Live API smoke test intentionally skipped because no API key should be used for this phase test pass.
