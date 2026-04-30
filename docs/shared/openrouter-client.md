# Shared module: `openrouter_client`

Single source of truth for talking to OpenRouter. Every skill that generates an image goes through this module.

## Responsibilities

- Authenticate with OpenRouter (read `OPENROUTER_API_KEY` from env)
- Call image-generation endpoints with the chosen model
- Retry on transient failures (rate limit, timeouts, 5xx) with exponential backoff
- Fall back to declared backup models when primary model unavailable
- Track per-call cost and accumulate into a session log
- Support image-to-image where the model exposes it
- Log structured request/response data for debugging

## Public API

```python
from shared.openrouter_client import OpenRouterClient

client = OpenRouterClient()  # reads OPENROUTER_API_KEY

# text-to-image
result = client.generate(
    model="google/gemini-2.5-flash-image",
    prompt="...",
    negative_prompt="...",
    size=(1024, 1024),
    n=3,
    seed=42,
    fallback_models=["openai/dall-e-3"],
)
# result: GenerateResult(images=[Image, Image, Image], cost_usd=0.0432, model_used=..., fallback_used=False)

# image-to-image (when model supports)
result = client.generate(
    model="black-forest-labs/flux-redux",
    prompt="...",
    reference_image=master_path,   # path or PIL.Image
    strength=0.7,
    n=1,
)

# session cost
print(client.session_cost_usd)
```

## Internal behavior

### Authentication

- Reads `OPENROUTER_API_KEY` from environment at construction
- If missing, raises `OpenRouterError` with message linking to OpenRouter sign-up
- Never stored in any output file, never logged in plain text

### Retry policy

- Retry on: 429 (rate limit), 5xx, network timeouts, connection errors
- Do not retry: 4xx other than 429, model-not-found errors
- Backoff: 1s, 2s, 4s, 8s, 16s (max 5 attempts)
- After exhausted retries, raise `OpenRouterError` with the original error context

### Fallback policy

- If primary model returns model-not-found or model-unavailable, try fallback chain in order
- Each fallback gets a fresh retry cycle
- Log a warning when fallback is used so the user notices model drift
- `result.fallback_used = True` and `result.model_used = "actual-model-id"`

### Cost tracking

- Maintains `~/.icon-skills/cost-log.json` (append-only) with one entry per call:
  ```json
  {
    "timestamp": "2026-04-29T15:31:22Z",
    "model": "google/gemini-2.5-flash-image",
    "prompt_chars": 412,
    "n": 3,
    "cost_usd": 0.0432,
    "skill": "icon-creator"
  }
  ```
- Per-session total available via `client.session_cost_usd`
- Each generation call returns its own cost in the result

Pricing data lives in `shared/presets/openrouter_pricing.yaml`, refreshed periodically (manual or CI). If the model isn't in the pricing table, cost is estimated as zero with a logged warning.

### Image-to-image

Not all models on OpenRouter expose image-to-image cleanly. The client checks model capability from `shared/presets/openrouter_models.yaml`:

```yaml
- id: black-forest-labs/flux-redux
  capabilities: [text-to-image, image-to-image]
  image_to_image_param: reference_image
- id: google/gemini-2.5-flash-image
  capabilities: [text-to-image]
```

If the user requests image-to-image on a text-only model, the client either:
1. Falls back to a model declared image-to-image capable, OR
2. Raises `OpenRouterError("model {x} does not support image-to-image")`

The skill chooses the policy via `image_to_image_fallback=True|False`.

### Logging

Structured JSON-line log written per call to a per-run logs/openrouter.log:

```json
{"event": "request", "ts": "...", "model": "...", "prompt_hash": "abc123", "n": 3, "seed": 42}
{"event": "response", "ts": "...", "model_used": "...", "fallback_used": false, "cost_usd": 0.0432, "duration_ms": 4127}
```

Prompts are hashed in logs (not stored verbatim) to avoid leaking sensitive content if logs are shared. Full prompts are in the run's `prompt-debug.txt`.

## Error model

```python
class OpenRouterError(IconSkillsError):
    """Anything API-related"""
    code: str            # 'auth', 'rate-limit', 'model-not-found', 'timeout', 'invalid-input', 'unknown'
    model_attempted: str
    fallback_chain_exhausted: bool
```

## Configuration

```yaml
# shared/defaults.yaml (relevant subset)
openrouter:
  base_url: https://openrouter.ai/api/v1
  timeout_seconds: 60
  max_retries: 5
  app_name: icon-creator-skills
  http_referer: https://github.com/{org}/icon-creator-skills
```

`http_referer` and `app_name` are sent as headers per OpenRouter's recommendation for app attribution. Cosmetic; can be overridden by user config.

## Testing

- Unit tests use `responses` library to mock HTTP calls
- Integration tests gated behind `RUN_LIVE_TESTS=1` env var
- Cost tracking tested with a fake pricing table in fixtures
- Retry behavior tested with simulated 429 / 5xx / timeout sequences

## Future extensibility

The `Backend` protocol (not yet implemented) would allow swapping in Replicate, fal.ai, or local-Stable-Diffusion. The current module is the only `Backend` implementation. Skills already talk to a typed interface, so a future swap is a single-file change.
