# Troubleshooting

## Run doctor first

```bash
icon-skills doctor
```

## OpenRouter API key missing

Use either `OPENROUTER_API_KEY` or `openrouter.api_key_file` in `~/.icon-skills/config.yaml`.
The key itself should never be committed to this repo.

## Model not found

Pass `--model` with a known OpenRouter image model or update `shared/presets/openrouter_models.yaml`.

## Vectorization quality is poor

`png-to-svg` works best on flat, low-color art. Complex rendered images may be refused unless `--force` is passed.

## Mascot variants drift from the master

Use fewer variant requests per run, set `--best-of-n 3`, and keep the character description concrete:
colors, accessories, body shape, and personality.

## App icon pack looks clipped

Adaptive Android icons require foreground safe-zone padding. Re-run with a master icon that has more padding.

## CMYK output warning

`mascot-pack` emits an approximate CMYK TIFF preview. It is not a replacement for a printer proof.
