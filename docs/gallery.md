# Gallery

Small committed examples from real local runs. These are intentionally static so the
GitHub README stays fast and users can understand the expected output shape before
running a live provider call.

## Geometric Fox Icon

Prompt:

```text
geometric fox app icon
```

Command:

```bash
python skills/icon-creator/scripts/generate.py \
  --description "geometric fox app icon" \
  --style-preset gradient \
  --variants 3 \
  --seed 42
```

Output:

![Geometric fox app icon](assets/examples/icon-geometric-fox-master.png)

Variant preview:

![Geometric fox app icon variants](assets/examples/icon-geometric-fox-preview.png)

Expected files:

- `master.png`
- `preview.png`
- `variants/1.png`, `variants/2.png`, `variants/3.png`
- `metadata.json`
- `prompt-debug.txt`

## Friendly Fox Explorer Mascot

Prompt:

```text
friendly fox explorer mascot
```

Command:

```bash
python skills/mascot-creator/scripts/generate.py \
  --description "friendly fox explorer mascot" \
  --type stylized \
  --preset cartoon-2d \
  --personality "curious and helpful" \
  --variants 1 \
  --best-of-n 1
```

Output:

![Friendly fox explorer mascot](assets/examples/mascot-fox-master.png)

Expected files:

- `master.png`
- `variants/1.png`
- `style-guide.md`
- `metadata.json`

## PNG to SVG Comparison

Command:

```bash
python skills/png-to-svg/scripts/vectorize.py \
  --input output/geometric-fox-app-icon-20260501-101843/master.png \
  --algorithm auto
```

Output:

![PNG to SVG comparison](assets/examples/png-to-svg-comparison.png)

This conversion is local-only and does not call an image provider.
