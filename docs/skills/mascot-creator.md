# Skill: `mascot-creator`

Generate a brand mascot or character with optional pose, expression, view, and outfit variants. The hardest skill in the toolkit — character consistency across variants is an unsolved problem at the prompt level, so this skill leans heavily on image-to-image flows.

## Purpose

A user describes a character ("wise old owl, professor, glasses"), picks a type and preset, optionally requests pose / expression / view / outfit variants, and gets back a complete character package: master, character sheet, and every requested variant — all preserving the same visual identity.

## Inputs

| Name | Required | Type | Default | Description |
|---|---|---|---|---|
| `description` | yes | string | — | Character description |
| `type` | yes | enum | — | `stylized` \| `realistic` \| `artistic` |
| `preset` | no | enum | type-default | See [mascot-types catalog](../presets/mascot-types.md) |
| `personality` | no | string | — | "friendly", "wise", "playful" — injected into prompt |
| `poses` | no | list | `["idle"]` | e.g. `["idle", "waving", "thinking", "celebrating"]` |
| `expressions` | no | list | `["neutral"]` | e.g. `["happy", "sad", "surprised", "angry"]` |
| `views` | no | list | `["front"]` | e.g. `["front", "side", "3-quarter", "back"]` |
| `outfits` | no | list | `[]` | Outfit variants per master e.g. `["casual", "formal", "sporty"]` |
| `reference-image` | no | path | — | Use existing character/style as anchor |
| `mascot-name` | no | string | derived | Used in output dir name |
| `model` | no | string | preset-derived | Override OpenRouter model id |
| `consistency-threshold` | no | float | 0.85 | Similarity score threshold for accepting variants |
| `output-dir` | no | path | `output/` | |

If `description` or `type` missing, `AskUserQuestion` blocks with a friendly question (e.g. "is this a stylized cartoon, photorealistic, or artistic mascot?").

## Output

```
output/{mascot-name}-{timestamp}/
├── master.png                    # canonical character: front, neutral, idle
├── character-sheet.png           # multi-view grid (all requested views)
├── style-guide.md                # locked style for future expansion
├── poses/
│   ├── idle.png
│   ├── waving.png
│   ├── thinking.png
│   └── ...
├── expressions/
│   ├── happy.png
│   ├── sad.png
│   ├── surprised.png
│   └── ...
├── views/
│   ├── front.png
│   ├── side.png
│   ├── 3-quarter.png
│   └── back.png
├── outfits/                      # only if requested
│   ├── casual.png
│   ├── formal.png
│   └── sporty.png
├── pose-expression-matrix/       # only if both poses and expressions requested
│   ├── waving-happy.png
│   ├── waving-surprised.png
│   └── ... (cartesian product, optional)
├── metadata.json
└── logs/
    ├── consistency.log
    └── openrouter.log
```

## The type/preset taxonomy

Two-level. `type` picks the broad family; `preset` picks the named style inside it.

```yaml
stylized:
  - flat-vector       # Slack/Notion-style flat illustration
  - cartoon-2d        # Disney/Cartoon Network 2D
  - chibi-kawaii      # anime, big head small body
  - 3d-toon           # Pixar-style 3D, cartoony
  - mascot-corporate  # Duolingo, Mailchimp brand-mascot vibe
  - sticker-style     # iMessage sticker, bold outline
  - low-poly          # geometric 3D

realistic:
  - photoreal-2d      # photorealistic 2D illustration
  - photoreal-3d      # CGI render
  - hyperreal         # extra-detailed, studio lighting
  - documentary       # natural / wildlife realism
  - portrait          # character portrait emphasis

artistic:
  - watercolor        # watercolor painting
  - pencil-sketch     # pencil drawing
  - pixel-art         # 8-bit / 16-bit retro
  - painterly         # oil-painting feel
  - line-art          # contour-only
  - ink-wash          # sumi-e brush-ink
  - chalk             # chalkboard / pastel
```

Each preset declares its primary and fallback OpenRouter models, prompt template, and negative-prompt extras. Full mapping in [docs/presets/mascot-types.md](../presets/mascot-types.md).

## Internal flow — the consistency-critical part

