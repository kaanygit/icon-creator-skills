# icon-creator

Generate one PNG icon from a text description.

## Usage

```bash
python skills/icon-creator/scripts/generate.py --description "minimalist mountain at dawn"
```

The script creates:

```text
output/{slug}-{timestamp}/
├── master.png
├── metadata.json
├── prompt-debug.txt
└── logs/openrouter.log
```

The final line printed to stdout is the `master.png` path.

## Options

- `--description`: required icon description.
- `--output-dir`: output root directory, default `output`.
- `--model`: OpenRouter model override, default `google/gemini-2.5-flash-image`.

## Requirements

Set `OPENROUTER_API_KEY` before running live generation:

```bash
export OPENROUTER_API_KEY="..."
```

Phase 01 does not support presets, reference images, variants, validation, packaging, or SVG output. Those land in later phases.

