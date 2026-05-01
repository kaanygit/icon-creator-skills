# Quality feature: brand kit + style memory

Project-level defaults so a user working on the same product can run icon-creator and mascot-creator repeatedly without retyping their brand colors, preset, and model preferences. And: name a style once, recall it later.

## `.iconrc.json` — project brand kit

A file at the project root, optional. When present, every skill run in that directory automatically applies these defaults.

### Schema

```json
{
  "version": 1,
  "brand": {
    "name": "Acme",
    "palette": ["#2563EB", "#1E40AF", "#FBBF24", "#1F2937"],
    "primary_color": "#2563EB",
    "background_color": "#FFFFFF"
  },
  "icon_creator": {
    "default_type": "app-icon",
    "default_style_preset": "flat",
    "default_variants": 3
  },
  "mascot_creator": {
    "default_type": "stylized",
    "default_preset": "flat-vector",
    "default_personality": "friendly"
  },
  "app_icon_pack": {
    "default_platforms": ["ios", "android", "web"],
    "default_app_name": "Acme"
  },
  "model_overrides": {
    "icon-creator/flat": "sourceful/riverflow-v2-fast-preview",
    "mascot-creator/stylized/3d-toon": "black-forest-labs/flux.2-pro"
  },
  "cost": {
    "per_call_threshold_usd": 0.50,
    "session_threshold_usd": 5.00
  }
}
```

### Resolution order

When a skill runs, defaults are merged in order:

1. Skill hardcoded defaults
2. `~/.icon-skills/config.yaml` (user-global)
3. `.iconrc.json` (project)
4. Per-call CLI args (highest priority)

Anything the user explicitly passes wins. Project file is just convenience.

### Discovery

Look upward from the current directory for `.iconrc.json` until found or root. Common pattern: file lives at git root.

## Style memory

Once a user runs a skill that produced a result they like, they can **name and save** that style for re-use:

### Saving

```
$ icon-creator save-style \
    --from output/mountain-icon-20260429-153122 \
    --name acme-flat-style
Saved style 'acme-flat-style' to ~/.icon-skills/styles/acme-flat-style/
```

What's saved:
- `style-anchor.png` (the master from the source run)
- `style-guide.md` (auto-generated description of palette, art-style descriptor, etc.)
- `metadata.json` (link back to the source run, the prompt that produced it, the preset used)

### Recall

```
$ icon-creator "rocket icon" --style acme-flat-style
```

This loads the saved style as if `--reference-image style-anchor.png --colors <palette>` had been passed.

### Listing / removing

```
$ icon-skills styles list
acme-flat-style       (saved 2026-04-29, used 12 times)
spring-marketing-vibe (saved 2026-04-15, used 3 times)

$ icon-skills styles remove spring-marketing-vibe
```

### Per-skill scope

Style memory is **skill-aware**. Saving an icon-creator style and trying to recall it from mascot-creator emits a warning that the style was created for a different skill. The recall still proceeds (the anchor + palette can be useful), but the user knows.

## Brand-kit-driven set generation

When a `.iconrc.json` is present and the user runs `icon-set-creator` without `colors` or `style-preset`, the brand kit fills them in. The user just supplies the icons list.

```bash
$ icon-set-creator icons:'["home","search","profile","settings"]'
# Resolves to:
#   colors: from .iconrc.json brand.palette
#   style-preset: from .iconrc.json icon_creator.default_style_preset
```

This makes "produce a coherent set in our brand style" a one-liner once the brand kit is set up.

## Style guide auto-generation

Both `icon-set-creator` and `mascot-creator` produce a `style-guide.md` that documents the locked style. This file is intended to be:

- Committed to the repo as part of brand assets
- Shared with designers / team members so future contributions match
- Re-used as a reference for future runs

Sample for an icon set:

```markdown
# Style guide: acme-navigation-icons

Generated 2026-04-29 by icon-set-creator v1.0.

## Visual language
- Preset: flat
- Stroke: not applicable (filled)
- Corner radius: rounded (8px effective at 1024 canvas)
- Fill: solid, no gradients
- Perspective: front-facing

## Palette
- Primary: #2563EB
- Secondary: #1E40AF
- Accent: #FBBF24
- Background: transparent

## Composition
- Subject occupies ≈70% of canvas
- Centered, even ≈10% padding

## To extend this set
> icon-set-creator --reference-icon style-anchor.png \
                   --colors "#2563EB,#1E40AF" \
                   icons:'["new-subject"]'
```

## Privacy and portability

`.iconrc.json` is meant to be **committed**. It contains brand info that's already public when the product ships.

`~/.icon-skills/styles/*` is **per-user**, lives in the home directory. Users can sync it via dotfile management if they want it across machines.

Neither contains secrets. API keys are exclusively in env vars.

## Out of scope for v1

- Brand-kit GUI / web UI for editing
- Style-memory cloud sync
- Team-shared style libraries
- Auto-suggesting a brand-kit setup based on existing project assets

These are obvious next steps once the v1 foundation lands.
