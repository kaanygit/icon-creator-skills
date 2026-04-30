# Skill: `mascot-pack`

Take a mascot output (master + variants) and produce **deliverables**: social media post sizes, sticker packs, print-ready files, web-ready responsive images. Where `app-icon-pack` is for icons going onto devices, `mascot-pack` is for mascots going onto marketing surfaces.

## Purpose

After `mascot-creator` produces a character with poses and expressions, the user typically wants to use the mascot somewhere — Instagram, a hero section, a Telegram sticker pack, a t-shirt mockup. Each surface has its own size, format, and background expectations. This skill packages the mascot for all of them in one shot.

## Inputs

| Name | Required | Type | Default | Description |
|---|---|---|---|---|
| `master` | yes | path | — | Mascot master PNG (transparent bg) |
| `variants-dir` | no | path | — | Directory containing pose/expression variants (typically `mascot-creator` output) |
| `targets` | no | list | all | `social`, `stickers`, `print`, `web` |
| `mascot-name` | no | string | derived | Used in zip name |
| `output-dir` | no | path | `output/` | |
| `bg-variants` | no | bool | true | Produce transparent + white-bg + dark-bg versions of master |
| `webp` | no | bool | true | Produce WebP alongside PNG for web targets (50% smaller) |
| `zip` | no | bool | true | Bundle output into a zip |

## Output

```
output/{mascot-name}-pack-{timestamp}/
├── master/
│   ├── master.png                # original transparent
│   ├── master-white-bg.png       # if bg-variants=true
│   └── master-dark-bg.png        # if bg-variants=true
├── social/                       # if "social" in targets
│   ├── instagram-post-1080.png
│   ├── instagram-story-1080x1920.png
│   ├── twitter-post-1200x675.png
│   ├── linkedin-post-1200x627.png
│   ├── facebook-cover-820x312.png
│   ├── youtube-thumbnail-1280x720.png
│   ├── tiktok-1080x1920.png
│   └── og-image-1200x630.png
├── stickers/                     # if "stickers" in targets
│   ├── imessage/
│   │   ├── sticker-300.png
│   │   ├── sticker-408.png       # Apple's recommended size
│   │   ├── sticker-618.png       # large
│   │   └── per-pose/             # one sticker per pose/expression variant
│   ├── telegram/
│   │   ├── sticker-512.png
│   │   ├── sticker-with-outline-512.png   # 8px white stroke (Telegram convention)
│   │   └── per-pose/
│   ├── whatsapp/
│   │   ├── tray-96.png
│   │   ├── sticker-512.png
│   │   └── per-pose/
│   ├── discord-emoji/
│   │   ├── emoji-128.png
│   │   └── per-pose/             # filename = "{pose-or-expression}.png"
│   └── slack-emoji/
│       └── emoji-128.png
├── print/                        # if "print" in targets
│   ├── business-card-300dpi.png
│   ├── poster-A4-300dpi.png
│   ├── poster-A3-300dpi.png
│   ├── tshirt-print-ready.png    # transparent bg, 300dpi, ~4500×4500 max
│   └── cmyk-preview.png          # advisory CMYK conversion of master
├── web/                          # if "web" in targets
│   ├── hero-800w.png
│   ├── hero-1200w.png
│   ├── hero-1600w.png
│   ├── hero-2400w.png
│   ├── avatar-64.png
│   ├── avatar-128.png
│   ├── avatar-256.png
│   ├── avatar-512.png
│   └── webp/                     # if webp=true
│       └── ... matching .webp for each
├── poses-grid.png                # showcase grid of all poses if variants-dir provided
├── expressions-grid.png          # showcase grid of all expressions if available
├── README.md                     # what each file is for
└── {mascot-name}-pack.zip
```

## Internal flow

