# Vision

## The problem

Producing a usable icon or mascot for a project today still costs hours, even with image-generation models.

The model itself is the easy part. What kills you is everything around it:

- Knowing the right prompt structure for icons specifically (centered subject, transparent background, no text, even padding, readable at 16×16)
- Knowing the difference between a "stylized cartoon" prompt and a "photorealistic 3D" prompt for mascots
- Cleaning up the output (background removal, auto-crop, padding normalization)
- Resizing to the right matrix of sizes (Apple alone wants 17 sizes across iPhone/iPad/Watch/Mac)
- Generating the boilerplate (`Contents.json`, `manifest.json`, `browserconfig.xml`)
- Producing **consistent** outputs — a navigation icon set where all 12 icons look like they belong together is a different problem from generating one icon
- For mascots: producing the **same character** in different poses and expressions, which is the hardest consistency problem in the whole space

This toolkit exists to compress that whole pipeline into "describe what you want, get production-ready files."

## The user

Solo developer, indie hacker, small studio team. Someone who:

- Ships apps and websites without a designer on staff
- Has tried image generators and gotten "fine but unusable" results
- Doesn't want to learn ImageMagick, doesn't want to fight Xcode's asset catalog format, doesn't want to look up the Android adaptive-icon safe zone for the tenth time
- Already lives in a coding agent (Claude Code / OpenCode / similar)

## The promise

```
> /icon-creator "minimalist mountain icon, dawn light, soft gradient"
  ↳ master.png + 3 variants
  ↳ Should I package this for iOS / Android / Web? [y]
  ↳ output/mountain-app-icons.zip — drop into Xcode and Android Studio, you're done.
```

```
> /mascot-creator "wise old owl, professor, glasses" --type stylized --preset 3d-toon \
                  --poses idle,waving,thinking --expressions happy,surprised
  ↳ master.png + character-sheet.png + 6 pose/expression PNGs
  ↳ output/owl-mascot-pack.zip — social media, stickers, transparent variants included.
```

The user thinks about **the icon they want**, not about the toolchain.

## What this is not

- Not a Figma replacement. If you want pixel-perfect manual control, use Figma.
- Not a foundation-model trainer. We orchestrate existing image-gen models, we don't fine-tune.
- Not a hosted service. Bring your own OpenRouter key. The skill runs on your machine, no telemetry.
- Not "magic." Image generation is still imperfect; the skill exposes regenerate, iterate, and "best-of-N" affordances because that's the honest UX.

## Why open source

- Asset size tables and platform conventions change. A community keeps `docs/platforms/*.md` current.
- Designer prompt templates improve over time. PR-able prompt presets is the right format.
- The user already pays OpenRouter; there's nothing left for us to monetize and no reason to gate the tool.
- Skill format is portable across agents. Open source is what makes that portability worth anything.

## Success looks like

A new user installs the skill, runs one command, gets a usable asset pack on the first try, drops it into their project, and ships. Time from `pip install` to App Store submission–ready icons: **under five minutes**.
