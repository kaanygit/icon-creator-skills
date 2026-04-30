# Quality feature: cost transparency + tracking

Image generation costs real money. The toolkit tells the user what they're about to spend, what they spent, and accumulates a lifetime log they can audit.

## Per-call cost reporting

Every generation call returns a cost in the result object:

```python
result = client.generate(...)
print(result.cost_usd)  # 0.0432
```

This is computed from the OpenRouter pricing table (`shared/presets/openrouter_pricing.yaml`) using the model's per-image-output rate × the number of images requested.

If the model isn't in the pricing table, cost is `None` with a logged warning. Skills then estimate based on the OpenRouter API response's reported usage where available.

## Pre-run cost estimates

Skills that fan out (`icon-set-creator`, `mascot-creator` with variants) print an estimate **before** the run:

```
About to generate:
  - 1 mascot master (3 candidates) — ~$0.06
  - 4 character views — ~$0.08
  - 4 poses — ~$0.08
  - 4 expressions — ~$0.08
  - Estimated retries (~20% overhead) — ~$0.06
  Total estimate: ~$0.36

Continue? [Y/n]
```

If the estimate exceeds the user's threshold (default `$1.00` per call, configurable in `~/.icon-skills/config.yaml`), the prompt is mandatory; the skill won't proceed without confirmation. Above a hard cap (`$10.00` per call default), the skill refuses without `--allow-large-cost`.

## Per-run summary

After each run, the skill prints a summary:

```
Generation complete.
  Skill: mascot-creator
  Run: owl-mascot-20260429-153122
  API calls: 23 (3 master + 4 views + 4 poses + 4 expressions + 8 retries)
  Cost: $0.41 (under estimate of $0.36 — 14% over)
  Output: output/owl-mascot-20260429-153122/
  Cumulative session cost: $1.27
```

## Lifetime cost log

`~/.icon-skills/cost-log.json` accumulates one entry per call (append-only):

```json
{"timestamp": "2026-04-29T15:31:22Z", "skill": "icon-creator", "model": "google/gemini-2.5-flash-image", "n": 3, "cost_usd": 0.0432, "run_id": "..."}
{"timestamp": "2026-04-29T15:32:01Z", "skill": "icon-creator", "model": "google/gemini-2.5-flash-image", "n": 1, "cost_usd": 0.0144, "run_id": "..."}
```

Disable with `~/.icon-skills/config.yaml` setting:
```yaml
cost_logging: false
```

### Audit commands

The toolkit ships a small CLI for auditing the log:

```
$ icon-skills cost summary
Last 7 days: $4.23 across 87 calls
Last 30 days: $18.91 across 412 calls
Lifetime: $34.12 across 798 calls

By skill:
  icon-creator    $11.20  (251 calls)
  mascot-creator  $19.40  (412 calls)
  icon-set-creator $3.52  (135 calls)
  ...

By model:
  google/gemini-2.5-flash-image    $14.20  (612 calls)
  black-forest-labs/flux-1.1-pro   $19.92  (186 calls)
```

```
$ icon-skills cost recent
Last 10 calls:
  2026-04-29 15:32  icon-creator       gemini-2.5-flash-image    $0.014
  ...
```

## Pricing table maintenance

`shared/presets/openrouter_pricing.yaml` is reviewed quarterly. Format:

```yaml
google/gemini-2.5-flash-image:
  per_image_usd: 0.0144
  notes: "Pricing as of 2026-04, OpenRouter listed rate"
black-forest-labs/flux-1.1-pro:
  per_image_usd: 0.04
  notes: "..."
openai/dall-e-3:
  per_image_usd: 0.04
  notes: "Standard quality 1024x1024"
```

OpenRouter pricing changes; CI pulls fresh data on a schedule (out of v1 scope but planned). For v1, manual updates in PRs.

## Cost vs quality tradeoffs

Skills expose `--quality-tier` in v2 (planned, not v1):
- `cheap`: 1 variant, no retries, lowest-cost model in fallback chain
- `balanced`: defaults
- `best`: 6 variants, full retry budget, primary models

For v1, users tune via explicit `--variants` and `--model` arguments.

## What's NOT tracked

- Vision-analyzer LLM calls (cheap, ≈ $0.001 each — accounted but rolled into per-run cost)
- Local image processing (free)
- Disk usage of run directories
- Background process activity

We track only what costs OpenRouter money, plus aggregate per-run/session/lifetime.
