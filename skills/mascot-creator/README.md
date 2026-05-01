# mascot-creator

Generate mascot masters and character variant packages.

```bash
.venv/bin/python skills/mascot-creator/scripts/generate.py \
  --description "fox, friendly explorer" \
  --type stylized \
  --preset cartoon-2d \
  --views front,side \
  --poses idle,running \
  --expressions happy,curious \
  --outfits adventurer,scientist \
  --matrix
```

Outputs are written under `output/{description}-{timestamp}/`.