```
1. parse_inputs (block on missing description/type via AskUserQuestion)

2. Generate master:
     - Build prompt from description + type + preset + personality
     - Generate N candidate masters (default 3)
     - User picks (best-of-N) OR auto-pick highest quality_validator score
     - Lock seed and master image

3. Style anchor extraction:
     - vision_analyzer.extract_character_traits(master)
       → palette, fur/skin tones, distinguishing features,
          proportions, accessories, art-style descriptor
     - Build "anchor description" string that gets prepended to every variant prompt

4. Generate each requested view (character sheet):
     - image-to-image with master as reference
     - prompt: "{anchor_description}, viewed from {view}, neutral pose, neutral expression"
     - consistency_checker.score(view, master) ≥ threshold or regenerate (max 3)

5. Generate poses:
     - image-to-image with master as reference
     - prompt: "{anchor_description}, {pose} pose, neutral expression, front view"
     - validate

6. Generate expressions:
     - image-to-image with master as reference
     - prompt: "{anchor_description}, {expression} expression, idle pose, front view"
     - validate

7. Generate outfits (if requested):
     - image-to-image with master
     - prompt: "{anchor_description}, wearing {outfit}, neutral pose, neutral expression"
     - validate

8. Generate pose×expression matrix (if both lists provided AND user opted in):
     - image-to-image with the corresponding pose variant as reference
     - validate against master

9. Compose character-sheet.png:
     - Grid layout: views on top row, master + key poses, expression strip
     - Padding, labels under each tile

10. Write style-guide.md:
     - Captures the anchor description, palette, distinguishing features, used presets
     - Enables future "add a new pose to this mascot" calls

11. Write metadata.json
```

## Image-to-image specifics

Not every OpenRouter model exposes a clean image-to-image endpoint. Strategy:

- **Preferred**: models with native image-to-image (e.g. Flux Redux, models supporting reference images)
- **Fallback**: text-to-image with **detailed character description** generated by `vision_analyzer` from the master, plus seed locking
- **Last resort**: best-of-N generation with `consistency_checker` filtering

The chosen approach per preset is encoded in `shared/presets/mascot_styles.yaml`. Logged at run time so the user knows which strategy was used.

## Consistency thresholds

| Check | Default threshold |
|---|---|
| Palette similarity vs master | ≥ 0.85 |
| Perceptual hash similarity | ≥ 0.75 |
| Face-region similarity (when face is detected) | ≥ 0.80 |
| Subject-segmentation overlap | ≥ 0.70 |

A variant must pass **all** checks. Failing variants auto-regenerate up to 3 times before being surfaced to the user as "best attempt; regenerate manually if needed."

## Cost estimation

`mascot-creator` is the most expensive skill because of the variant fan-out. Pre-run estimate is mandatory.

```
total_calls = N_master_candidates
            + len(views)
            + len(poses)
            + len(expressions)
            + len(outfits)
            + (len(poses) × len(expressions) if matrix=true else 0)
            + retries (estimated 20% overhead)
```

If estimated cost exceeds the user's threshold (default $5.00), prompt for confirmation before starting.

## Edge cases

- **No `type` specified.** `AskUserQuestion`: "Stylized (cartoon), realistic (photo-like), or artistic (hand-drawn)?"
- **Reference image is a real person's photo.** Vision analyzer flags identifiable-person risk. Warning before proceeding.
- **Pose × expression matrix is huge.** e.g. 4 poses × 5 expressions = 20 calls. Confirmation required.
- **Anchor extraction returns ambiguous traits.** Fall back to verbose description and warn that variant consistency may suffer.
- **Style is too realistic to vectorize.** `mascot-pack` consumers should not assume SVG availability.

## Acceptance criteria (phase by phase)

- **Phase 8** (v0.1): Master generation only, type + preset working, no variants. `> mascot-creator "fox" --type stylized --preset flat-vector` produces clean master.
- **Phase 9** (v0.2): Character sheet with multi-view (front/side/3-quarter/back). Faces consistent across views (manual review).
- **Phase 10** (v0.3): Pose and expression variants, image-to-image flow, consistency checker enforcing thresholds.
- **Phase 11** (v0.4): Outfit variants, optional pose×expression matrix, style-guide.md generation.

## Dependencies

- All shared modules, `consistency_checker` and `vision_analyzer` central
- `shared/presets/mascot_styles.yaml`
- `shared/presets/prompt_templates/mascot-creator/`
- Optional downstream: `mascot-pack` for packaging, `png-to-svg` (rarely useful for realistic; sometimes for stylized)

## Future work (not in v1)

- LoRA/IP-Adapter integration when OpenRouter exposes those parameters
- "Add new pose to existing mascot" mode (load master + style-guide, generate just the new variant)
- Animation-ready: rigging-friendly outputs (separate body parts on layers — depends on backend support)
- Brand-pack mode: generate mascot + matching color icon set in one go
