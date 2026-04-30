# Platform: watchOS

Apple Watch app icons. Different watch case sizes generate different point→pixel mappings; we ship the union to cover all current watches.

## Size matrix

| Idiom | Use | Pixel size | Watch case |
|---|---|---|---|
| Notification Center | 24mm | 48 | 38mm series |
| Notification Center | 27.5mm | 55 | 42mm series |
| Companion Settings | 29mm @2x | 58 | all |
| Companion Settings | 29mm @3x | 87 | all |
| Home Screen (38mm) | 40mm @2x | 80 | 38mm |
| Home Screen (42mm) | 44mm @2x | 88 | 42mm |
| Short Look (38mm) | 86mm @2x | 172 | 38mm |
| Short Look (42mm) | 98mm @2x | 196 | 42mm |
| Long Look (44mm) | 50mm @2x | 100 | 44mm |
| App Store | marketing | 1024 | all |

Total distinct sizes: **10** (some overlap with iPhone sizes but stored separately).

## Output layout

```
watchos/
└── AppIcon.appiconset/
    ├── icon-watch-24.png
    ├── icon-watch-27.5.png
    ├── icon-watch-29@2x.png
    ├── icon-watch-29@3x.png
    ├── icon-watch-40@2x.png
    ├── icon-watch-44@2x.png
    ├── icon-watch-86@2x.png
    ├── icon-watch-98@2x.png
    ├── icon-watch-50@2x.png
    ├── icon-watch-1024.png
    └── Contents.json
```

## `Contents.json`

Each entry uses `idiom: "watch"` and includes `role` and `subtype`. The full schema:

```json
{
  "images": [
    {
      "size": "24x24",
      "idiom": "watch",
      "scale": "2x",
      "role": "notificationCenter",
      "subtype": "38mm",
      "filename": "icon-watch-24.png"
    },
    {
      "size": "27.5x27.5",
      "idiom": "watch",
      "scale": "2x",
      "role": "notificationCenter",
      "subtype": "42mm",
      "filename": "icon-watch-27.5.png"
    },
    {
      "size": "29x29",
      "idiom": "watch",
      "scale": "2x",
      "role": "companionSettings",
      "filename": "icon-watch-29@2x.png"
    },
    {
      "size": "29x29",
      "idiom": "watch",
      "scale": "3x",
      "role": "companionSettings",
      "filename": "icon-watch-29@3x.png"
    },
    {
      "size": "40x40",
      "idiom": "watch",
      "scale": "2x",
      "role": "appLauncher",
      "subtype": "38mm",
      "filename": "icon-watch-40@2x.png"
    },
    {
      "size": "44x44",
      "idiom": "watch",
      "scale": "2x",
      "role": "appLauncher",
      "subtype": "40mm",
      "filename": "icon-watch-44@2x.png"
    },
    {
      "size": "86x86",
      "idiom": "watch",
      "scale": "2x",
      "role": "quickLook",
      "subtype": "38mm",
      "filename": "icon-watch-86@2x.png"
    },
    {
      "size": "98x98",
      "idiom": "watch",
      "scale": "2x",
      "role": "quickLook",
      "subtype": "42mm",
      "filename": "icon-watch-98@2x.png"
    },
    {
      "size": "50x50",
      "idiom": "watch",
      "scale": "2x",
      "role": "quickLook",
      "subtype": "44mm",
      "filename": "icon-watch-50@2x.png"
    },
    {
      "size": "1024x1024",
      "idiom": "watch-marketing",
      "scale": "1x",
      "filename": "icon-watch-1024.png"
    }
  ],
  "info": {
    "version": 1,
    "author": "icon-creator-skills"
  }
}
```

## watchOS-specific quirks

### Round mask at runtime

Apple Watch app icons are masked into a circle by the OS. The icon should:
- Be designed within the central ~80% of the canvas (think "circular safe zone")
- Have minimal detail at the edges (gets cropped by mask)

The skill **doesn't enforce** circular safe zone but emits a warning if subject content extends to the edges (heuristic: alpha non-empty pixels in the outer 10% of canvas).

### Marketing 1024

Same rule as iOS — must not have alpha. Skill auto-flattens onto `bg-color` and warns.

### Source quality

watchOS sizes are small (24–100). Master master should be ≥ 1024 for crisp downsampling. Lanczos filter handles this fine, but starting from 256 will look mushy at 100×100 and below.

## Integration

1. Open Xcode → Watch app target → `Assets.xcassets`
2. Drag `AppIcon.appiconset/` into the catalog
3. Verify the target uses it: Watch app target → General → App Icons Source → AppIcon

## Validation

When `validate=true`:
- `Contents.json` parses; all required `role`/`subtype` combos present
- All PNG files exist and match dimensions
- Marketing 1024 has no alpha
