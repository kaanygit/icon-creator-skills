# app-icon-pack

Convert a generated `master.png` into app icon assets for iOS, Android, Web, macOS, watchOS, and Windows.

```bash
python skills/app-icon-pack/scripts/pack.py \
  --master output/geometric-fox-app-icon-20260501-101843/master.png \
  --app-name "Foxy" \
  --platforms ios,android,web,macos,watchos,windows
```

The output directory contains per-platform folders, a README with integration steps, and a zip unless `--no-zip` is passed.
