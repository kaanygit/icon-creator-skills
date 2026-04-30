# Platform: Social media + print + web (mascot-pack outputs)

Output specifications for `mascot-pack`. Sizes covering social channels, sticker platforms, print-ready formats, and responsive web.

## Social media sizes

| Channel | Size | Aspect | Notes |
|---|---|---|---|
| Instagram post | 1080×1080 | 1:1 | square |
| Instagram story / reel | 1080×1920 | 9:16 | vertical, full-bleed safe |
| Twitter / X post | 1200×675 | 16:9 | landscape |
| LinkedIn post | 1200×627 | 1.91:1 | wide |
| Facebook cover | 820×312 | 2.63:1 | very wide |
| YouTube thumbnail | 1280×720 | 16:9 | landscape |
| TikTok / Reels (alt) | 1080×1920 | 9:16 | vertical |
| OpenGraph (general share) | 1200×630 | 1.91:1 | universal |

For each, the mascot is centered (or right-third for landscape templates) on a chosen background. Default backgrounds:
- transparent (default)
- white (`--bg-variants` produces this)
- dark (`--bg-variants` produces this — uses `#1A1A1A` unless overridden)

User can pass `--social-bg path/to/bg.png` to use a custom background image (mascot composited centered).

## Sticker platforms

### iMessage

Three sizes per Apple sticker pack guidelines:

| Size | Use |
|---|---|
| 300×300 | Small sticker |
| 408×408 | Recommended (Apple default) |
| 618×618 | Large sticker |

Per-sticker file size limit: **500KB**. The skill validates and warns if any sticker exceeds.

### Telegram

| Size | Use |
|---|---|
| 512×512 | Static sticker |
| 512×512 (with outline) | Telegram convention is 8px white stroke around subject |

Static stickers must be PNG (Telegram supports WebP but PNG is universally compatible).

### WhatsApp

| Size | Use |
|---|---|
| 96×96 | Tray icon (sticker pack thumbnail) |
| 512×512 | Each sticker |

Per-sticker file size limit: **100KB**. The skill compresses if needed; warns if compression degrades quality below threshold.

### Discord emoji

128×128 PNG. Per-emoji file size limit: **256KB**. One file per pose / expression.

### Slack emoji

128×128 PNG. Per-emoji file size limit: **128KB**. One file per pose / expression.

## Print sizes

Generated at **300dpi** for print-quality output.

| Asset | Pixel size | Use |
|---|---|---|
| Business card | 1050×600 | 3.5×2 inch at 300dpi |
| A4 poster | 2480×3508 | 210×297mm at 300dpi |
| A3 poster | 3508×4961 | 297×420mm at 300dpi |
| T-shirt print | up to 4500×4500 | 15×15 inch at 300dpi |

### CMYK preview

Pillow's `ImageCms` converts the master's RGB image to CMYK using a generic SWOP profile (bundled with the package or downloaded once). The output is a **preview only** — actual print shops use their own ICC profiles and require `.tiff` or `.pdf`. The skill writes `cmyk-preview.png` with a header note: *"For preview only. Send your printer the original RGB master and let them handle the conversion."*

### T-shirt specifics

T-shirt printing prefers **transparent** backgrounds. The skill automatically removes background (rembg) if not already transparent, then runs alpha-edge cleanup.

## Responsive web sizes

| Size | Use |
|---|---|
| `hero-800w.png` | Mobile / small viewport |
| `hero-1200w.png` | Standard desktop |
| `hero-1600w.png` | Large desktop |
| `hero-2400w.png` | Retina / high-DPI |

| Avatar size | Use |
|---|---|
| 64 | Tiny avatar (comments) |
| 128 | Small avatar |
| 256 | Profile-page avatar |
| 512 | Large avatar / profile hero |

WebP variants (≈50% smaller) produced when `--webp` is true. HTML snippet for `srcset` is included in the README.

## Showcase grids

`mascot-pack` also produces:

- `poses-grid.png`: composite grid of all poses laid out for at-a-glance review (up to 4×3 layout, scaled per count)
- `expressions-grid.png`: same for expressions
- `master-bg-variants.png`: master shown on transparent / white / dark side-by-side

These are useful as "sales asset" for designers showing the mascot's range, and for the user's own validation.

## Background variants for master

When `--bg-variants=true` (default):

- `master.png` (transparent)
- `master-white-bg.png` (composited on `#FFFFFF`)
- `master-dark-bg.png` (composited on `#1A1A1A`)

Allows the user to pick what looks best in different placements without re-running.

## Quirks and gotchas

### Per-pose stickers and missing variants

If `variants-dir` doesn't include all poses/expressions the user references in social/sticker arguments, the skill warns and uses the master for missing ones.

### CMYK accuracy

Bundled SWOP is a generic ISO-coated profile. Print shops in different regions (Europe, Asia, US) use different profiles. The CMYK preview is genuinely a preview, not a proof. The README is explicit about this.

### Telegram sticker outline

The 8px white stroke is Telegram convention, not a hard requirement. Some sticker packs ship without outlines. We produce both versions (with and without) so users can choose.

### Animated sticker formats (Telegram .tgs / Lottie)

Out of scope for v1. Future enhancement.

### File-size budgets

iMessage and WhatsApp have strict per-file limits. Compression strategy:
1. Save as PNG
2. If size > limit: re-save with `optimize=true`
3. If still > limit: progressively reduce alpha precision (bit depth) and/or color quantize
4. If still > limit: emit warning and continue (better to ship a slightly-too-large file than no file)

## Validation

When `validate=true`:
- Every declared file exists with exact pixel dimensions
- iMessage / WhatsApp / Discord / Slack sticker files within size budgets (warn if not)
- Print files at 300dpi metadata where possible (DPI metadata in PNG via tEXt chunk)
- WebP files decode cleanly
