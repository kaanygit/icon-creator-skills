# Platform: iOS

`AppIcon.appiconset` produced by `app-icon-pack` for iPhone, iPad, and iPad Pro.

## Size matrix

All filenames inside `AppIcon.appiconset/`. Filename convention: `icon-{point-size}@{scale}x.png`, except marketing which is `icon-1024.png`.

| Idiom | Point size | @1x | @2x | @3x |
|---|---|---|---|---|
| iPhone Notification | 20pt | — | 40 | 60 |
| iPhone Settings | 29pt | — | 58 | 87 |
| iPhone Spotlight | 40pt | — | 80 | 120 |
| iPhone App | 60pt | — | 120 | 180 |
| iPad Notification | 20pt | 20 | 40 | — |
| iPad Settings | 29pt | 29 | 58 | — |
| iPad Spotlight | 40pt | 40 | 80 | — |
| iPad App | 76pt | 76 | 152 | — |
| iPad Pro App | 83.5pt | — | 167 | — |
| App Store Marketing | 1024pt | 1024 | — | — |

Total distinct files: **17**.

## `Contents.json` schema

The marketing 1024 entry uses the `ios-marketing` idiom. Here's the full structure produced:

```json
{
  "images": [
    { "size": "20x20", "idiom": "iphone", "filename": "icon-20@2x.png", "scale": "2x" },
    { "size": "20x20", "idiom": "iphone", "filename": "icon-20@3x.png", "scale": "3x" },
    { "size": "29x29", "idiom": "iphone", "filename": "icon-29@2x.png", "scale": "2x" },
    { "size": "29x29", "idiom": "iphone", "filename": "icon-29@3x.png", "scale": "3x" },
    { "size": "40x40", "idiom": "iphone", "filename": "icon-40@2x.png", "scale": "2x" },
    { "size": "40x40", "idiom": "iphone", "filename": "icon-40@3x.png", "scale": "3x" },
    { "size": "60x60", "idiom": "iphone", "filename": "icon-60@2x.png", "scale": "2x" },
    { "size": "60x60", "idiom": "iphone", "filename": "icon-60@3x.png", "scale": "3x" },
    { "size": "20x20", "idiom": "ipad", "filename": "icon-20.png", "scale": "1x" },
    { "size": "20x20", "idiom": "ipad", "filename": "icon-20@2x-ipad.png", "scale": "2x" },
    { "size": "29x29", "idiom": "ipad", "filename": "icon-29.png", "scale": "1x" },
    { "size": "29x29", "idiom": "ipad", "filename": "icon-29@2x-ipad.png", "scale": "2x" },
    { "size": "40x40", "idiom": "ipad", "filename": "icon-40.png", "scale": "1x" },
    { "size": "40x40", "idiom": "ipad", "filename": "icon-40@2x-ipad.png", "scale": "2x" },
    { "size": "76x76", "idiom": "ipad", "filename": "icon-76.png", "scale": "1x" },
    { "size": "76x76", "idiom": "ipad", "filename": "icon-76@2x.png", "scale": "2x" },
    { "size": "83.5x83.5", "idiom": "ipad", "filename": "icon-83.5@2x.png", "scale": "2x" },
    { "size": "1024x1024", "idiom": "ios-marketing", "filename": "icon-1024.png", "scale": "1x" }
  ],
  "info": {
    "version": 1,
    "author": "icon-creator-skills"
  }
}
```

## Quirks and gotchas

### Transparency

App Store marketing icon (1024×1024) **must not** have alpha. If the master is transparent, `app-icon-pack` composites onto a background — `bg-color` argument or `#FFFFFF` default — and warns.

### Squircle masking

iOS applies its own corner-mask at runtime (squircle). Icons should be **fully square**, not pre-rounded. If the master has rounded corners, they may double-up with iOS's mask and look weird. We don't auto-detect this; the README warns.

### iOS 13+ unified icon

iOS 13+ supports a single 1024 icon entry with `idiom: any`, and the OS rasterizes the rest. We still ship the legacy matrix for compatibility with older Xcode and tooling that expects all sizes.

### Asset Catalog drag-and-drop

The intended user flow:
1. Open Xcode → project → `Assets.xcassets`
2. Delete the placeholder `AppIcon` (or the new `AppIcon` Single 1024 entry)
3. Drag `AppIcon.appiconset/` from our output into the Asset Catalog
4. Verify in target settings: General → App Icons and Launch Images → App Icons Source → AppIcon

We document this in the per-run README.

### Naming

Filenames matter only because `Contents.json` references them. We use stable conventions so users can re-run and replace cleanly. iPad-specific filenames have `-ipad` suffix where the size collides with iPhone (29@2x).

## Source-image strategy

- **PNG master ≥ 1024**: lanczos resize to each target size
- **SVG master**: rasterize fresh at each target size (lossless)
- **PNG master < 1024**: hard error; quality is unacceptable for App Store

## Validation

When `validate=true`:
- `Contents.json` parses against Apple's published JSON schema
- Every filename listed in `Contents.json` exists on disk
- Every PNG matches its declared size
- 1024×1024 marketing icon has no alpha channel (warn if it does — App Connect will reject)
- All other sizes have valid alpha or solid bg (acceptable either way)

## Future Apple platforms

- **visionOS**: 1536×1536 PNG with depth-sticker layers (front, middle, back). Out of scope for v1; would need its own asset format.
