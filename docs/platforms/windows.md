# Platform: Windows

Microsoft Store / UWP / Win32 packaging tiles. Smaller scope than iOS/Android, mostly square logos at standardized sizes.

## Output layout

```
windows/
├── Square44x44Logo.png       # taskbar / app list
├── Square71x71Logo.png       # small Start tile
├── Square150x150Logo.png     # medium Start tile (most prominent)
├── Square310x310Logo.png     # large Start tile
├── Wide310x150Logo.png       # wide Start tile (optional)
├── StoreLogo.png             # 50×50 — used in Microsoft Store listing
└── manifest-snippet.xml      # snippet for AppxManifest.xml
```

## Size matrix

| Filename | Size | Use |
|---|---|---|
| Square44x44Logo | 44×44 | Taskbar, Alt+Tab, app list |
| Square71x71Logo | 71×71 | Small Start tile |
| Square150x150Logo | 150×150 | Medium Start tile (primary) |
| Square310x310Logo | 310×310 | Large Start tile |
| Wide310x150Logo | 310×150 | Wide Start tile |
| StoreLogo | 50×50 | Microsoft Store listing |

All PNG, can be transparent or opaque.

## Wide tile composition

The 310×150 wide tile is non-square. Master is centered in the **right half** by convention (Microsoft templates) with the left half used for app name text. The skill produces a wide tile with the master centered overall (no text), since we don't bundle fonts. Users wanting the text-on-left layout can supply a custom wide-tile via `--wide-tile path/to/wide.png`.

## `manifest-snippet.xml`

A snippet to merge into the user's `Package.appxmanifest`:

```xml
<Applications>
  <Application Id="App">
    <uap:VisualElements
        DisplayName="{app-name}"
        Square150x150Logo="Assets\Square150x150Logo.png"
        Square44x44Logo="Assets\Square44x44Logo.png"
        BackgroundColor="{bg-color}">
      <uap:DefaultTile
          Square71x71Logo="Assets\Square71x71Logo.png"
          Square310x310Logo="Assets\Square310x310Logo.png"
          Wide310x150Logo="Assets\Wide310x150Logo.png" />
      <uap:SplashScreen Image="Assets\SplashScreen.png" />
    </uap:VisualElements>
  </Application>
</Applications>
```

The snippet references file paths assuming the user copies the `windows/*.png` files to their project's `Assets/` directory.

## Quirks

### Transparent vs opaque

Windows tiles can be transparent. If transparent, the OS uses the manifest's `BackgroundColor` to fill behind the icon. We emit transparent PNGs by default and rely on `BackgroundColor` (set to `bg-color`).

### Plated vs tile-style

Some apps prefer the entire tile to be the icon (logo bleeds to edges). Others prefer a centered logo with consistent padding. The skill produces centered with ~10% padding by default; users can override with `--windows-padding 0` for full-bleed.

### Splash screen

`SplashScreen.png` (620×300) is referenced in the manifest snippet but not produced by `app-icon-pack` (it's a different asset, more like a marketing image than an icon). Out of scope for v1.

### Microsoft Store hi-res

The Microsoft Store accepts a much larger Store Logo (300×300). We ship 50×50 (the in-tile use); merchants targeting the Store can upload an arbitrary larger logo separately. Future enhancement: optional 300×300.

## Integration

1. Copy `windows/*.png` into your UWP project's `Assets/` directory
2. Merge the contents of `manifest-snippet.xml` into your `Package.appxmanifest`
3. Re-build and re-package

## Validation

When `validate=true`:
- All declared PNG files exist with exact pixel dimensions
- `manifest-snippet.xml` is valid XML
- Wide tile aspect ratio is 310:150 ± 1px tolerance
