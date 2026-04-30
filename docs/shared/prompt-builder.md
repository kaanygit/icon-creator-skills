# Shared module: `prompt_builder`

Builds final prompts and negative prompts from skill inputs, presets, and reference-derived hints. Centralized so that prompt evolution happens in templates, not scattered in skill code.

## Responsibilities

- Load Jinja-style prompt templates from `shared/presets/prompt_templates/`
- Inject preset-specific style phrasing
- Inject reference-derived hints (palette, character traits, anchor descriptor)
- Assemble negative-prompt extras
- Apply user-supplied overrides without losing preset structure
- Hash prompts for logging without exposing content

## Public API

```python
from shared.prompt_builder import PromptBuilder

pb = PromptBuilder()

# Build for icon-creator
result = pb.build(
    skill="icon-creator",
    type="app-icon",
    preset="flat",
    description="minimalist mountain at dawn",
    colors=["#FF5733", "#1A1A1A"],
    reference_hints=None,                # or StyleHints from vision_analyzer
    user_extras=None,                    # optional free-form addendum
)
# PromptResult(
#   positive="...",
#   negative="...",
#   prompt_hash="abc123",
#   model_recommendation="google/gemini-2.5-flash-image",
#   model_fallbacks=["openai/dall-e-3"]
# )

# Build for mascot-creator with character anchor
result = pb.build(
    skill="mascot-creator",
    type="stylized",
    preset="3d-toon",
    description="wise old owl, professor, glasses",
    personality="wise",
    anchor_traits=character_traits,      # CharacterTraits from vision_analyzer
    variant_kind="pose",
    variant_value="waving",
)
```

## Template structure

Templates live in `shared/presets/prompt_templates/{skill}/{preset}.j2`. Each template has two named blocks: `positive` and `negative`.

Example: `prompt_templates/icon-creator/flat.j2`:

```jinja
{% block positive %}
{{ description }}, flat-style icon, solid colors, no gradients, simple geometry,
centered subject, transparent background, square 1:1 aspect ratio,
even padding, no text, no letters, optimized for use as an app icon,
high contrast, clean edges, vector-style appearance
{%- if colors %}, color palette: {{ colors | join(", ") }}{% endif %}
{%- if reference_hints %}, in the style of: {{ reference_hints.descriptor }}{% endif %}
{%- if user_extras %}, {{ user_extras }}{% endif %}
{% endblock %}

{% block negative %}
photograph, photorealistic, 3d render, gradient, shadow, depth, perspective,
text, words, letters, signature, watermark, multiple subjects, asymmetric,
cluttered, busy, low contrast, blurry, antialiased edges
{% endblock %}
```

Mascot template example: `prompt_templates/mascot-creator/3d-toon-pose-variant.j2`:

```jinja
{% block positive %}
{{ anchor_traits.anchor_text }}, in a {{ variant_value }} pose,
neutral expression, full body visible, front view,
3D toon style, soft shading, rounded forms, character consistent with reference
{% endblock %}

{% block negative %}
different character, different colors, different proportions,
photograph, photorealistic, gritty texture, harsh lighting,
multiple characters, blurry, low quality
{% endblock %}
```

## Resolution order

1. Look up `prompt_templates/{skill}/{preset}-{variant_kind}.j2` (most specific)
2. Fall back to `prompt_templates/{skill}/{preset}.j2`
3. Fall back to `prompt_templates/{skill}/_default.j2` (skill-level default)
4. If none found, raise `PromptBuilderError`

## Preset metadata

Each preset declares its template, model recommendation, and metadata in `shared/presets/{skill}_styles.yaml`:

```yaml
icon-creator:
  flat:
    template: flat.j2
    primary_model: google/gemini-2.5-flash-image
    fallback_models: [openai/dall-e-3]
    style_phrase: "flat-style icon, solid colors, no gradients"
    negative_extras: "gradient, shadow, depth"
    description: "Modern flat illustration"
  glass-morphism:
    template: glass-morphism.j2
    primary_model: black-forest-labs/flux-1.1-pro
    fallback_models: [openai/dall-e-3]
    style_phrase: "glass morphism, frosted blur, translucent"
    negative_extras: "opaque, flat, vector"
    description: "Modern glass / frosted-blur look"
```

## Hashing

Prompts are hashed with a stable algorithm (SHA-256 truncated to 16 chars) for log redaction. The full prompt is written to `prompt-debug.txt` in the run directory; logs reference the hash.

```python
prompt_hash = sha256(positive + "||" + negative).hexdigest()[:16]
```

## User overrides

Users can override the preset choices without forking templates:

- `user_extras`: free-form text appended to positive prompt
- `extra_negatives`: free-form additions to negative prompt
- `model_override`: bypass `primary_model`

Overrides do not modify saved templates.

## Error model

```python
class PromptBuilderError(IconSkillsError):
    code: str   # 'template-not-found', 'preset-unknown', 'render-failed'
```

## Testing

- Snapshot tests: render every (skill, preset) combination with fixed inputs and compare against committed expected output
- Editing a template that changes the snapshot is a deliberate decision, captured in PR review
- Pyramid: unit tests for the loader, snapshot tests for templates, smoke tests for end-to-end prompt generation per skill
