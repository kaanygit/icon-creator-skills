# Skill: `icon-set-creator`

Generate a coherent **family** of icons that share style, palette, stroke width, and visual rhythm. e.g. all 12 icons in a navigation bar, an entire feature-icon set for a marketing page, a sticker-pack of related concepts.

## Why this is a separate skill

Single-icon generation and set generation are different problems:

- **Single-icon** optimizes one output. Each call is independent.
- **Set generation** optimizes group consistency. Stroke width, fill style, palette, perspective, level of detail must match across all members.

Naive approach (calling `icon-creator` 12 times in a loop) fails because the model drifts between calls. We need a **style anchor**, batch consistency validation, and disciplined prompt templating.

## Inputs

| Name | Required | Type | Default | Description |
|---|---|---|---|---|
| `icons` | yes | list[string] | — | List of subjects: `["home", "search", "profile", "settings", ...]` |
| `style-preset` | yes | enum | — | All members share this preset. See [icon-styles](../presets/icon-styles.md) |
| `colors` | yes | list[string] | — | Hex palette, applied uniformly |
| `reference-icon` | no | path | — | Existing icon to anchor style from. If absent, the first generated icon becomes the anchor |
| `set-name` | no | string | derived | Used in output dir name |
| `stroke-width` | no | enum | preset default | `thin` \| `regular` \| `bold` — only meaningful for outline/line presets |
| `corner-radius` | no | enum | preset default | `sharp` \| `rounded` \| `pill` |
| `model` | no | string | preset-derived | OpenRouter model id |
| `output-dir` | no | path | `output/` | |
| `seed-base` | no | int | random | Base seed; each icon uses `seed-base + i` for variety within consistency |

## Output

```
output/{set-name}-{timestamp}/
├── style-guide.md               # documents the locked style
├── style-anchor.png             # the anchor used to enforce consistency
├── preview.png                  # grid of all icons for at-a-glance review
├── icons/
│   ├── home.png
│   ├── search.png
│   ├── profile.png
│   └── ... (one per requested subject)
├── metadata.json
└── logs/
    ├── consistency-checks.log
    └── openrouter.log
```

### `style-guide.md` contents

Auto-generated documentation of the locked style, useful for adding new icons later (humans or this skill on a future call):

```markdown
# Style guide: {set-name}

Generated 2026-04-29.

## Visual language
- Preset: flat
- Stroke width: regular (≈3px at 1024 canvas)
- Corner radius: rounded (8px)
- Fill style: solid, no gradients
- Perspective: front-facing, no depth cues

## Palette
- Primary: #2563EB
- Secondary: #1E40AF
- Background: transparent

## Composition
- Subject occupies ≈70% of canvas
- Centered, even padding ≈10%
- Single subject per icon, no compound elements

## To add new icons matching this set
> icon-set-creator --reference-icon {path/to/style-anchor.png} \
                   --colors "#2563EB,#1E40AF" \
                   icons:'["new-subject"]'
```

## Internal flow

```
1. parse_inputs
2. if reference-icon: anchor = load + analyze
   else: generate first icon as anchor with full preset prompt
3. style-guide = vision_analyzer.extract_style(anchor)
   # extracts: stroke width estimate, palette, corner radius, fill density, perspective
4. for each subject in icons:
       prompt = prompt_builder.build(
           preset, subject,
           anchor_hints=style-guide,
           palette=colors,
           seed=seed-base + i
       )
       image = openrouter_client.generate(model, prompt)
       image = image_utils.post_process(image)
       similarity = consistency_checker.score(image, anchor)
       if similarity < threshold:
           regenerate (max 3 attempts)
5. write all icons + style-guide.md + preview grid
```

## Consistency thresholds

`consistency_checker` compares each generated icon to the anchor on:

- **Color histogram similarity** ≥ 0.80 (palette match)
- **Edge density similarity** ≥ 0.70 (stroke weight match)
- **Perceptual hash distance** within tolerance (overall stylistic similarity)
- **Background uniformity** (all transparent, no incidental fills)

Default combined-score threshold: 0.80. Configurable per call via `--consistency-threshold`.

## Edge cases

- **Subject is hard to render in chosen preset.** e.g. `"settings"` icon in `watercolor` preset is awkward. Quality validator may flag; user can re-run with explicit per-subject overrides.
- **Anchor itself is poor.** First-icon strategy can fail if the anchor comes out badly. Mitigation: produce 3 anchor candidates first, pick best, then proceed.
- **Subject list is huge (100+).** Cost gets significant. Skill prints estimated cost and confirms above threshold.
- **Conflicting constraints.** e.g. `stroke-width: thin` with `style-preset: 3d-isometric` — preset wins, override is ignored with a warning.

## Acceptance criteria (phase 13)

- Generate a 12-icon navigation set (`home, search, profile, settings, messages, notifications, calendar, camera, music, video, files, help`) in `flat` preset
- Visual review: all 12 icons readable at 24px, palette matches, stroke weight consistent, no obvious outliers
- `consistency_checker` reports ≥0.80 average similarity to anchor across the set
- `preview.png` grid is coherent at a glance

## Dependencies

- All shared modules
- `consistency_checker` is critical here, more than in any other skill
- Optional invocation of `app-icon-pack` (less common; sets aren't usually app icons)

## Future work (not in v1)

- "Add to existing set" mode: point at an existing output directory, add new icons that match
- Auto-icon-naming from a feature description: "icons for a fitness tracking app" → skill proposes the list
- Negative-space variants automatically (filled vs outlined twin sets)
