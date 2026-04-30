# Skill: `app-icon-pack`

Take a master image (PNG or SVG) and produce a complete, ready-to-ship asset pack for any combination of iOS, macOS, watchOS, Android, Web, and Windows. Generates platform-required boilerplate (`Contents.json`, `manifest.json`, `browserconfig.xml`) and ships everything in a clean directory + zip.

## Purpose

Resizing one image into 60+ correctly-named, correctly-organized files is the most mechanical and most frustrating part of shipping an app. This skill compresses it to one call.

## Inputs

| Name | Required | Type | Default | Description |
|---|---|---|---|---|
| `master` | yes | path | — | Source image (PNG ≥ 1024×1024 or SVG) |
| `platforms` | no | list | `["ios", "android", "web"]` | Any of: `ios`, `macos`, `watchos`, `android`, `web`, `windows` |
| `app-name` | no | string | "MyApp" | Used in zip name and `manifest.json` |
| `bg-color` | no | hex | `#FFFFFF` | Used for Android adaptive-icon background and Microsoft Tile |
| `output-dir` | no | path | `output/` | |
| `zip` | no | bool | true | Also produce a zip alongside the directory |
| `validate` | no | bool | true | Run platform-specific validators (Contents.json schema, manifest schema) |

## Output

```
output/{app-name}-icons-{timestamp}/
├── ios/                          # if "ios" in platforms
│   └── AppIcon.appiconset/
│       ├── icon-20@2x.png … icon-1024.png
│       └── Contents.json
├── macos/                        # if "macos"
│   └── AppIcon.appiconset/
│       ├── icon-16.png … icon-1024@2x.png
│       └── Contents.json
├── watchos/                      # if "watchos"
│   └── AppIcon.appiconset/
│       └── ... full watch matrix
├── android/                      # if "android"
│   ├── mipmap-mdpi/ic_launcher.png
│   ├── mipmap-hdpi/ic_launcher.png
│   ├── mipmap-xhdpi/ic_launcher.png
│   ├── mipmap-xxhdpi/ic_launcher.png
│   ├── mipmap-xxxhdpi/ic_launcher.png
│   ├── mipmap-anydpi-v26/
│   │   └── ic_launcher.xml
│   ├── drawable/
│   │   ├── ic_launcher_foreground.png
│   │   └── ic_launcher_background.png
│   ├── notification/
│   │   └── ic_stat_24.png        # monochrome 24×24
│   └── play-store/
│       └── ic_launcher_512.png
├── web/                          # if "web"
│   ├── favicon.ico               # multi-res 16/32/48
│   ├── favicon-16x16.png
│   ├── favicon-32x32.png
│   ├── apple-touch-icon.png      # 180
│   ├── android-chrome-192x192.png
│   ├── android-chrome-512x512.png
│   ├── mstile-150x150.png
│   ├── safari-pinned-tab.svg
│   ├── manifest.json
│   ├── browserconfig.xml
│   └── og-image.png              # 1200×630
├── windows/                      # if "windows"
│   ├── Square44x44Logo.png
│   ├── Square71x71Logo.png
│   ├── Square150x150Logo.png
│   ├── Square310x310Logo.png
│   ├── Wide310x150Logo.png
│   └── StoreLogo.png             # 50×50
├── README.md                     # integration instructions per platform
└── {app-name}-icons.zip          # if zip=true
```

## Internal flow

```
1. validate_master(path):
     - exists, readable
     - PNG: ≥ 1024×1024, square, alpha channel preferred
     - SVG: parses cleanly, has square viewBox (if not square, warn)
2. determine_source_strategy:
     - SVG: rasterize at each target size (lossless)
     - PNG: lanczos resize from master
3. for each platform in platforms:
     - load size table from shared/presets/platforms/{platform}.yaml
     - for each entry: produce file at size with correct naming
     - generate platform metadata file (Contents.json / manifest.json / etc.)
     - special-case: Android adaptive icon (foreground + background separation,
                     108dp canvas with 72dp safe zone)
     - special-case: Web ICO multi-resolution
4. write README.md with per-platform integration instructions
5. if validate: run platform validators
6. if zip: produce zip alongside directory
```

## Platform-specific notes

Detailed size tables and quirks per platform are in [docs/platforms/](../platforms/). Brief summary here:

### iOS — see [docs/platforms/ios.md](../platforms/ios.md)
- Sizes: 17 distinct PNGs covering iPhone, iPad, iPad Pro, App Store
- `Contents.json` lists every entry with `idiom`, `size`, `scale`, `filename`
- iOS 13+ allows a single 1024 entry with proper "any" idiom; we ship the legacy matrix for compatibility

