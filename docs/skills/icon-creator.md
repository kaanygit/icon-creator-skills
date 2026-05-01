# Skill: `icon-creator`

Generate a single icon (app icon, favicon, UI icon, logo-mark) from a text description and optional reference image.

## Purpose

This is the highest-volume skill in the toolkit. The user describes an icon, optionally references an existing image, picks a style, gets a master PNG plus variants. Optionally chains into `app-icon-pack` for multi-platform packaging and `png-to-svg` for vectorization.

## Inputs

| Name | Required | Type | Default | Description |
|---|---|---|---|---|
| `description` | yes | string | — | What the icon should depict. e.g. "minimalist mountain at dawn" |
| `type` | no | enum | `app-icon` | `app-icon` \| `ui-icon` \| `favicon` \| `logo-mark` |
| `style-preset` | no | enum | preset based on `type` | See [icon-styles catalog](../presets/icon-styles.md) |
| `colors` | no | string\|list | auto from prompt | Hex codes or palette name (e.g. `["#FF5733", "#1A1A1A"]`) |
| `reference-image` | no | path | — | Path to PNG/JPG used as inspiration |
| `variants` | no | int | 3 | Number of variants to produce. 1–6 supported. |
| `model` | no | string | preset-derived | Override OpenRouter model id |
| `output-dir` | no | path | `output/` | Where to write the run directory |
| `slug` | no | string | derived from description | Used in directory name |
| `vectorize` | no | bool | false | Also run `png-to-svg` on the master |
| `package` | no | enum\|list | none | Pass to `app-icon-pack`; one of `ios`, `android`, `web`, etc. |
| `bg-removal` | no | bool | auto | Force on/off; default detects alpha channel and runs only if missing |
| `seed` | no | int | random | For reproducible runs |

If `description` is missing, `AskUserQuestion` prompts for it before any model call.

## Output

```
output/{slug}-{timestamp}/
├── master.png                   # 1024×1024, transparent bg, square
├── master.svg                   # only if vectorize=true and suitable
├── variants/
│   ├── 1.png
│   ├── 2.png
│   └── 3.png
├── metadata.json                # see schema below
├── prompt-debug.txt             # full prompt + negative prompt for inspection
├── preview.png                  # grid showing master + variants for quick scan
└── logs/
    ├── openrouter.log
    └── validator.log
```

If `package` was set, also produces an `app-icon-pack`-style asset directory and zip alongside the master.

### `metadata.json` schema

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
    "fallback_used": false
  },
  "prompt": {
    "positive": "...",
    "negative": "..."
  },
  "cost": {
    "currency": "USD",
    "total": 0.0432,
    "by_call": [0.0144, 0.0144, 0.0144]
  },
  "validation": {
    "all_passed": true,
    "checks": {
      "transparent_bg": true,
      "square_aspect": true,
      "centered": true,
      "readable_at_16px": true
    }
  }
}
```

## Internal flow

```
1. parse_inputs(args)                          # fill defaults, AskUserQuestion if needed
2. if reference: vision_analyzer.analyze()     # extract style hints
3. prompt_builder.build(type, preset, hints)
4. model = preset.model or args.model
5. for i in range(variants):
       image = openrouter_client.generate(model, prompt, seed+i)
       image = image_utils.post_process(image)  # bg removal, crop, square+pad
6. master = quality_validator.pick_best(variants)  # or first if all pass
7. write_outputs()
8. if vectorize: invoke png-to-svg
9. if package: invoke app-icon-pack
```

## Model selection by preset

Preset-to-model mapping lives in `shared/presets/icon-styles.yaml`. Defaults:

| Preset | Primary model | Fallback |
|---|---|---|
| `flat` | `sourceful/riverflow-v2-fast-preview` | `black-forest-labs/flux.2-pro` |
| `gradient` | `sourceful/riverflow-v2-fast-preview` | `black-forest-labs/flux.2-pro` |
| `glass-morphism` | `sourceful/riverflow-v2-fast-preview` | `black-forest-labs/flux.2-pro` |
| `outline` | `sourceful/riverflow-v2-fast-preview` | `black-forest-labs/flux.2-pro` |
| `3d-isometric` | `sourceful/riverflow-v2-fast-preview` | `black-forest-labs/flux.2-pro` |
| `skeuomorphic` | `sourceful/riverflow-v2-fast-preview` | `black-forest-labs/flux.2-pro` |
| `neumorphic` | `sourceful/riverflow-v2-fast-preview` | `black-forest-labs/flux.2-pro` |
| `material` | `sourceful/riverflow-v2-fast-preview` | `black-forest-labs/flux.2-pro` |
| `ios-style` | `sourceful/riverflow-v2-fast-preview` | `black-forest-labs/flux.2-pro` |

## Prompt template (sketch)

Final prompt is composed from:

```
[POSITIVE]
{description}, {preset.style_phrase}, centered subject, transparent background,
square aspect ratio, even padding, no text, optimized for app icon use,
high contrast, clean edges {color_clause}.

[NEGATIVE]
photograph, realistic photo, watermark, signature, text, letters, words,
multiple subjects, asymmetric composition, cluttered, low contrast, blurry,
{preset.negative_extras}
```

Full templates in [docs/presets/prompt-templates.md](../presets/prompt-templates.md).

## Edge cases

- **Empty description.** `AskUserQuestion` blocks until provided.
- **Reference image is a logo.** `vision_analyzer` flags brand-similar inputs; warning surfaced, generation continues if user confirms.
- **All variants fail validation.** Auto-retry once with adjusted prompt; if still failing, surface the failures and let the user inspect.
- **Model not available on OpenRouter.** Fallback chain kicks in; if all fail, hard error with model-availability list.
- **`vectorize=true` on a complex/photoreal icon.** `png-to-svg` suitability check warns; user decides.

## Acceptance criteria (per phase)

- **Phase 1** (v0.1): Single shot, no presets. `> icon-creator "fox"` produces a usable PNG. Cost logged. Metadata written.
- **Phase 2** (v0.2): All 9 style presets work. Reference image input changes output style measurably.
- **Phase 3** (v0.3): Multi-shot, quality validator, iteration mode (`--refine path/to/prev/master.png`).

## Dependencies on other components

- `shared/openrouter_client.py`
- `shared/vision_analyzer.py` (when reference present)
- `shared/prompt_builder.py`
- `shared/image_utils.py`
- `shared/quality_validator.py`
- `shared/presets/icon_styles.yaml`
- `shared/presets/prompt_templates/icon-creator/`
- Optional invocation of `png-to-svg` and `app-icon-pack`

## Future work (not in v1)

- Brand-kit aware generation: read `.iconrc.json` and apply automatically without per-call args
- "Iterate on this one" — pick a variant, refine
- Style-memory: name a style, recall later for new icons in the same family
