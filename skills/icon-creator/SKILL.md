---
name: icon-creator
description: Generate a single icon, app icon, favicon, UI icon, or logo-mark from a text description.
---

# icon-creator

Use this skill when the user asks to create an icon, app icon, favicon, UI icon, or logo-mark.

## How to invoke

Call:

```bash
python skills/icon-creator/scripts/generate.py --description "<user's description>"
```

Optional arguments:

- `--output-dir <path>`: output root, default `output`
- `--model <openrouter-model-id>`: model override, default `google/gemini-3.1-flash-image-preview`
- `--style-preset <preset>`: one of `flat`, `gradient`, `glass-morphism`, `outline`, `3d-isometric`, `skeuomorphic`, `neumorphic`, `material`, `ios-style`
- `--colors <hex,hex>`: comma-separated palette to steer the output
- `--reference-image <path>`: PNG/JPG reference used for palette and style hints

The script prints the path to the generated `master.png` on the last line of stdout.

## Phase 02 limits

This version is still single-shot. It supports style presets and reference-image hints, but no variants, quality validator, packaging, or vectorization.
