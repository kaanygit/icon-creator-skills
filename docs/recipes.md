# Recipes

## Generate a 12-icon navigation set

```bash
python skills/icon-set-creator/scripts/generate_set.py \
  --icons '["home","search","profile","settings","messages","notifications","calendar","camera","music","video","files","help"]' \
  --style-preset flat \
  --colors "#2563EB,#1E40AF" \
  --set-name navigation-icons
```

## Build a full mascot pack

```bash
python skills/mascot-creator/scripts/generate.py \
  --description "fox, friendly explorer" \
  --type stylized \
  --preset cartoon-2d \
  --poses idle,waving,running \
  --expressions happy,curious,surprised \
  --outfits adventurer,scientist

python skills/mascot-pack/scripts/pack.py \
  --master output/fox-friendly-explorer-{timestamp}/master.png \
  --variants-dir output/fox-friendly-explorer-{timestamp}/ \
  --targets all
```

## Replace an app icon end-to-end

```bash
python skills/icon-creator/scripts/generate.py \
  --description "calendar app icon, clean folded page" \
  --style-preset ios-style \
  --variants 3

python skills/app-icon-pack/scripts/pack.py \
  --master output/calendar-app-icon-{timestamp}/master.png \
  --app-name CalendarPro \
  --platforms all
```

## Save and reuse a style

```bash
icon-skills styles save --from output/calendar-app-icon-{timestamp} --name calendar-ios
icon-skills styles show calendar-ios
```

## Replay a local packaging run

```bash
icon-skills replay output/foxy-icons-{timestamp}
```
