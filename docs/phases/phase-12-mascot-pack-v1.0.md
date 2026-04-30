# Phase 12: `mascot-pack` v1.0

Take a `mascot-creator` output (master + variants) and produce deliverables: social media post sizes, sticker packs, print-ready files, web-ready responsive images.

## Goal

```
> /mascot-pack --master output/owl-{ts}/master.png \
               --variants-dir output/owl-{ts}/ \
               --targets social,stickers,print,web
```

produces a complete deliverable pack ready for marketing, sticker apps, print shops, and web embed — all in one zip.

## Deliverables

### Skill folder

```
skills/mascot-pack/
├── SKILL.md
├── scripts/
│   ├── pack.py                 # orchestrator
│   ├── social.py
│   ├── stickers.py
│   ├── print.py
│   └── web.py
└── tests/
    └── test_pack.py
```

### Preset content

```
shared/presets/platforms/social-print.yaml    # all sizes per [docs/platforms/social-print.md]
```

### Bundled assets

- ICC profile for CMYK preview (SWOP) — bundled with the package
- Default fonts: NONE (we don't bundle fonts; users supply via `--og-font` if they want OG-image text)

## Implementation steps

1. Author `social-print.yaml` with all sizes
2. Add `pillow_avif` and `pillow_heif` to optional deps; ensure WebP support (Pillow has it natively)
3. Write `social.py`:
   - For each social size, resize/center master with chosen background
   - Optional bg variants (transparent, white, dark)
4. Write `stickers.py`:
   - iMessage 300/408/618 PNGs
   - Per-pose iMessage stickers if variants-dir provided
   - Telegram 512 with and without 8px white outline (see `image_utils.add_stroke`)
   - Per-pose Telegram stickers
   - WhatsApp 512 + 96 tray icon, file-size budget enforcement
   - Discord/Slack 128 emoji per pose / expression
5. Write `print.py`:
   - 300dpi sizes for business card, A4, A3, T-shirt
   - CMYK preview using `Pillow.ImageCms` + bundled SWOP profile
6. Write `web.py`:
   - Hero responsive set (800w, 1200w, 1600w, 2400w)
   - Avatar set (64, 128, 256, 512)
   - WebP duplicates when `--webp` true
7. Compose `poses-grid.png` and `expressions-grid.png` for showcase
8. Write per-run README.md describing each file's intended use
9. Optional zip
10. Tests with synthetic master + synthetic variants directory

## Acceptance criteria

### Automated
- All declared files exist with correct dimensions
- Sticker per-platform file-size budgets respected (warn if exceeded; don't fail)
- WebP files decode cleanly
- CMYK preview file is in CMYK color mode
- Grid files compose correctly when variants-dir provided

### Manual / by-eye
- **Social**: drop into a real Instagram / Twitter / LinkedIn draft; previews look correct
- **iMessage**: import as a sticker pack via Xcode sticker-pack project; verify on device
- **Telegram**: import as a sticker set via @stickers bot; verify the outlined version reads cleanly
- **WhatsApp**: import via a test sticker app; verify under-100KB
- **Print**: open in InDesign or similar; check at 100% zoom for crispness
- **Web**: drop responsive set into a test page with `srcset`; verify correct image picked at different viewport widths

### Documentation
- SKILL.md complete
- README.md explains each output category and how to use it

## Test in OpenCode

End-to-end:
```
> /mascot-creator "happy fox" --type stylized --preset sticker-style \
                  --poses idle,waving,celebrating \
                  --expressions happy,sad,surprised
... output/happy-fox-{ts}/

> /mascot-pack --master output/happy-fox-{ts}/master.png \
               --variants-dir output/happy-fox-{ts}/ \
               --targets stickers,social
```

Confirm:
- Sticker pack ready for direct iMessage / Telegram import
- Social sizes ready for direct upload
- README explains where each file goes

## Out of scope for phase 12

- Animated stickers (Telegram .tgs, Lottie) — post-v1
- LINE / KakaoTalk sticker formats — post-v1
- Print-ready PDF with bleed and crop marks — post-v1
- Mockup compositing (mascot on a t-shirt, billboard) — post-v1
- Brand-template overlays — post-v1

## Risks

- **CMYK conversion is approximate.** Document this prominently in the README; bundled SWOP profile is generic, not a substitute for press proofs.
- **WhatsApp 100KB limit can hurt quality** for complex variants. Compression strategy progressively reduces alpha precision; warn if quality drops below threshold.
- **Telegram outline width** is convention, not spec. We provide both versions; user picks.

## Dependencies on prior work

- Phase 11 (mascot-creator full feature set as input)
- Phases 04 / 05 (image_utils maturity, including write_ico_multires, rasterize_svg, bg_remove)
