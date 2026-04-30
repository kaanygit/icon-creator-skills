# Platform: Web

The web has the most fragmented icon story of any platform: favicons, Apple touch icons, PWA manifest icons, Microsoft Tile, Safari pinned tabs, OpenGraph share images. `app-icon-pack` produces all of them and the boilerplate to wire them up.

## Output layout

```
web/
├── favicon.ico                  # multi-resolution: 16, 32, 48
├── favicon-16x16.png
├── favicon-32x32.png
├── apple-touch-icon.png         # 180×180
├── android-chrome-192x192.png
├── android-chrome-512x512.png
├── mstile-150x150.png
├── safari-pinned-tab.svg        # monochrome SVG for Safari pinned tabs
├── manifest.json                # Web App Manifest
├── browserconfig.xml            # Microsoft tile config
└── og-image.png                 # 1200×630 OpenGraph share image
```

## File details

### `favicon.ico`

Multi-resolution ICO containing 16, 32, 48 sizes. Older browsers fall back to this when no other icon is available. Written using `image_utils.write_ico_multires`.

### `favicon-16x16.png`, `favicon-32x32.png`

Standalone PNGs referenced from HTML `<link rel="icon">`. More reliable than ICO in modern browsers.

### `apple-touch-icon.png`

180×180 PNG. iOS Safari uses this when users add the page to their home screen. Must be **opaque** (Apple compositing flattens transparency to black). The skill auto-flattens onto `bg-color`.

### `android-chrome-192x192.png`, `android-chrome-512x512.png`

Used by Chrome Android when adding to home screen. Referenced in `manifest.json`. May be transparent.

The 512 entry is also used as the **maskable** icon when paired with `purpose: "maskable"` in the manifest. Chrome applies a circle/squircle mask at runtime, similar to Android adaptive icons. We don't auto-produce a separate maskable variant; users wanting one can pass `--maskable-padding 20` to add 20% padding around the subject.

### `mstile-150x150.png`

Microsoft Edge Tile icon (Windows pinned-site / Edge Start). 150×150, opaque, baked-on `bg-color`. Referenced in `browserconfig.xml`.

### `safari-pinned-tab.svg`

Safari's pinned-tab feature: a monochrome SVG icon that the browser recolors to match the user's chosen theme. Must be:
- Single color (we strip color, output black SVG)
- Solid shapes (no gradients, no opacity)
- viewBox `0 0 16 16` recommended for crispness at the rendered size

We derive this from the master via `png-to-svg` (potrace path, monochrome). If the master is too complex for clean monochrome conversion, we emit a warning and skip this file.

### `manifest.json`

W3C Web App Manifest. Generated content:

```json
{
  "name": "{app-name}",
  "short_name": "{app-name}",
  "icons": [
    {
      "src": "/android-chrome-192x192.png",
      "sizes": "192x192",
      "type": "image/png"
    },
    {
      "src": "/android-chrome-512x512.png",
      "sizes": "512x512",
      "type": "image/png",
      "purpose": "any"
    },
    {
      "src": "/android-chrome-512x512.png",
      "sizes": "512x512",
      "type": "image/png",
      "purpose": "maskable"
    }
  ],
  "theme_color": "{bg-color}",
  "background_color": "{bg-color}",
  "display": "standalone"
}
```

User can pass `--manifest-extras path/to/extras.json` to merge additional fields (start_url, scope, orientation, etc.).

### `browserconfig.xml`

Microsoft browser config:

```xml
<?xml version="1.0" encoding="utf-8"?>
<browserconfig>
    <msapplication>
        <tile>
            <square150x150logo src="/mstile-150x150.png"/>
            <TileColor>{bg-color}</TileColor>
        </tile>
    </msapplication>
</browserconfig>
```

### `og-image.png`

OpenGraph / Twitter card image, 1200×630. Used for social sharing previews. Mascot or logo composited on a brand-colored background, centered. Layout:
- Subject occupies central ~50% width
- App name optionally rendered as text below — disabled by default since we don't bundle fonts; users can pass `--og-text "App Name"` and a font path

## HTML snippet

The per-run README includes the HTML the user pastes into `<head>`:

```html
<link rel="icon" type="image/x-icon" href="/favicon.ico">
<link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png">
<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png">
<link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">
<link rel="mask-icon" href="/safari-pinned-tab.svg" color="#000000">
<link rel="manifest" href="/manifest.json">
<meta name="msapplication-config" content="/browserconfig.xml">
<meta name="theme-color" content="{bg-color}">

<!-- OpenGraph / Twitter -->
<meta property="og:image" content="https://yoursite.com/og-image.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="https://yoursite.com/og-image.png">
```

## Quirks and gotchas

### `apple-touch-icon` cannot be transparent

Safari composites the icon over a default background (white or theme color) but anti-aliasing artifacts and color-bleed at the edge are unpredictable. Always ship opaque. The skill auto-flattens.

### `safari-pinned-tab.svg` quirks

- Must be black (`fill="#000000"`)
- No gradients or opacity
- Safari ignores the SVG's `viewBox` rendering size and recolors based on user theme
- If conversion fails, the skill skips and the user falls back to the OS default tab icon — graceful degradation

### Maskable purpose

When `purpose: "maskable"` is set in the manifest, browsers apply a circle/squircle mask. The icon's "safe zone" is similarly the central ~80%. Without padding, Chrome may crop the subject. The skill ships the same 512 image for both purposes by default; users explicitly opting into maskable get a `--maskable-padding` argument.

### ICO encoding

Pillow's ICO writer is not great for sizes ≥ 256. We work around by encoding ≥256 entries as PNG-in-ICO, < 256 as BMP. `image_utils.write_ico_multires` handles this.

### OG image text rendering

Pillow's text rendering needs a font file. We don't ship one (licensing variability). Users wanting text on `og-image.png` pass `--og-font path/to/font.ttf` along with `--og-text`. Default is image-only.

## Validation

When `validate=true`:
- `manifest.json` validates against W3C schema
- `browserconfig.xml` parses as valid XML
- All declared icon files exist and have correct dimensions
- `favicon.ico` opens cleanly (multi-resolution decode succeeds)
- `safari-pinned-tab.svg` is monochrome (only one color in path fills)
- `og-image.png` is exactly 1200×630
