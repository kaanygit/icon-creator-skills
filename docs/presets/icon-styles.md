# Icon style presets

The full catalog of style presets supported by `icon-creator` and `icon-set-creator`. Each preset declares a model recommendation, a style phrase used in prompt building, and negative-prompt extras.

The canonical machine-readable source is `shared/presets/icon_styles.yaml`. This document is the human-readable companion describing intent, fit, and example outputs. Current model IDs and retired fallbacks are tracked centrally in [model-matrix.md](model-matrix.md).

## How to choose a preset

| If the user says... | Use preset |
|---|---|
| "modern", "minimal", "clean" | `flat` |
| "iOS app icon", "Apple-style" | `ios-style` |
| "Material Design", "Android-native" | `material` |
| "frosted glass", "translucent", "glassy" | `glass-morphism` |
| "outlined", "stroke", "line icon" | `outline` |
| "isometric", "3D blocks" | `3d-isometric` |
| "vintage", "physical buttons", "real-looking" | `skeuomorphic` |
| "soft shadows", "embossed" | `neumorphic` |
| "gradient", "smooth color transitions" | `gradient` |

When unsure, default is `flat`.

## Preset catalog

### `flat`

Modern flat illustration. Solid colors, no gradients, no shadows. The 2010s+ default for digital UI.

**Style phrase**: "flat-style icon, solid colors, no gradients, simple geometry"
**Negative**: "gradient, shadow, depth, 3d, photorealistic"
**Best for**: app icons, UI icons, favicons, logo-marks
**Models**: primary `google/gemini-3.1-flash-image-preview`, fallback `black-forest-labs/flux.2-pro`

### `gradient`

Smooth color gradients on otherwise flat shapes. Common in modern app icons (Instagram, Spotify).

**Style phrase**: "smooth color gradient, modern app icon style, vibrant"
**Negative**: "flat solid colors, photorealistic, harsh"
**Best for**: app icons, brand-mark icons
**Models**: primary `google/gemini-3.1-flash-image-preview`, fallback `black-forest-labs/flux.2-pro`

### `glass-morphism`

Frosted-glass / translucent panel look. Apple-style "liquid glass," translucent layered shapes with soft blur.

**Style phrase**: "glass morphism, frosted blur, translucent layers, soft highlights"
**Negative**: "opaque, flat, vector-only"
**Best for**: app icons (especially iOS / macOS), modern UI icons
**Models**: primary `google/gemini-3.1-flash-image-preview`, fallback `black-forest-labs/flux.2-pro`

### `outline`

Line-art icons. Single stroke weight, no fills. "Hero Icons" or "Lucide" style.

**Style phrase**: "outline icon, single stroke weight, no fill, line art"
**Negative**: "filled, solid, gradient, shadow"
**Best for**: UI icons (especially in icon sets), favicons in some brand systems
**Models**: primary `google/gemini-3.1-flash-image-preview`, fallback `black-forest-labs/flux.2-pro`

### `3d-isometric`

Isometric 3D-look icons (30° angle). Modern fintech / SaaS site illustration style.

**Style phrase**: "isometric 3D icon, 30 degree projection, soft shadows, geometric"
**Negative**: "flat 2d, photorealistic perspective"
**Best for**: feature-set icons on marketing sites, brand-mark icons with depth
**Models**: primary `google/gemini-3.1-flash-image-preview`, fallback `black-forest-labs/flux.2-pro`

### `skeuomorphic`

Physical-object look. Real materials, depth, shadows. Pre-iOS-7 Apple style.

**Style phrase**: "skeuomorphic, photorealistic materials, leather or metal texture, deep shadows, embossed"
**Negative**: "flat, abstract, vector"
**Best for**: niche use (retro feel, physical-tool brand metaphors)
**Models**: primary `google/gemini-3.1-flash-image-preview`, fallback `black-forest-labs/flux.2-pro`

### `neumorphic`

Soft-UI / "Neumorphism." Subtle inner and outer shadows on monochromatic backgrounds.

**Style phrase**: "neumorphic, soft inner and outer shadows, monochromatic, subtle depth"
**Negative**: "high contrast, vivid colors, flat"
**Best for**: minimal UI icon sets, dashboard widgets
**Models**: primary `google/gemini-3.1-flash-image-preview`, fallback `black-forest-labs/flux.2-pro`

### `material`

Google Material Design icon style. Round corners, dual-tone, balanced negative space.

**Style phrase**: "Google Material Design icon, dual-tone, balanced, rounded corners"
**Negative**: "ornate, photorealistic, hand-drawn"
**Best for**: Android app icons, web apps targeting Material aesthetic
**Models**: primary `google/gemini-3.1-flash-image-preview`, fallback `black-forest-labs/flux.2-pro`

### `ios-style`

Apple iOS app-icon style. Squircle implied (rendered in `app-icon-pack`), simple subject on color or gradient bg, polished.

**Style phrase**: "iOS app icon style, polished, single subject on solid or gradient background"
**Negative**: "outlined, line art, busy"
**Best for**: iOS app icons
**Models**: primary `google/gemini-3.1-flash-image-preview`, fallback `black-forest-labs/flux.2-pro`

## Adding a new preset

1. Add an entry to `shared/presets/icon_styles.yaml`:
   ```yaml
   icon-creator:
     my-preset:
       template: my-preset.j2
       primary_model: ...
       fallback_models: [...]
       style_phrase: "..."
       negative_extras: "..."
       description: "Short human description"
   ```
2. Drop a Jinja template at `shared/presets/prompt_templates/icon-creator/my-preset.j2`
3. Add a section to this catalog explaining intent, fit, and recommended use
4. Add a snapshot test fixture for the new preset

No Python code change required.

## Preset × type matrix

Default presets per `type` when the user doesn't specify:

| Type | Default preset |
|---|---|
| `app-icon` | `flat` (mainstream) |
| `ui-icon` | `outline` (sets / interfaces) |
| `favicon` | `flat` (small-size readability) |
| `logo-mark` | `flat` (or `gradient` for branded marks) |

Users can override on every call.
