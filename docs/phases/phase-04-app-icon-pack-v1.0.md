# Phase 04: `app-icon-pack` v1.0

Master image → asset pack for **iOS, Android, and Web**. The first packaging skill. Brings the toolkit to "demo-shippable" — combined with phases 01–03, a user can go from prompt to App Store / Play Store / browser-ready files.

## Goal

```
> /app-icon-pack --master output/fox-icon-{ts}/master.png \
                 --app-name "Foxy" \
                 --platforms ios,android,web
```

produces a directory + zip containing valid `AppIcon.appiconset/`, Android mipmap directories with adaptive icon, full web favicon set with `manifest.json` — all drop-in usable.

## Deliverables

### Skill folder

```
skills/app-icon-pack/
├── SKILL.md
├── scripts/
│   ├── pack.py                    # entrypoint
│   ├── ios.py                     # iOS-specific packaging
│   ├── android.py                 # Android-specific (incl. adaptive icon)
│   └── web.py                     # Web-specific (favicon, manifest, etc.)
└── tests/
    ├── test_ios.py
    ├── test_android.py
    └── test_web.py
```

### Preset content

```
shared/presets/platforms/
├── ios.yaml             # all 17 sizes + Contents.json idiom mapping
├── android.yaml         # density buckets + adaptive icon math
├── web.yaml             # favicon, apple-touch, PWA, mstile, og
└── schemas/
    ├── ios-contents.schema.json
    └── web-manifest.schema.json
```

### New shared utilities

- `shared/image_utils.write_ico_multires`
- `shared/image_utils.rasterize_svg` (cairosvg primary, resvg fallback)
- `shared/image_utils.bg_remove` (rembg)
- `shared/image_utils.composite_on_bg`

## Implementation steps

1. Add native deps (`Pillow`, `cairosvg` or `resvg-py`, `rembg[cpu]`) to pyproject; document install commands in README
2. Implement `image_utils.bg_remove` and `clean_alpha_edges`
3. Implement `image_utils.write_ico_multires`
4. Implement `image_utils.rasterize_svg`
5. Author the three platform YAMLs with exact size tables (per [platforms/ios.md](../platforms/ios.md), [platforms/android.md](../platforms/android.md), [platforms/web.md](../platforms/web.md))
6. Write `ios.py`:
   - Resize master to all 17 sizes (lanczos for PNG master, fresh raster for SVG)
   - Generate `Contents.json` from YAML schema
   - Marketing 1024 with alpha auto-flatten + warning
7. Write `android.py`:
   - Resize to 5 density buckets
   - Generate adaptive icon (foreground = master scaled to 72dp safe zone, background = solid bg-color)
   - Write `mipmap-anydpi-v26/ic_launcher.xml`
   - Generate notification icon (24×24 monochrome via thresholding)
   - Generate Play Store 512×512 (opaque)
8. Write `web.py`:
   - All favicon variants
   - `manifest.json` with maskable + any purposes
   - `browserconfig.xml`
   - `safari-pinned-tab.svg` (only if monochrome conversion succeeds; skip + warn otherwise)
   - `og-image.png` 1200×630
9. Write `pack.py` orchestrator:
   - Validate master (square, ≥1024 PNG or any-size SVG)
   - Dispatch to per-platform modules in parallel
   - Generate per-run README.md with integration instructions per platform
   - Optional zip
10. Validation routines per [app-icon-pack.md](../skills/app-icon-pack.md)
11. Tests: synthetic master → run pack → assert all expected files exist with correct dimensions, all manifests parse, ICO decodes

## Acceptance criteria

### Automated
- Run `pack.py` on a synthetic 1024×1024 RGBA master
- All declared files exist with exact pixel dimensions (verified by reading PNG headers)
- `Contents.json` validates against bundled schema
- `manifest.json` validates against bundled W3C schema
- `browserconfig.xml` parses as valid XML
- `favicon.ico` decodes back into 16/32/48 entries

### Manual / by-eye
1. **iOS**: Drag generated `AppIcon.appiconset/` into a real Xcode project, build, run on simulator. Confirm icon shows on home screen, all sizes look crisp.
2. **Android**: Copy `android/` contents into a real Android Studio project's `app/src/main/res/`. Re-build. Confirm:
   - Launcher shows the icon
   - Adaptive icon previews correctly in Android Studio (Resource Manager → drawable → ic_launcher → preview)
   - Foreground content fits within safe zone (no clipping on circle-mask launchers)
3. **Web**: Drop `web/` into a real test page's root. Open in Safari, Chrome, Firefox, Edge. Confirm:
   - Favicon shows in tab
   - "Add to Home Screen" on iOS produces correct icon
   - "Install app" on Chrome produces correct icon
   - OpenGraph preview works (paste link in Slack or use a debug tool)
4. **Adaptive icon edge case**: Run with a master where subject extends to canvas edges. Confirm the safe-zone scaling kicks in and content doesn't get clipped.

### Documentation
- Update SKILL.md with all flags
- README.md per-platform integration instructions (verified against the manual tests above)

## Test in OpenCode

End-to-end:
```
> /icon-creator "minimalist mountain icon, dawn" --style-preset flat
... produces output/mountain-{ts}/master.png

> /app-icon-pack --master output/mountain-{ts}/master.png --app-name "Peak" \
                 --platforms ios,android,web
```

Confirm the entire pipeline runs through OpenCode and produces a working asset pack.

## Out of scope for phase 04

- macOS / watchOS / Windows (phase 05)
- Live preview server (`--serve`) — future enhancement
- Splash-screen generation
- Themed adaptive icons (Android 13+ dynamic color)

## Risks

- **R-004**: Adaptive icon safe zone errors. Mitigated by hardcoded math + visual safe-zone preview as part of run output.
- **R-010**: cairosvg / rembg native deps fail to install. Mitigate with clear install docs and resvg-py fallback.
- **Manifest spec edge cases**: Some PWA tooling expects extra fields (start_url, scope). Document `--manifest-extras` for users with specific needs.

## Dependencies on prior work

- Phase 00 (config, errors, logging)
- A working `icon-creator` from phase 01–03 to produce the master (or any user-supplied master)
