# Mascot type / preset catalog

Two-level taxonomy for `mascot-creator`. Top-level **type** picks the broad family; **preset** picks the named visual style within it.

The canonical machine-readable source is `shared/presets/mascot_styles.yaml`. This document describes intent, fit, model choice, and rough vibe per preset.

## Top-level types

| Type | One-line | When to pick |
|---|---|---|
| `stylized` | Cartoon / illustrated / non-realistic | Brand mascots, app characters, sticker packs, anything where the design language is "drawn / animated, not real" |
| `realistic` | Photorealistic, CGI, lifelike | Wildlife brands, "feels real" product mascots, character portraits aiming for realism |
| `artistic` | Hand-drawn aesthetic, traditional media feel | Editorial illustrations, painterly mascots, indie / boutique brands |

If unsure which top-level type to use, the skill asks: "Stylized (cartoon), realistic (photo-like), or artistic (hand-drawn)?"

## `stylized` presets

### `flat-vector`

Flat illustration, modern vector style. Slack/Notion/Mailchimp-mascot vibe. Solid colors, simple shapes, expressive but minimal.

**Best for**: brand mascots, in-app guides, marketing illustrations
**Style phrase**: "flat vector illustration, solid colors, modern brand mascot style"
**Models**: `google/gemini-2.5-flash-image` → `openai/dall-e-3`

### `cartoon-2d`

Classic 2D cartoon look. Disney/Cartoon-Network-style outlines, fills, animated-show feel.

**Best for**: kid-targeted apps, fun consumer brands
**Style phrase**: "2D cartoon character, animated show style, bold outlines, expressive face"
**Models**: `black-forest-labs/flux-1.1-pro` → `openai/dall-e-3`

### `chibi-kawaii`

Anime cute. Big head, small body, oversized eyes, pastel palette.

**Best for**: anime-fan audiences, kawaii branding
**Style phrase**: "chibi kawaii character, big head, small body, oversized expressive eyes, pastel"
**Models**: `black-forest-labs/flux-1.1-pro` → `openai/dall-e-3`

### `3d-toon`

Pixar-style 3D cartoon. Soft shading, rounded forms, friendly. NOT photoreal — clearly stylized 3D.

**Best for**: app mascots that want depth without realism, modern brand characters
**Style phrase**: "3D toon style, Pixar-like, soft shading, rounded forms, friendly"
**Models**: `black-forest-labs/flux-1.1-pro` → `openai/dall-e-3`

### `mascot-corporate`

Brand-mascot vibe specifically. Duolingo, Mailchimp Freddie, Slack-bot. Designed to be reproducible at small sizes, recognizable silhouette.

**Best for**: SaaS mascots, brand identities
**Style phrase**: "corporate brand mascot, recognizable silhouette, friendly, scalable"
**Models**: `google/gemini-2.5-flash-image` → `openai/dall-e-3`

### `sticker-style`

iMessage-style sticker. Bold outline (white edge), saturated fills, single character on transparent bg.

**Best for**: sticker packs (especially with `mascot-pack` downstream)
**Style phrase**: "sticker style, bold white outline, saturated colors, expressive"
**Models**: `google/gemini-2.5-flash-image` → `openai/dall-e-3`

### `low-poly`

Geometric 3D, faceted polygon look. Indie-game / minimalist 3D vibe.

**Best for**: game studios, tech-startup mascots wanting minimal-3D
**Style phrase**: "low-poly geometric character, faceted, flat-shaded polygons"
**Models**: `black-forest-labs/flux-1.1-pro` → `openai/dall-e-3`

## `realistic` presets

### `photoreal-2d`

Photorealistic-looking 2D illustration. Detailed shading and texture, but flat — not 3D rendered.

**Best for**: editorial-style mascots, premium brands
**Style phrase**: "photorealistic 2D illustration, detailed rendering, painterly realism"
**Models**: `black-forest-labs/flux-1.1-pro` → `stability-ai/stable-diffusion-3.5`

### `photoreal-3d`

CGI-rendered photorealistic character. Studio lighting feel, computer-generated but indistinguishable from photo of a 3D model.

**Best for**: premium app mascots wanting "wow factor," gaming brands
**Style phrase**: "photorealistic 3D CGI character, studio lighting, sharp focus"
**Models**: `black-forest-labs/flux-1.1-pro` → `stability-ai/stable-diffusion-3.5`

