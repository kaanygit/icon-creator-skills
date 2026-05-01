# Marketplace Prep

Use this page when submitting or describing the package in a skills directory such as
skills.sh.

## Package

- Repository: `kaanygit/icon-creator-skills`
- Install all skills:

```bash
npx skills add kaanygit/icon-creator-skills --skill '*' --agent opencode --global --yes
```

- List skills:

```bash
npx skills add kaanygit/icon-creator-skills --list
```

## Short Description

Generate icons, mascot characters, icon sets, SVG conversions, and platform asset packs
from agent workflows.

## Long Description

`icon-creator-skills` is an agent-skill toolkit for visual asset production. It includes
skills for single icon generation, mascot generation, coherent icon-set generation,
platform app-icon packaging, mascot deliverable packaging, and local PNG-to-SVG
vectorization. Generation skills support OpenRouter by default, with optional OpenAI and
Google Gemini providers.

## Categories

- Design
- Image generation
- Brand assets
- Developer tools
- App store assets

## Included Skills

- `icon-creator`
- `icon-set-creator`
- `mascot-creator`
- `app-icon-pack`
- `mascot-pack`
- `png-to-svg`

## Example Prompts

```text
Use icon-creator to create a gradient app icon for a geometric fox finance app.
```

```text
Use mascot-creator to create a stylized cartoon-2d mascot: friendly fox explorer.
Keep it cheap with --variants 1 --best-of-n 1.
```

```text
Use app-icon-pack on output/my-icon/master.png for iOS, Android, and Web.
```

## Visual Examples

Use the committed images in [gallery.md](gallery.md):

- `docs/assets/examples/icon-geometric-fox-master.png`
- `docs/assets/examples/icon-geometric-fox-preview.png`
- `docs/assets/examples/mascot-fox-master.png`
- `docs/assets/examples/png-to-svg-comparison.png`

## Verification

```bash
npx skills add . --list
python -m pytest
python -m ruff check .
```
