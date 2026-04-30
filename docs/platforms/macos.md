# Platform: macOS

`AppIcon.appiconset` for Mac apps. Same Asset Catalog format as iOS but with different sizes and conventions.

## Size matrix

| Point size | @1x | @2x |
|---|---|---|
| 16pt | 16 | 32 |
| 32pt | 32 | 64 |
| 128pt | 128 | 256 |
| 256pt | 256 | 512 |
| 512pt | 512 | 1024 |

Total distinct PNG sizes: **10** (some overlap when @2x of a smaller size equals @1x of a larger size, but Apple wants both as separate entries).

## Output layout

```
macos/
└── AppIcon.appiconset/
    ├── icon-16.png
    ├── icon-16@2x.png
    ├── icon-32.png
    ├── icon-32@2x.png
    ├── icon-128.png
    ├── icon-128@2x.png
    ├── icon-256.png
    ├── icon-256@2x.png
    ├── icon-512.png
    ├── icon-512@2x.png
    └── Contents.json
```

## `Contents.json`

```json
{
  "images": [
    { "size": "16x16", "idiom": "mac", "filename": "icon-16.png", "scale": "1x" },
    { "size": "16x16", "idiom": "mac", "filename": "icon-16@2x.png", "scale": "2x" },
    { "size": "32x32", "idiom": "mac", "filename": "icon-32.png", "scale": "1x" },
    { "size": "32x32", "idiom": "mac", "filename": "icon-32@2x.png", "scale": "2x" },
    { "size": "128x128", "idiom": "mac", "filename": "icon-128.png", "scale": "1x" },
    { "size": "128x128", "idiom": "mac", "filename": "icon-128@2x.png", "scale": "2x" },
    { "size": "256x256", "idiom": "mac", "filename": "icon-256.png", "scale": "1x" },
    { "size": "256x256", "idiom": "mac", "filename": "icon-256@2x.png", "scale": "2x" },
    { "size": "512x512", "idiom": "mac", "filename": "icon-512.png", "scale": "1x" },
    { "size": "512x512", "idiom": "mac", "filename": "icon-512@2x.png", "scale": "2x" }
  ],
  "info": {
    "version": 1,
    "author": "icon-creator-skills"
  }
}
```

## macOS-specific design considerations

### Rounded square mask

Unlike iOS (squircle applied at runtime), macOS app icons are **expected to include the rounded-square shape themselves**. The standard macOS icon shape:
- Rounded square with corner radius ≈ 22.37% of side length
- Optional drop shadow at the bottom (Apple's design convention since Big Sur)

The skill **does not auto-apply** this shape (would conflict with non-app-icon use cases). Users producing macOS app icons should provide a master that already incorporates the rounded-square aesthetic, or pass `--macos-shape rounded-square` (planned post-v1).

### Transparent edges

macOS icons can have transparent areas (unlike iOS marketing 1024). The squircle shape is visually expected but not strictly required by the OS.

### Light / dark variants

Apple introduced separate appearance variants. We do not produce light/dark by default. If the master is mode-specific, the user should run `app-icon-pack` twice with different masters and merge the appiconsets manually. Future enhancement: `--master-light` and `--master-dark` arguments.

## Integration

1. Open Xcode → Mac app project → `Assets.xcassets`
2. Drag `AppIcon.appiconset/` into the catalog (replace existing)
3. Verify in target settings: General → App Icon → AppIcon

## Validation

When `validate=true`:
- `Contents.json` parses against Apple schema
- All 10 PNG files exist and match dimensions
- Format is RGBA (alpha permitted)
