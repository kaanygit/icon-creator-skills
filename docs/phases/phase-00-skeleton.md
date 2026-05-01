# Phase 00: Skeleton

Set up the shared infrastructure that every later phase depends on. No skills yet — just the pieces every skill will use.

Phase 00 starts only after [Phase 00-preflight](phase-00-preflight.md) is accepted. Do not implement OpenRouter calls from stale examples; consume the current model/API rules from [docs/presets/model-matrix.md](../presets/model-matrix.md) and [docs/shared/openrouter-client.md](../shared/openrouter-client.md).

## Goal

A working `shared/` package that can:
- Talk to OpenRouter using the current image-generation API contract
- Resize, crop, pad, save images
- Load configuration from defaults + user-config + project-config + per-call args
- Log structured events to a per-run logs directory

A "hello world" generation works: `python -m shared.smoke_test "fox"` produces a PNG.

## Prerequisites

- Python 3.11+ on developer machine
- OpenRouter account with API key
- Phase 00-preflight accepted; current OpenRouter model matrix verified
- A few hundred MB of disk for downloaded `rembg` models (lazy-fetched on first use)

## Deliverables

### Package structure

```
shared/
├── __init__.py
├── openrouter_client.py
├── image_utils.py
├── config.py
├── errors.py
├── logging_setup.py
├── smoke_test.py                  # standalone "hello world"
├── presets/
│   ├── openrouter_models.yaml     # capability matrix
│   ├── openrouter_pricing.yaml    # rates
│   └── defaults.yaml              # global defaults
└── tests/
    ├── test_openrouter_client.py
    ├── test_image_utils.py
    └── test_config.py
```

### Config schema

`shared/presets/defaults.yaml`:

```yaml
openrouter:
  base_url: https://openrouter.ai/api/v1
  timeout_seconds: 60
  max_retries: 5
  app_name: icon-creator-skills

image:
  default_master_size: 1024
  default_pad_color: [0, 0, 0, 0]    # RGBA transparent

cost:
  per_call_threshold_usd: 1.00
  session_threshold_usd: 5.00
  per_call_hard_cap_usd: 10.00

logging:
  level: INFO
  per_run_logs: true
```

### OpenRouter model schema

`shared/presets/openrouter_models.yaml` is created from `docs/presets/model-matrix.md`:

```yaml
models:
  sourceful/riverflow-v2-fast-preview:
    status: selected
    provider: sourceful
    output_modalities: [image]
    default_modalities: [image]
    supports_text_to_image: true
    supports_image_input: true
    supports_image_edit: true
    pricing_basis: image
```

Phase 00 should also include retired/unavailable model IDs as explicit `status: retired` entries so future agents do not reintroduce them as fallbacks.

### Errors module

```python
class IconSkillsError(Exception): ...
class OpenRouterError(IconSkillsError): ...
class DependencyMissingError(IconSkillsError): ...
class ValidationError(IconSkillsError): ...
class InputError(IconSkillsError): ...
class CostThresholdError(IconSkillsError): ...
```

### Repository scaffolding

- `pyproject.toml` with declared dependencies (Pillow, requests, pyyaml, jinja2, python-dotenv)
- `pytest.ini`
- `ruff.toml` (or section in pyproject)
- GitHub Actions CI workflow stub (lint + tests)

## Implementation steps

1. Initialize Python package, set up pyproject.toml, dev dependencies
2. Write `errors.py` with the exception hierarchy
3. Write `config.py` with merge logic across defaults / user / project / args
4. Write `logging_setup.py` (structured JSON-line logger, per-run directory aware)
5. Write `image_utils.py` minimal API: load, save, resize, crop_square, pad_square, ensure_alpha, detect_alpha
6. Write `openrouter_client.py` with current OpenRouter image-generation request/response handling, retry, fallback chain, model-capability checks, and cost tracking via `openrouter_pricing.yaml`
7. Write `smoke_test.py`: takes a description string, calls openrouter_client, saves PNG
8. Tests for each module
9. CI passes

## Acceptance criteria

### Automated
- All tests in `shared/tests/` pass
- Lint clean (ruff)
- `shared/presets/openrouter_models.yaml` exists and includes selected + retired model records from `docs/presets/model-matrix.md`
- OpenRouter client unit tests mock a response with `choices[0].message.images[0].image_url.url`
- `python -m shared.smoke_test "fox"` exits 0 and produces a non-empty PNG file at `output/smoke-fox-{ts}.png`

### Manual / by-eye
- The smoke-test PNG is recognizably a fox (not perfect, but not garbage)
- Cost log at `~/.icon-skills/cost-log.json` has one entry from the smoke test
- Log file at `output/smoke-fox-{ts}/logs/openrouter.log` contains one request and one response event

## Test in OpenCode

Phase 00 has no skill yet; the user does not test it in OpenCode. Validation is via the smoke test from a terminal.

## Out of scope for phase 00

- Vision analyzer, prompt builder, consistency checker, quality validator (later phases load them as needed)
- Any skill scaffolding
- Preset prompt templates and style-specific model tuning
- Multi-shot, retry-with-augmented-prompt (basic retry on transient errors only; quality retries come in phase 03)
- Production image-to-image UX. Phase 00 only stores capabilities and supports the low-level request shape if straightforward.
