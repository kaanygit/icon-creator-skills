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
- `--model <openrouter-model-id>`: model override, default `google/gemini-3-pro-image-preview`

The script prints the path to the generated `master.png` on the last line of stdout.

## Phase 01 limits

This version is intentionally simple: single-shot generation, no style presets, no reference image, no validation, no variants, no packaging, no vectorization.

