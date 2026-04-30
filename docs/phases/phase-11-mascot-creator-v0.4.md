# Phase 11: `mascot-creator` v0.4 — outfits + style-guide

Add outfit variants. Add optional pose × expression matrix. Generate `style-guide.md` output for future re-use.

## Goal

`--outfits casual,formal,sporty` produces three outfit variants. `--matrix` enables pose × expression cartesian product. Every successful run writes a `style-guide.md` documenting the locked character.

## Deliverables

### New prompt templates

Per preset:
- `outfit-variant.j2`

17 new templates.

### Skill updates

- `generate.py` accepts `--outfits` and `--matrix`
- Outfit loop similar to pose/expression
- Matrix mode: for each (pose, expression) pair, run a variant
- Style-guide.md generation at end of every run

### Style-guide template

`shared/templates/style-guide.md.j2` (Jinja for the guide itself):

```jinja
# Style guide: {{ mascot_name }}

Generated {{ timestamp }} by mascot-creator v{{ version }}.

## Character

{{ anchor_traits.anchor_text }}

## Visual identity

- Type: {{ type }}
- Preset: {{ preset }}
- Personality: {{ personality | default('—') }}

## Palette

{% for color in anchor_traits.colors %}
- {{ color }}
{% endfor %}

## Distinguishing features

{% for feature in anchor_traits.distinguishing_features %}
- {{ feature }}
{% endfor %}

## Variants produced in this run

{% if views %}
### Views
{% for v in views %}- {{ v }}{% endfor %}
{% endif %}

{% if poses %}
### Poses
{% for p in poses %}- {{ p }}{% endfor %}
{% endif %}

{% if expressions %}
### Expressions
{% for e in expressions %}- {{ e }}{% endfor %}
{% endif %}

{% if outfits %}
### Outfits
{% for o in outfits %}- {{ o }}{% endfor %}
{% endif %}

## To extend this mascot later

```
> /mascot-creator --reference-image {{ master_path }} \
                  --type {{ type }} --preset {{ preset }} \
                  --poses "<new-poses>" \
                  ...
```

This loads the locked anchor and produces additional variants in the same style.
```

## Implementation steps

1. Author 17 outfit-variant templates
2. Snapshot tests for all 17
3. Update `generate.py`:
   - Outfit loop (pattern from pose/expression)
   - Matrix mode: nested loop, with image-to-image using the corresponding pose variant as reference (so the matrix entry inherits both pose and identity)
   - Style-guide.md generation at end
4. Update README.md auto-generation per run to include "see style-guide.md for the locked character description"

## Acceptance criteria

### Automated
- 17 outfit snapshot tests pass
- End-to-end with all variant types: master + views + poses + expressions + outfits
- `--matrix` produces N × M output files
- `style-guide.md` generated and contains all expected sections

### Manual / by-eye
- 3+ runs with full feature set
- Outfit variants visually clear (casual ≠ formal ≠ sporty) AND character preserved
- Matrix entries combine pose + expression credibly (e.g. "waving + happy" shows a smiling, waving character)
- Style-guide.md is human-readable and accurate to the run

### Documentation
- SKILL.md complete with `--outfits`, `--matrix`
- README explains style-guide.md as a "save this for later" artifact

## Test in OpenCode

```
> /mascot-creator "fox, friendly explorer" --type stylized --preset cartoon-2d \
                  --views front,side --poses idle,running --expressions happy,curious \
                  --outfits adventurer,scientist --matrix
```

Confirm:
- Full output structure
- Matrix folder has 4 entries (2 poses × 2 expressions)
- style-guide.md present
- Run summary lists all variants and total cost

## Out of scope for phase 11

- "Add to existing mascot" mode that loads a previous style-guide.md and produces additional variants without regenerating master (post-v1)
- LoRA/IP-Adapter integration when OpenRouter exposes those (post-v1)
- Animation-ready layered output (post-v1)

## Risks

- **Matrix mode multiplies cost.** Pre-run cost estimate is mandatory; default confirmation threshold $1.00 will get hit on most matrix runs.
- **Outfit variants can lose character identity** if the outfit description overrides the anchor. Mitigate by structure: outfit description is appended to anchor_text, never replaces.
- **Style-guide.md accuracy.** Anchor traits come from vision LLM; if extraction is wrong, the guide is wrong. We rely on `extract_character_traits` working well from phase 09.

## Dependencies on prior work

- Phase 10 (poses, expressions, image-to-image flow)
- Phase 09 (vision_analyzer character traits)
