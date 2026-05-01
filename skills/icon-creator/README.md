# icon-creator

Generate a validated PNG icon from a text description, with style presets, reference-image hints, multi-variant output, and refinement.

## Usage

```bash
python skills/icon-creator/scripts/generate.py \
  --description "minimalist mountain at dawn" \
  --style-preset flat \
  --variants 3
```

The script creates:

```text
output/{slug}-{timestamp}/
├── master.png
├── preview.png
├── variants/
│   ├── 1.png
│   ├── 2.png
│   └── 3.png
├── metadata.json
├── prompt-debug.txt
└── logs/openrouter.log
```

The final line printed to stdout is the auto-picked `master.png` path.

## Options

- `--description`: required icon description.
- `--output-dir`: output root directory, default `output`.
- `--model`: OpenRouter model override, default `sourceful/riverflow-v2-fast-preview`.
- `--style-preset`: `flat`, `gradient`, `glass-morphism`, `outline`, `3d-isometric`, `skeuomorphic`, `neumorphic`, `material`, or `ios-style`.
- `--colors`: comma-separated palette, e.g. `#FF6600,#111111`.
- `--reference-image`: PNG/JPG style reference. The skill extracts palette and style hints locally.
- `--variants`: number of candidates to generate and validate, default `3`, supported range `1-6`.
- `--seed`: optional base seed for reproducibility where the provider supports it.
- `--refine`: previous `master.png` or variant to use as an image reference for iteration.

## Examples

```bash
python skills/icon-creator/scripts/generate.py \
  --description "rocket" \
  --style-preset 3d-isometric \
  --variants 3 \
  --seed 42
```

```bash
python skills/icon-creator/scripts/generate.py \
  --description "lighthouse" \
  --style-preset gradient \
  --colors "#2F80ED,#F2994A" \
  --reference-image ./brand/style-ref.png
```

```bash
python skills/icon-creator/scripts/generate.py \
  --refine output/rocket-{timestamp}/master.png \
  --description "more geometric" \
  --variants 2
```

## Requirements

Set `OPENROUTER_API_KEY` before running live generation:

```bash
export OPENROUTER_API_KEY="..."
```

Phase 03 does not support packaging or SVG output. Those land in later phases.
