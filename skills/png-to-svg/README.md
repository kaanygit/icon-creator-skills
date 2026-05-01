# png-to-svg

Convert existing icon PNG/JPG files into SVG.

```bash
python skills/png-to-svg/scripts/vectorize.py \
  --input output/geometric-fox-app-icon-20260501-101843/master.png \
  --algorithm auto
```

Outputs:

```text
output/{input-stem}-svg-{timestamp}/
├── {input-stem}.svg
├── {input-stem}-comparison.png
└── {input-stem}-stats.json
```

No OpenRouter/API call is made. The current fallback tracer is local and deterministic.
