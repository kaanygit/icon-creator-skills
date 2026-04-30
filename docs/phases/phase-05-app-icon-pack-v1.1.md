# Phase 05: `app-icon-pack` v1.1 — macOS, watchOS, Windows

Extend `app-icon-pack` to cover the remaining platforms: macOS, watchOS, Windows. Same architecture as phase 04, lower stakes (smaller user base per platform).

## Goal

`--platforms macos,watchos,windows` produces working asset packs for each, drop-in usable in Xcode (Mac/Watch targets) and Visual Studio / UWP projects.

## Deliverables

### Skill scripts

```
skills/app-icon-pack/scripts/
├── macos.py
├── watchos.py
└── windows.py
```

### Preset content

```
shared/presets/platforms/
├── macos.yaml
├── watchos.yaml
└── windows.yaml
```

## Implementation steps

1. Author the three platform YAMLs (per [platforms/macos.md](../platforms/macos.md), [platforms/watchos.md](../platforms/watchos.md), [platforms/windows.md](../platforms/windows.md))
2. Write `macos.py`:
   - 10 PNGs (16/32/128/256/512 × @1x and @2x)
   - `Contents.json` with `idiom: mac`
3. Write `watchos.py`:
   - 10 PNGs covering notification, settings, launcher, quickLook for both 38mm and 42mm subtypes
   - `Contents.json` with `idiom: watch` + `role` + `subtype`
   - Watch-specific edge warning (heuristic for content extending to outer 10%, since Watch masks to circle)
4. Write `windows.py`:
   - 6 PNGs (Square44, Square71, Square150, Square310, Wide310x150, StoreLogo)
   - `manifest-snippet.xml`
5. Wire into `pack.py` orchestrator
6. Tests: similar to phase 04 — synthetic master → assert all files exist with correct dimensions and metadata files parse

## Acceptance criteria

### Automated
- Same suite as phase 04 extended to the three new platforms
- All PNGs exist with correct dimensions
- `Contents.json` files parse against schema
- `manifest-snippet.xml` is valid XML

### Manual / by-eye
1. **macOS**: Drop `macos/AppIcon.appiconset/` into a real Mac app target in Xcode. Build, run, confirm dock icon and About window icon look correct. Eyeball at multiple zoom levels (16, 32, 256, 512).
2. **watchOS**: Drop `watchos/AppIcon.appiconset/` into a real Watch app target. Build to a Watch simulator (or device). Confirm icon appears on home screen, in companion settings.
3. **Windows**: Copy PNGs into a sample UWP project's `Assets/`, merge manifest snippet. Build and deploy locally. Confirm tile shows on Start menu, taskbar icon correct.

### Edge cases verified
- **Mac without rounded-square baked into master**: documented warning that macOS expects rounded square; user gets the icon as-is.
- **Watch icon with edge-extending content**: warning emitted; user can ignore if they know what they're doing.

### Documentation
- Update SKILL.md to mention new platform flags
- Per-platform integration instructions added to per-run README

## Test in OpenCode

```
> /app-icon-pack --master output/mountain-{ts}/master.png --app-name "Peak" \
                 --platforms macos,watchos,windows
```

Confirm:
- Three new platform directories created
- `manifest-snippet.xml` present for Windows
- Per-platform integration instructions in run README

## Out of scope for phase 05

- visionOS (Apple Vision Pro) — needs entirely different asset format with depth layers; future
- Microsoft Store hi-res 300×300 (we ship 50×50 in v1)
- macOS light/dark variant icons (future, requires `--master-light` and `--master-dark`)
- Themed Android icons (future)
- Splash screens for any platform

## Risks

- **macOS rounded-square convention**: We don't auto-apply the shape (would conflict with non-app-icon use). Document clearly; user supplies a master that incorporates the desired shape.
- **Watch edge-clipping**: The skill warns but doesn't auto-pad. Users wanting circular safe zone can pre-pad their master via `image_utils.pad_square` with extra padding.

## Dependencies on prior work

- Phase 04 — most of the orchestrator and shared image-utils already in place