```
1. validate_master                 # exists, transparent or auto-bg-removable
2. discover_variants(variants-dir) # find poses/, expressions/ subdirs if present
3. for each target in targets:
     - load size table for target
     - resize master (and variants where applicable) to each size
     - apply target-specific transforms (e.g. Telegram outline, sticker rounding)
     - apply bg fills where required (e.g. social media posts often need bg)
4. if bg-variants: produce master variants with white and dark backgrounds
5. if webp: produce WebP for web/ target outputs
6. compose poses-grid.png and expressions-grid.png
7. write README.md describing each file's intended use
8. if zip: bundle
```

## Target details

### Social

Sizes per [docs/platforms/social-print.md](../platforms/social-print.md):

| Channel | Size | Notes |
|---|---|---|
| Instagram post | 1080×1080 | Centered mascot on optional bg |
| Instagram story | 1080×1920 | Vertical |
| Twitter / X post | 1200×675 | 16:9 |
| LinkedIn post | 1200×627 | 1.91:1 |
| Facebook cover | 820×312 | Wide |
| YouTube thumbnail | 1280×720 | 16:9 |
| TikTok | 1080×1920 | Vertical, full-bleed safe area |
| OpenGraph (general) | 1200×630 | Universal share |

For each, the mascot is centered (or per template offset) on a chosen background. Default background is transparent; with `bg-variants=true` the skill also produces white-bg and dark-bg versions.

### Stickers

| Platform | Sizes | Notes |
|---|---|---|
| iMessage | 300, 408, 618 | Square, Apple's official sizes |
| Telegram | 512×512 | PNG, optional 8px white stroke convention |
| WhatsApp | 512 sticker + 96 tray | WebP supported but PNG default for compatibility |
| Discord emoji | 128×128 | Per pose / expression |
| Slack emoji | 128×128 | Per pose / expression |

For per-pose stickers, the skill iterates over `poses/` and `expressions/` from `variants-dir`, naming each output by source filename.

### Print

| Asset | Spec |
|---|---|
| Business card | 300dpi, transparent, 1050×600 |
| A4 poster | 300dpi, 2480×3508 |
| A3 poster | 300dpi, 3508×4961 |
| T-shirt print | 300dpi, transparent, ≤4500×4500, color-mode RGB but with CMYK preview |
| CMYK preview | Advisory only; warns if master uses out-of-gamut RGB |

CMYK conversion uses a generic SWOP profile; not a substitute for a print shop's proofing but useful for early visual check.

### Web

Responsive image set + avatar set, with optional WebP variants for size savings.

## Edge cases

- **Master is not transparent.** `image_utils.bg_remove` runs first (rembg). User can opt out with `--no-bg-removal`; in that case targets requiring transparency get the un-modified master and any background blending is the user's responsibility.
- **No variants directory.** Per-pose sticker outputs are skipped; master is used for all sticker outputs.
- **Master aspect is not square.** For square targets (stickers, OG, IG post) we center on a square canvas with padding. For non-square targets we fit-within and pad with chosen bg.
- **Print CMYK conversion is approximate.** Always emits a "for preview only" note in the README.
- **Mascot has visible white edges** (anti-aliasing artifact from poor bg removal). `image_utils` runs an alpha-edge cleanup pass before exporting transparent assets.

## Acceptance criteria

- **Phase 12** (v1.0): All four targets produce expected files. Telegram sticker pack imports cleanly into Telegram's bot. iMessage sticker meets Apple's 500KB-per-sticker limit. PWA web set displays at intended sizes in browser.

## Dependencies

- `Pillow` (resize, format conversion, ICO writing)
- `Pillow.ImageCms` for CMYK preview (with bundled SWOP profile)
- `pillow_avif` or `webp` support for WebP output
- `image_utils` from shared (bg removal, alpha cleanup)
- `shared/presets/platforms/social-print.yaml`

## Future work (not in v1)

- Animated stickers (Telegram .tgs / Lottie format)
- Mockup compositing (mascot on a coffee cup, t-shirt, billboard)
- Brand-template overlays (corporate logo + mascot composite)
- LINE / KakaoTalk sticker formats
- Print-ready PDF export with bleed and crop marks
