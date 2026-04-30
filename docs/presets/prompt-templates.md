# Prompt templates

How prompts are constructed, where they live, how to author and test them. The actual templates are versioned files under `shared/presets/prompt_templates/`. This document describes the structure and the conventions.

## Layout

```
shared/presets/prompt_templates/
├── icon-creator/
│   ├── _default.j2
│   ├── flat.j2
│   ├── gradient.j2
│   ├── glass-morphism.j2
│   ├── outline.j2
│   ├── 3d-isometric.j2
│   ├── skeuomorphic.j2
│   ├── neumorphic.j2
│   ├── material.j2
│   └── ios-style.j2
├── icon-set-creator/
│   ├── _default.j2
│   └── (preset-specific overrides as needed)
├── mascot-creator/
│   ├── _default.j2
│   ├── stylized/
│   │   ├── flat-vector/
│   │   │   ├── master.j2
│   │   │   ├── view-variant.j2
│   │   │   ├── pose-variant.j2
│   │   │   ├── expression-variant.j2
│   │   │   └── outfit-variant.j2
│   │   ├── cartoon-2d/
│   │   ├── chibi-kawaii/
│   │   ├── 3d-toon/
│   │   ├── mascot-corporate/
│   │   ├── sticker-style/
│   │   └── low-poly/
│   ├── realistic/
│   │   ├── photoreal-2d/
│   │   ├── photoreal-3d/
│   │   ├── hyperreal/
│   │   ├── documentary/
│   │   └── portrait/
│   └── artistic/
│       ├── watercolor/
│       ├── pencil-sketch/
│       ├── pixel-art/
│       ├── painterly/
│       ├── line-art/
│       ├── ink-wash/
│       └── chalk/
```

## File contract

Each `.j2` file uses Jinja2 with two named blocks: `positive` and `negative`.

```jinja
{% block positive %}
... positive prompt content ...
{% endblock %}

{% block negative %}
... negative prompt content ...
{% endblock %}
```

`prompt_builder` renders both blocks with the per-call context.

## Available context variables

### Common (all skills)

| Variable | Type | Description |
|---|---|---|
| `description` | string | The user's description |
| `colors` | list[hex] \| None | User-supplied colors |
| `reference_hints` | StyleHints \| None | From `vision_analyzer` |
| `user_extras` | string \| None | Free-form addendum |

### `icon-creator` specific

| Variable | Type | Description |
|---|---|---|
| `type` | enum | `app-icon` \| `ui-icon` \| `favicon` \| `logo-mark` |

### `icon-set-creator` specific

| Variable | Type | Description |
|---|---|---|
| `subject` | string | The current subject in the set |
| `anchor_hints` | StyleHints | Extracted from set anchor |
| `palette` | list[hex] | Locked palette for the set |
| `stroke_width` | enum | `thin` \| `regular` \| `bold` |
| `corner_radius` | enum | `sharp` \| `rounded` \| `pill` |

### `mascot-creator` specific

| Variable | Type | Description |
|---|---|---|
| `type` | enum | `stylized` \| `realistic` \| `artistic` |
| `personality` | string | "wise", "friendly", etc. |
| `anchor_traits` | CharacterTraits | For variant generation |
| `variant_kind` | enum | `master` \| `view` \| `pose` \| `expression` \| `outfit` |
| `variant_value` | string | "front", "waving", "happy", "casual", etc. |

## Template authoring conventions

### Positive block

- Lead with the user's description
- Add the preset's style phrasing
- Add structural constraints (centered, transparent, square, etc.) for icons
- Add character-consistency clauses for mascot variants
- Conditionally append palette / hints / user-extras at the end
- One sentence per line where possible (easier to diff)

### Negative block

- Common negatives across many presets are factored into the skill-level `_default.j2` and inherited
- Preset-specific negatives go in the preset file
- Examples of common negatives: `text, words, letters, signature, watermark, blurry, low quality`
- Examples of preset-negatives: for `flat`, add `gradient, shadow, depth`; for `realistic`, add `cartoon, flat, 2d, anime`

### Inheritance

Use Jinja `{% extends %}` for shared structure:

```jinja
{# prompt_templates/mascot-creator/_default.j2 #}
{% block positive_subject %}{{ description }}{% endblock %}
{% block positive_style %}{# overridden by preset #}{% endblock %}
{% block positive_constraints %}centered, single subject{% endblock %}
{% block positive_extras %}{% if user_extras %}, {{ user_extras }}{% endif %}{% endblock %}

{% block positive %}
{{ self.positive_subject() }}, {{ self.positive_style() }},
{{ self.positive_constraints() }}{{ self.positive_extras() }}
{% endblock %}
```

```jinja
{# prompt_templates/mascot-creator/stylized/3d-toon/master.j2 #}
{% extends "_default.j2" %}
{% block positive_style %}3D toon style, Pixar-like, soft shading, rounded forms, friendly{% endblock %}
```

### Variant templates: anchor injection

For mascot variant prompts (view, pose, expression, outfit), the anchor description from `CharacterTraits.anchor_text` MUST be the first thing in the positive block, before any other context. This is what keeps character consistency.

```jinja
{# prompt_templates/mascot-creator/stylized/3d-toon/pose-variant.j2 #}
{% block positive %}
{{ anchor_traits.anchor_text }}.

In a {{ variant_value }} pose, neutral expression, full body visible, front view.
3D toon style, soft shading, rounded forms, character consistent with reference.
{% endblock %}
```

## Snapshot testing

Every (skill, preset) combination has a snapshot test. Test inputs are fixed; rendered prompt is committed to `tests/fixtures/prompts/{skill}/{preset}.txt`.

When a template changes, the snapshot diff is reviewed in the PR. Intentional changes update the snapshot; accidental changes get caught.

## Tunable knobs (planned, post-v1)

- `style_strength` — multiplier for the preset style phrase (lighter / heavier)
- `description_emphasis` — emphasis tokens (e.g., `(({{ description }}))` for models that respect weight syntax)
- `composition` — explicit framing override (close-up, full-body, three-quarter)

These add complexity; deferred until we have evidence templates need them per-call.

## Bad-prompt anti-patterns to avoid

- **"high quality, masterpiece, 8k"** — buzzword stacking; on modern models this either does nothing or hurts. Prefer specific style phrases.
- **Negative prompts that contradict the positive** — confuses the model. Negatives should describe what to exclude, not be opposites of the positive.
- **Subject hidden in a sea of style words** — the user's description should be the first or second thing in the prompt.
- **Hardcoded colors when user asked for palette** — always make palette injection conditional, never bake colors into a template.
- **Prompts > 400 tokens** — most image models truncate or weight-decay long prompts. Aim for 80-200 tokens.
