# icon-creator

Generate one PNG icon from a text description.

## Usage

```bash
python skills/icon-creator/scripts/generate.py \
  --description "minimalist mountain at dawn" \
  --style-preset flat
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
- `--model`: OpenRouter model override, default `google/gemini-3.1-flash-image-preview`.
- `--style-preset`: `flat`, `gradient`, `glass-morphism`, `outline`, `3d-isometric`, `skeuomorphic`, `neumorphic`, `material`, or `ios-style`.
- `--colors`: comma-separated palette, e.g. `#FF6600,#111111`.
- `--reference-image`: PNG/JPG style reference. The skill extracts palette and style hints locally.

## Examples

```bash
python skills/icon-creator/scripts/generate.py \
  --description "rocket" \
  --style-preset 3d-isometric
```

```bash
python skills/icon-creator/scripts/generate.py \
  --description "lighthouse" \
  --style-preset gradient \
  --colors "#2F80ED,#F2994A" \
  --reference-image ./brand/style-ref.png
```

## Requirements

Set `OPENROUTER_API_KEY` before running live generation:

```bash
export OPENROUTER_API_KEY="..."
```

Phase 02 does not support variants, validation, packaging, or SVG output. Those land in later phases.
