# Quality feature: auto-retry + validation

Generated images fail validation often enough that "always retry once on failure" is the default. This document describes when retries fire, what gets retried, and the escape hatches.

## Validation gates

Three points where validation gates the pipeline:

### 1. `quality_validator` — usability check

Runs after image generation, before declaring the master. Checks (per [quality-validator.md](../shared/quality-validator.md)):
- Transparent background
- Square aspect
- Centered subject
- Readable at 16px
- Adequate contrast
- Non-empty content
- No text artifacts

Failure → retry up to 3 times, escalating prompt adjustments per attempt.

### 2. `consistency_checker` — set / variant cohesion

Runs in:
- `icon-set-creator`: compare each set member to anchor
- `mascot-creator`: compare each variant to master

Failure → retry up to 3 times with the same prompt + same seed-range (variation comes from the model's stochasticity, not from prompt churn).

### 3. Platform validators — `app-icon-pack`

Runs at packaging time:
- `Contents.json` schema valid
- `manifest.json` schema valid
- File dimensions match declared sizes
- ICO multi-resolution decodes cleanly

Failure here is **not retried** — it indicates a code bug, not a model output problem. Escalates to error.

## Retry strategies

### `quality_validator` retries

| Attempt | Strategy |
|---|---|
| 1 (original) | Run as-prompted |
| 2 | Add the failed-check phrase to the negative prompt explicitly. e.g. failure on `transparent_bg` → append `"opaque background, white background, solid background"` to negative |
| 3 | Switch model to fallback. Sometimes the primary model just doesn't do what we asked; the fallback might |
| 4 (last) | Generate with significantly more variants (e.g. 6) and pick best, even if best still doesn't fully pass |

After 4 attempts, surface the best output even if it failed validation, with a clear warning:

```
⚠ Output did not fully pass validation:
  - readable_at_16px: 0.62 (threshold 0.70)
Best candidate retained at master.png; consider regenerating with a different prompt.
```

### `consistency_checker` retries

| Attempt | Strategy |
|---|---|
| 1 | Image-to-image with master as reference, full prompt |
| 2 | Same prompt, different seed |
| 3 | Reinforce anchor description (e.g. "exactly the same character as the reference, not a different character") |

After 3 attempts, surface best-attempt with warning. The user can manually regenerate that single variant if they care.

## Per-skill retry budgets

Total retries are capped to prevent runaway costs:

| Skill | Per-call max | Notes |
|---|---|---|
| `icon-creator` | 4 | Single icon |
| `icon-set-creator` | 3 per member, 36 total for a 12-icon set | High because consistency matters |
| `mascot-creator` | 4 master, 3 per variant | Variants are where retries cluster |

Hard cap is enforced in `openrouter_client`; exceeding raises `OpenRouterError("retry budget exceeded")`.

## Escape hatches

### `--no-retry`

Disable all retries. Used when debugging or when the user just wants to see what comes out. Failed validations still emit warnings but don't trigger regeneration.

### `--no-validate`

Skip validation entirely. Output is delivered as-is. Useful for non-icon use cases where the validator's assumptions don't apply (e.g. generating illustrations that aren't intended to be icons).

### `--validate-strict`

Treat **any** validation failure as a hard error (no auto-accept-best-attempt). Used when shipping to App Store and only "passes" output is acceptable.

## Observability

Every retry is logged with reason:

```json
{"event": "retry", "attempt": 2, "reason": "transparent_bg failed", "strategy": "augment-negative-prompt"}
{"event": "retry", "attempt": 3, "reason": "transparent_bg failed", "strategy": "fallback-model"}
{"event": "validate-pass", "attempt": 3, "scores": {...}}
```

These accumulate in `logs/validator.log` per run. The run summary surfaces "X retries used, Y final cost" so users know if a run was easy or hard.

## When retries shouldn't fire

- **Hard-error API failures**: model not found, auth invalid → fail fast, don't retry
- **Cost threshold exceeded mid-retry**: pause and require confirmation rather than burn budget on a hopeless prompt
- **Same failure repeated 3 times**: escalates with a hint that the prompt may fundamentally be incompatible with the chosen model/preset
