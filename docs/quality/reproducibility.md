# Quality feature: reproducibility

Every run records enough state to be regenerated later. Same inputs, same model, same seed → same output (within model determinism limits).

## What gets recorded

Every run writes a `metadata.json` to its output directory:

```json
{
  "skill": "icon-creator",
  "version": "0.3.0",
  "run_id": "mountain-icon-20260429-153122",
  "timestamp": "2026-04-29T15:31:22Z",

  "inputs": {
    "description": "minimalist mountain at dawn",
    "type": "app-icon",
    "style-preset": "flat",
    "colors": ["#FF5733", "#1A1A1A"],
    "reference-image": null,
    "variants": 3,
    "seed": 42
  },

  "model": {
    "id": "sourceful/riverflow-v2-fast-preview",
    "fallback_used": false,
    "fallback_chain": ["black-forest-labs/flux.2-pro"]
  },

  "prompt": {
    "positive_hash": "abc123de",
    "negative_hash": "789xyz12"
  },

  "preset_versions": {
    "icon_styles_yaml_sha": "...",
    "prompt_template_sha": "..."
  },

  "skills_version": {
    "package_version": "0.3.0",
    "git_commit": "abc1234"
  },

  "cost": {
    "currency": "USD",
    "total": 0.0432,
    "by_call": [0.0144, 0.0144, 0.0144]
  },

  "validation": {
    "all_passed": true,
    "checks": { ... }
  },

  "outputs": {
    "master": "master.png",
    "variants": ["variants/1.png", "variants/2.png", "variants/3.png"],
    "svg": null,
    "package": null
  }
}
```

The full prompt text lives in `prompt-debug.txt`, hashed in `metadata.json` for log redaction.

## Reproducing a run

```
$ icon-skills replay output/mountain-icon-20260429-153122/
Replaying with same inputs, model, seed...
New run: output/mountain-icon-20260429-180412-replay-of-153122/
```

The replay command:
1. Loads `metadata.json`
2. Re-runs the same skill with the captured inputs
3. Writes a new run directory with `replay_of` field linking back

If the original used a model that's no longer available, replay tries the fallback chain and notes the substitution in the new metadata.

## When reproducibility breaks

Image generation is **not fully deterministic** even with seeds. Same inputs to the same model on the same day usually produce the same image; across model versions or providers, results diverge.

What we guarantee:
- All **inputs** are recoverable
- The **prompt** is recoverable verbatim (from `prompt-debug.txt`)
- The **decision trail** (model used, fallback applied, retries) is recoverable

What we don't guarantee:
- Pixel-identical regeneration (model nondeterminism)
- Long-term reproducibility if the upstream model is deprecated

## Versioning strategy

Each metadata records:
- `skills_version.package_version` — what version of the toolkit was used
- `skills_version.git_commit` — exact commit SHA when running from git
- `preset_versions.*_sha` — SHA of the YAML preset files at run time
- `preset_versions.prompt_template_sha` — SHA of the specific prompt template used

This lets us debug "why did the same prompt produce different output last week?" — answer: the prompt template changed, here's the diff.

## Replay vs refinement

Replay = same inputs, same outputs (or as close as the model allows).
Refinement = take a previous output as a starting point, change something, get something new (see [multi-shot-iteration.md](multi-shot-iteration.md)).

These are distinct commands and produce differently-named output directories.

## What's NOT recorded

- Reference images are referenced by **path**, not copied. If the user moves or deletes a reference, replay fails. Acceptable tradeoff (versus blowing up disk with copies of every reference).
- API key / auth state — never recorded.
- User config (`~/.icon-skills/config.yaml`) state — recorded only the **subset that affected the run** (e.g. cost threshold), not the whole config.

## Privacy considerations

The metadata file may include the full description text and color hex codes. Users sharing run directories should be aware:
- Description text is recoverable
- Reference image paths are recoverable (though not the images themselves unless shared)
- Prompts are hashed in logs but full text is in `prompt-debug.txt` (in the run dir, not in any global log)

Users wanting privacy-safe sharing can pass `--scrub-metadata` (planned post-v1) which redacts description and reference-path before writing.