### `hyperreal`

Pushed beyond photoreal: extra detail, dramatic lighting, almost-painted feel that reads as "more real than real."

**Best for**: editorial covers, hero illustrations
**Style phrase**: "hyperrealistic, extreme detail, dramatic studio lighting, ultra sharp"
**Models**: `black-forest-labs/flux-1.1-pro` → `stability-ai/stable-diffusion-3.5`

### `documentary`

Natural / wildlife-photo realism. As if shot in the wild. For animal mascots wanting authenticity.

**Best for**: nature brands, wildlife-related apps, conservation orgs
**Style phrase**: "documentary wildlife photograph, natural lighting, authentic environment"
**Models**: `black-forest-labs/flux-1.1-pro` → `stability-ai/stable-diffusion-3.5`

### `portrait`

Character portrait emphasis. Realistic but framed as a portrait — bust, focused on face.

**Best for**: human-character mascots, personality-driven brand reps
**Style phrase**: "realistic character portrait, bust framing, focused face, soft studio lighting"
**Models**: `black-forest-labs/flux-1.1-pro` → `openai/dall-e-3`

## `artistic` presets

### `watercolor`

Watercolor painting. Visible washes, paper texture, organic edges.

**Best for**: editorial brands, indie aesthetic, lifestyle products
**Style phrase**: "watercolor painting, visible washes, paper texture, organic edges"
**Models**: `black-forest-labs/flux-1.1-pro` → `openai/dall-e-3`

### `pencil-sketch`

Pencil drawing. Visible graphite hatching and shading. Often monochrome.

**Best for**: editorial illustrations, sketch-aesthetic brands
**Style phrase**: "pencil sketch, graphite hatching, monochrome, hand-drawn"
**Models**: `black-forest-labs/flux-1.1-pro` → `openai/dall-e-3`

### `pixel-art`

8-bit / 16-bit retro game style. Limited palette, blocky.

**Best for**: indie games, retro-themed brands, dev tools
**Style phrase**: "pixel art, 16-bit retro game style, limited palette, blocky"
**Models**: `black-forest-labs/flux-1.1-pro` → `openai/dall-e-3`

### `painterly`

Oil-painting / acrylic feel. Visible brushstrokes, texture, traditional-media depth.

**Best for**: artisanal brands, premium consumer products
**Style phrase**: "painterly oil-painting style, visible brushstrokes, rich texture"
**Models**: `black-forest-labs/flux-1.1-pro` → `openai/dall-e-3`

### `line-art`

Single-color contour drawing. Pure outline, no fill.

**Best for**: minimal editorial illustration, coloring-book aesthetic
**Style phrase**: "line art, contour drawing, single color, no fill, minimal"
**Models**: `google/gemini-2.5-flash-image` → `openai/dall-e-3`

### `ink-wash`

Sumi-e brush-ink painting. East Asian traditional aesthetic. Bold gestural strokes, ink wash backgrounds.

**Best for**: Asian-aesthetic brands, meditative / wellness apps
**Style phrase**: "sumi-e ink wash painting, bold brush strokes, monochrome ink, traditional"
**Models**: `black-forest-labs/flux-1.1-pro` → `openai/dall-e-3`

### `chalk`

Chalkboard / pastel feel. Soft, slightly smudgy edges, paper-or-chalkboard ground.

**Best for**: education-themed brands, kid-targeted products with handcrafted feel
**Style phrase**: "chalk drawing on chalkboard, soft smudgy edges, hand-drawn"
**Models**: `black-forest-labs/flux-1.1-pro` → `openai/dall-e-3`

## Default preset per type

When the user picks a `type` but not a `preset`:

| Type | Default preset |
|---|---|
| `stylized` | `flat-vector` |
| `realistic` | `photoreal-3d` |
| `artistic` | `watercolor` |

These are documented in the SKILL.md so the user knows what they get without an explicit preset.

## Adding a new preset

1. Choose top-level type (`stylized`, `realistic`, `artistic`) — if it doesn't fit any, propose a new type via discussion first
2. Add an entry under the correct type in `shared/presets/mascot_styles.yaml`
3. Drop Jinja templates in `shared/presets/prompt_templates/mascot-creator/{preset-name}/` (one per variant kind: master, view, pose, expression, outfit)
4. Add a catalog section here
5. Add snapshot tests