### macOS — see [docs/platforms/macos.md](../platforms/macos.md)
- 7 sizes × @1x and @2x = 14 PNGs
- Same `AppIcon.appiconset` structure as iOS

### watchOS — see [docs/platforms/watchos.md](../platforms/watchos.md)
- Notification, Companion Settings, Home Screen, Short Look, App Launcher, App Store
- Sizes vary by watch case (38mm, 40mm, 42mm, 44mm) — we ship the union

### Android — see [docs/platforms/android.md](../platforms/android.md)
- Five density buckets: mdpi (48), hdpi (72), xhdpi (96), xxhdpi (144), xxxhdpi (192)
- Adaptive icon: 108dp canvas, 72dp safe zone — content scaled to fit safe area
- Foreground + background as separate drawables; XML in `mipmap-anydpi-v26/`
- Notification icon: monochrome 24×24, white-on-transparent (auto-derived via thresholding)
- Play Store: 512×512 PNG (high-res icon), feature-graphic 1024×500 placeholder

### Web — see [docs/platforms/web.md](../platforms/web.md)
- Favicon multi-resolution ICO + individual PNG fallbacks
- Apple touch icon (180×180)
- PWA manifest with both 192 and 512 (maskable variant tagged)
- Microsoft Tile (150×150)
- Safari pinned tab as monochrome SVG
- Open Graph image 1200×630
- Auto-generated `manifest.json` and `browserconfig.xml`

### Windows — see [docs/platforms/windows.md](../platforms/windows.md)
- Microsoft Store / UWP / Win32 packaging tiles

## Adaptive-icon foreground/background separation

When the master has a transparent background, the foreground is the master itself, the background is a solid `bg-color` fill. When the master has an opaque background, we attempt to separate via `image_utils.bg_remove` (rembg). User can override with explicit `--foreground` and `--background` paths.

The 72dp safe zone math:

```
canvas = 432px (108dp × 4 for xxxhdpi)
safe_zone = 288px (72dp × 4)
content_max = safe_zone (centered)
padding = (canvas - content_max) / 2 = 72px
```

We scale the master to fit `content_max` and center it on a `canvas`-sized transparent canvas for the foreground; the background drawable is `canvas`-sized solid `bg-color`.

## Validation

If `validate=true`:

- `Contents.json` schema validation against Apple's published schema
- `manifest.json` validation against W3C Web App Manifest schema
- `browserconfig.xml` parses as valid XML and matches MS schema
- All declared filenames exist
- All PNGs at expected dimensions
- ICO contains expected resolutions

Failures emit warnings; the run still completes (the user may have intentional reasons).

## Edge cases

- **Master is not square.** We center-crop to square with a warning, OR pad to square if user passes `--no-crop`. Default is crop.
- **Master is opaque (no alpha).** Adaptive icon path uses `image_utils.bg_remove`; web favicon stays opaque (which is fine).
- **Master is < 1024.** Hard error — quality at that source is unacceptable for App Store. User must provide a larger master.
- **SVG with non-square viewBox.** Warning, then center within square viewBox before rasterizing.
- **Zip name collides with existing.** Append timestamp or counter.

## README.md auto-content

The skill writes a per-run `README.md` explaining how to drop the assets into Xcode, Android Studio, and a web project. Sample sections:

- "Drop `ios/AppIcon.appiconset/` into your Xcode project under `Assets.xcassets`. Verify it shows up in your target's `App Icon and Launch Images` setting."
- "Copy `android/` contents to `app/src/main/res/`. Re-build."
- "Copy `web/` contents to your site's root. Add this to your HTML head: …"

## Acceptance criteria

- **Phase 4** (v1.0): iOS + Android + Web. Drop into a real Xcode project, real Android Studio project, real web page — all platforms render correctly. Adaptive icon renders without clipping in Android Studio's preview.
- **Phase 5** (v1.1): macOS + watchOS + Windows. Smoke-tested in Xcode (Mac target) and Visual Studio.

## Dependencies

- `Pillow` (resize, format conversion, ICO writing)
- `cairosvg` or `resvg-py` (SVG rasterization)
- `image_utils` from shared
- `shared/presets/platforms/{platform}.yaml`
- Platform validator schemas in `shared/presets/schemas/`

## Future work (not in v1)

- Live preview server: `app-icon-pack --serve` opens a browser preview of the asset pack
- Splash-screen generation alongside icons
- Notification badge auto-derivation with user-configurable threshold
- Themed adaptive icons (Android 13+ dynamic color support)
- App Store / Play Store screenshot frame templates
