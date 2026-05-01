# Getting Started

## 1. Check your environment

```bash
icon-skills doctor --fix
```

## 2. Generate your first icon

```bash
icon-skills estimate icon --variants 3
icon-skills create-icon \
  --description "minimal fox app icon" \
  --style-preset gradient \
  --variants 3
```

Expected output:

```text
output/minimal-fox-app-icon-{timestamp}/master.png
```

## 3. Package the icon

```bash
icon-skills create-app-icon-pack \
  --master output/minimal-fox-app-icon-{timestamp}/master.png \
  --app-name Foxy \
  --platforms all
```

Expected output includes iOS, Android, Web, macOS, watchOS, Windows, and a zip.

## 4. Vectorize when suitable

```bash
python skills/png-to-svg/scripts/vectorize.py \
  --input output/minimal-fox-app-icon-{timestamp}/master.png \
  --algorithm auto
```

## 5. Generate a mascot

```bash
icon-skills estimate mascot --variants 1 --poses idle,waving --expressions happy,curious --best-of-n 1
icon-skills create-mascot \
  --description "friendly fox explorer mascot" \
  --type stylized \
  --preset cartoon-2d \
  --poses idle,waving \
  --expressions happy,curious
```

## 6. Package the mascot

```bash
python skills/mascot-pack/scripts/pack.py \
  --master output/friendly-fox-explorer-mascot-{timestamp}/master.png \
  --variants-dir output/friendly-fox-explorer-mascot-{timestamp}/ \
  --targets all
```

## 7. Generate an icon family

```bash
icon-skills estimate icon-set --icons '["home","search","profile","settings"]' --best-of-n 1
icon-skills create-icon-set \
  --icons '["home","search","profile","settings"]' \
  --style-preset flat \
  --colors "#2563EB,#1E40AF"
```
