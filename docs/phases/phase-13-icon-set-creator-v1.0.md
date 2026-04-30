# Phase 13: `icon-set-creator` v1.0

Coherent icon family generation. Takes a list of subjects, locks a style anchor, produces N icons that match in palette, stroke, corner radius, and overall look.

## Goal

```
> /icon-set-creator icons:'["home","search","profile","settings","messages","notifications","calendar","camera","music","video","files","help"]' \
                    --style-preset flat --colors "#2563EB,#1E40AF"
```

produces 12 visually-coherent icons. Anyone scanning the preview grid recognizes them as a set.

## Deliverables

### Skill folder

```
skills/icon-set-creator/
├── SKILL.md
├── scripts/
│   └── generate_set.py
└── tests/
    └── test_set.py
```

### Skill flow

1. If `--reference-icon` provided, use it as anchor; else generate first icon and use as anchor (with 3 candidates, user-pick OR auto-pick best)
2. Extract style guide from anchor (palette, edge density, fill style)
3. Lock prompt template: same template for every member, only `subject` varies
4. Generate each icon in the list (potentially in parallel within rate limits)
5. Validate each via `consistency_checker` against the anchor (threshold 0.80)
6. Retry failures up to 3 times
7. Compose `preview.png` grid showing all icons together
8. Generate `style-guide.md` describing the locked style
9. Optional: chain into `app-icon-pack` if user wants a particular member as an app icon

## Implementation steps

1. Implement style-guide extraction in `vision_analyzer` (combination of palette, edge density, gradient prevalence, art style descriptor — bundled into a structured `IconSetStyleGuide`)
2. Implement `generate_set.py`:
   - Parse args: `icons` (list), `--style-preset`, `--colors`, `--reference-icon`, `--set-name`, `--stroke-width`, `--corner-radius`, `--seed-base`
   - Anchor resolution (provided or first-icon-generated)
   - Style guide extraction
   - Per-icon generation with consistent prompt template
   - Consistency check + retry per member
3. Compose preview grid (`image_utils.compose_grid` with labels)
4. Generate `style-guide.md` from extracted guide + run inputs
5. Tests with a synthetic anchor + small icon list

## Acceptance criteria

### Automated
- Generate 4-icon set from synthetic anchor; all 4 produced; consistency scores ≥ 0.80 average
- preview.png exists and is composed grid
- style-guide.md exists with all expected sections

### Manual / by-eye

**The 12-icon navigation set is the headline test.**

```
> /icon-set-creator \
    icons:'["home","search","profile","settings","messages","notifications","calendar","camera","music","video","files","help"]' \
    --style-preset flat --colors "#2563EB,#1E40AF"
```

Acceptance:
- All 12 icons recognizable as the labeled subject
- All 12 read at the same stroke / fill weight (no outliers that look noticeably "thicker" or "thinner")
- All 12 use the locked palette (or close approximations)
- All 12 read at 24px (small-size readability test)
- preview.png "looks like a set" — a designer wouldn't say "where did that one come from?"

Repeat for at least 2 more presets (`outline`, `ios-style`) and confirm coherence holds.

### Documentation
- SKILL.md
- README with the 12-icon example
- "When to add to an existing set" pattern documented (user passes `--reference-icon` from earlier output)

## Test in OpenCode

End-to-end:
```
> /icon-set-creator icons:'["home","search","profile","settings"]' \
                    --style-preset flat --colors "#2563EB,#1E40AF"
```

Confirm:
- 4 icons + preview + style-guide
- All visually coherent
- style-guide.md describes the locked style

## Out of scope for phase 13

- "Add to existing set" mode that reads previous style-guide.md and extends (post-v1)
- Auto icon list generation from feature description (post-v1)
- Negative-space variant pairs (filled + outlined twin sets) (post-v1)
- Multi-shot per-member with auto-pick (works through inheritance from phase 03 patterns; default 1 per member to control cost)

## Risks

- **Cost can be significant.** 12 icons × 1 base + (up to 3 retries average 0.5) = ~18 calls. Pre-run estimate confirmation enforced.
- **Some subjects are harder to render in some presets.** "Settings" in `watercolor` is awkward. Quality validator + consistency checker may keep retrying. We cap retries; surface "best attempt" with warning.
- **Anchor selection matters a lot.** A bad anchor poisons the entire set. When generating the first icon to use as anchor, default to 3 candidates with `quality_validator`-based auto-pick.

## Dependencies on prior work

- Phases 01–03 (icon-creator pattern)
- Phase 09 (consistency_checker, vision_analyzer style extraction)
- Phase 11 (style-guide.md template pattern from mascot-creator)
