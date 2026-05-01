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
- `--provider`: image provider override: `openrouter`, `openai`, or `google`.
- `--model`: provider model override. If omitted, uses `~/.icon-skills/config.yaml`, then the preset default.
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

Set a provider API key before running live generation:

```bash
export OPENROUTER_API_KEY="..."
# or
export OPENAI_API_KEY="..."
# or
export GEMINI_API_KEY="..."
```

You can also set provider defaults in `~/.icon-skills/config.yaml`:

```yaml
image_generation:
  provider: openrouter

openrouter:
  api_key_file: ~/.icon-skills/openrouter.key
  model: google/gemini-2.5-flash-image
```
