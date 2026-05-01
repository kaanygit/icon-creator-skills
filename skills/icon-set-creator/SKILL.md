---
name: icon-set-creator
description: Generate a coherent icon family from a list of subjects, with style anchor extraction, consistency scoring, preview grid, style-guide.md, and per-icon PNG outputs.
---

# Icon Set Creator

Use this skill when the user wants multiple icons that must look like one family.

## CLI

```bash
.venv/bin/python skills/icon-set-creator/scripts/generate_set.py \
  --icons '["home","search","profile","settings"]' \
  --style-preset flat \
  --colors "#2563EB,#1E40AF"
```

This skill uses the configured image provider, defaulting to OpenRouter. Use `--provider openrouter|openai|google` and `--model <model-id>` to override one run. For larger sets, warn the user about call count before running.

## Output

The run folder contains:

- `style-anchor.png`
- `icons/*.png`
- `preview.png`
- `style-guide.md`
- `metadata.json`
