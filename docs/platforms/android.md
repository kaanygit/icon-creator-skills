# Platform: Android

Android needs more than just resized PNGs: it has **adaptive icons** (foreground + background) since API 26, density buckets, the Play Store hi-res icon, and a notification icon. `app-icon-pack` produces all of them.

## Density buckets (legacy mipmap PNGs)

Located under `android/mipmap-{dpi}/`. Filename: `ic_launcher.png`.

| Bucket | dpi | Pixel size |
|---|---|---|
| `mipmap-mdpi` | 160 | 48 |
| `mipmap-hdpi` | 240 | 72 |
| `mipmap-xhdpi` | 320 | 96 |
| `mipmap-xxhdpi` | 480 | 144 |
| `mipmap-xxxhdpi` | 640 | 192 |

These are still required for backwards compatibility (pre-API-26 devices, splash screens, anything reading the legacy launcher icon).

## Adaptive icon (API 26+)

Two layers: **foreground** (the recognizable subject) and **background** (a solid color or pattern). Android masks them at runtime into circle / squircle / rounded-square depending on launcher.

### The math

- Total canvas: 108×108 dp
- Safe zone (always visible): 72×72 dp centered
- Outer 18dp on each side may be cropped or used for parallax/animation
- Foreground content **must fit within the 72dp safe zone**

In our pipeline, this rasterizes per density:

| Bucket | 108dp canvas | 72dp safe zone | Foreground content max |
|---|---|---|---|
| mdpi | 108 | 72 | 72 |
| hdpi | 162 | 108 | 108 |
| xhdpi | 216 | 144 | 144 |
| xxhdpi | 324 | 216 | 216 |
| xxxhdpi | 432 | 288 | 288 |

### Output layout

```
android/
├── mipmap-mdpi/ic_launcher.png         # legacy 48
├── mipmap-hdpi/ic_launcher.png         # legacy 72
├── mipmap-xhdpi/ic_launcher.png        # legacy 96
├── mipmap-xxhdpi/ic_launcher.png       # legacy 144
├── mipmap-xxxhdpi/ic_launcher.png      # legacy 192
├── mipmap-anydpi-v26/
│   └── ic_launcher.xml                 # adaptive icon descriptor
├── drawable/
│   ├── ic_launcher_foreground.png      # 432 (xxxhdpi) — Android scales for other dpis
│   └── ic_launcher_background.png      # 432 — solid color or image
├── notification/
│   └── ic_stat_24.png                  # monochrome 24×24 notification icon
└── play-store/
    └── ic_launcher_512.png             # high-res for Play Store listing
```

Note: the adaptive icon's foreground and background are typically shipped as **vector drawables** (XML) or as PNG. We ship as PNG at xxxhdpi (432px), which Android scales correctly per device. Vector drawable support is future work (requires SVG → Android VectorDrawable XML conversion).

### `mipmap-anydpi-v26/ic_launcher.xml`

```xml
<?xml version="1.0" encoding="utf-8"?>
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@drawable/ic_launcher_background"/>
    <foreground android:drawable="@drawable/ic_launcher_foreground"/>
</adaptive-icon>
```

## Foreground / background separation

When the master has a transparent background:
- Foreground = master image, scaled to fit the 72dp safe zone, centered on a 108dp transparent canvas
- Background = solid `bg-color` fill (default `#FFFFFF`, user-supplied via `--bg-color`)

When the master has an opaque background:
- `image_utils.bg_remove` runs to extract the subject
- Subject becomes the foreground
- Background becomes the original master's background color (sampled from corners), or user-supplied `bg-color`

User can override entirely with explicit `--foreground` and `--background` paths.

## Notification icon

Pre-Lollipop Android renders notification icons with intricate detail. Lollipop+ (API 21+) **flattens** notification icons to white silhouettes. The skill produces a 24×24 monochrome PNG:

- Threshold the master alpha at 0.5
- Render white-on-transparent
- Verify subject is recognizable as a silhouette (warning if subject relies on color)

## Play Store icon

512×512 high-res icon used in the Play Store listing. **Must be square, opaque, with the bg color baked in** — no transparency allowed.

## Quirks and gotchas

### Adaptive icon clipping

If the foreground subject extends past the 72dp safe zone, parts get clipped at runtime on circle-mask launchers. Our pipeline auto-scales down to fit; preview (`preview-android.png`) overlays the safe-zone circle so the user can verify before shipping.

### Vector vs raster background

Many official Android docs recommend **vector drawables** for both layers (zoomable, smaller binary). We ship raster PNGs because we can't reliably convert arbitrary inputs to AndroidVectorDrawable XML (which is a constrained subset of SVG). Future enhancement.

### Themed icons (Android 13+)

API 33 introduces **themed icons**: a monochrome layer the OS recolors with the user's accent color. We don't ship a themed icon by default; users wanting one can pass an explicit `--themed-foreground` monochrome PNG.

### Round icon legacy

Pre-API-26 devices that prefer round icons used a separate `ic_launcher_round.png`. Most modern launchers respect adaptive icons; we don't ship `ic_launcher_round.png` (legacy). Apps that target very old API levels can request it as future work.

## Integration

Documented in the per-run README:

1. Copy `android/` contents into `app/src/main/res/`
2. Reference `@mipmap/ic_launcher` in `AndroidManifest.xml` (already standard)
3. Re-build; verify launcher displays the new icon

## Validation

When `validate=true`:
- All density mipmap PNGs exist and match expected dimensions
- Adaptive icon XML parses
- Foreground content (alpha non-empty pixels) fits within safe zone
- Notification icon is monochrome (only white pixels with varying alpha)
- Play Store 512 has no transparency
