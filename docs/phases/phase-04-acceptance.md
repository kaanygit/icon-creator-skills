# Phase 04 acceptance

## Phase

- Phase: 04
- Commit: this commit
- Date: 2026-05-01
- Reviewer: kaanygit / Codex
- Environment: macOS, zsh, Python 3.14.4 in local `.venv`

## Scope completed

- [x] `skills/app-icon-pack/` added with `SKILL.md`, README, and CLI.
- [x] `pack.py` orchestrator added.
- [x] iOS writer added with `AppIcon.appiconset/` and `Contents.json`.
- [x] Android writer added with density mipmaps, adaptive icon XML, foreground/background PNGs, notification icon, and Play Store icon.
- [x] Web writer added with favicon PNGs, multi-resolution ICO, PWA manifest, browserconfig, Safari pinned-tab fallback SVG, and OpenGraph image.
- [x] Platform YAMLs and lightweight schemas added under `shared/presets/platforms/`.
- [x] Shared image utilities extended with background compositing, hex parsing, ICO writing, and optional SVG rasterization.
- [x] Per-run README and optional zip output implemented.

## Automated checks

```bash
.venv/bin/python -m pytest
# result: 30 passed
```

```bash
.venv/bin/python -m ruff check .
# result: All checks passed
```

## Packaging check

Used existing Phase 03 output; no OpenRouter request was made:

```bash
python skills/app-icon-pack/scripts/pack.py \
  --master output/geometric-fox-app-icon-20260501-101843/master.png \
  --app-name Foxy \
  --platforms all \
  --bg-color "#224466"
```

Phase 04 outputs verified in:

```text
output/foxy-icons-20260501-103451/
```

- [x] `ios/AppIcon.appiconset/` generated.
- [x] iOS `Contents.json` parses.
- [x] iOS app icon PNGs generated, including `icon-1024.png`.
- [x] `android/mipmap-*` legacy icons generated.
- [x] Android adaptive icon XML parses.
- [x] Android foreground/background PNGs are 432×432.
- [x] Android Play Store icon is 512×512.
- [x] Web favicon PNGs and `favicon.ico` generated.
- [x] Web `manifest.json` parses and includes 192/512/maskable icons.
- [x] Web `browserconfig.xml` parses.
- [x] Web `og-image.png` is 1200×630.
- [x] Zip generated: `output/foxy-icons-20260501-103451.zip`.

## Manual checks

- [x] Local generated file tree inspected.
- [x] PNG dimensions and manifests verified by tests and local pack validation.
- [ ] Real Xcode iOS project drag-and-drop check accepted.
- [ ] Real Android Studio project check accepted.
- [ ] Real browser install/favicon check accepted.

## Known issues

- SVG master input requires optional `cairosvg`; Phase 04 acceptance used PNG master.
- Background removal is not implemented yet. Opaque masters are packaged as-is with solid adaptive-icon background support.
- Safari pinned-tab SVG is a safe monochrome fallback shape, not full vector tracing of the source icon.

## Sign-off

- [x] Phase implementation accepted
- [x] Synthetic automated pack test accepted
- [x] Existing-master package run accepted
- [ ] External IDE/browser manual checks accepted
- [x] Safe to continue to Phase 05
