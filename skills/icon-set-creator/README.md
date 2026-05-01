# icon-set-creator

Generate a coherent icon family.

```bash
.venv/bin/python skills/icon-set-creator/scripts/generate_set.py \
  --icons '["home","search","profile","settings"]' \
  --style-preset flat \
  --colors "#2563EB,#1E40AF" \
  --set-name nav-icons
```

Use `--reference-icon path/to/style-anchor.png` to anchor a future set to an existing style.
