# CLAUDE.md

Context file for any Claude Code / AI agent session working in this repo. Read this first.

---

## What this project is

`icon-creator-skills` — an open-source agent-skill toolkit for icon and mascot generation, with multi-platform asset packaging. Built on OpenRouter image models, designed to drop into Claude Code, OpenCode, and any harness that supports the SKILL.md format.

**License:** MIT.
**Language:** Python 3.11+.

## Current status

**Phase 05 implemented. Shared infrastructure, `icon-creator` v0.3, and `app-icon-pack` v1.1 exist.**

This repo now includes shared infrastructure under `shared/`, `icon-creator`, and `app-icon-pack`. `icon-creator` supports presets, reference images, multi-variant output, validator auto-pick, preview grids, and refinement. `app-icon-pack` converts a PNG master into iOS, Android, Web, macOS, watchOS, and Windows assets. Later skill folders are still phase-gated.

Current / target layout:

```
icon-creator-skills/
├── README.md, LICENSE, CLAUDE.md
├── pyproject.toml                    # package + dev tooling
├── docs/                             # design docs (already exist)
├── shared/                           # Phase 00 shared package
├── skills/                           # added per phase
│   ├── icon-creator/                 # phases 1-3
│   ├── icon-set-creator/             # phase 13
│   ├── mascot-creator/               # phases 8-11
│   ├── png-to-svg/                   # phases 6-7
│   ├── app-icon-pack/                # phases 4-5 implemented
│   └── mascot-pack/                  # phase 12
└── tests/
```

## Decisions already made (don't relitigate without reason)

- **6 skills** (icon-creator, icon-set-creator, mascot-creator, png-to-svg, app-icon-pack, mascot-pack). Mascot ≠ icon, set ≠ single, packaging ≠ generation.
- **Monorepo** with shared `shared/` package across all skills.
- **Python**, not Node.js. Pillow + OpenCV + rembg + vtracer ecosystem.
- **OpenRouter-only** image generation in v1. No Replicate / fal.ai / direct provider abstraction.
- **MIT license.**
- **No telemetry, ever.**
- **Phased build with explicit acceptance tests.** Each phase has a manual checkpoint in OpenCode before moving on.
- **Mascot two-level taxonomy:** `type ∈ {stylized, realistic, artistic}` × `preset` (~17 named presets).
- **Output format:** always a flat directory with optional zip. Never zip-only.

Full rationale per decision: `docs/decisions.md`.

## File map (where to find what)

| Question | Doc |
|---|---|
| What does this project do, who is it for? | `docs/vision.md` |
| How is it structured, how do skills compose? | `docs/architecture.md` |
| Why is decision X what it is? | `docs/decisions.md` |
| What can go wrong? | `docs/risks.md` |
| Specs of skill `<X>`? | `docs/skills/<X>.md` |
| How does shared module `<Y>` work? | `docs/shared/<Y>.md` |
| Style preset taxonomy? | `docs/presets/icon-styles.md`, `docs/presets/mascot-types.md` |
| Current OpenRouter model matrix? | `docs/presets/model-matrix.md` |
| How are prompts assembled? | `docs/presets/prompt-templates.md` |
| Asset sizes for platform `<P>`? | `docs/platforms/<P>.md` |
| Cross-cutting feature like cost tracking, retries, brand kit? | `docs/quality/*.md` |
| What does phase N do, how is it tested? | `docs/phases/phase-NN-*.md` |
| Phase index / what's next? | `docs/phases/README.md` |

## How to work in this repo

### If a user asks "implement phase N"

1. Read `docs/phases/phase-NN-*.md` end-to-end. It tells you the goal, deliverables, implementation steps, and acceptance criteria.
2. Read the spec docs it references (skills, shared modules) so you understand the design.
3. Implement. Default to writing tests alongside code.
4. Mark acceptance criteria (automated + manual + documentation) as you go.
5. Phase is **not done** until all acceptance criteria pass and the user has manually validated in OpenCode (the "Test in OpenCode" section of every phase doc).

### If a user asks "add a new preset"

1. Decide the type (icon style, mascot style)
2. Add YAML entry to `shared/presets/<icon|mascot>_styles.yaml` (will exist after phase 0)
3. Add Jinja template to `shared/presets/prompt_templates/<skill>/<preset>.j2`
4. Add a section to `docs/presets/<icon-styles|mascot-types>.md` documenting it
5. Add a snapshot test fixture
6. Optional: visual sanity check by running the skill with the new preset

No Python code change needed for new presets.

### If a user asks "why is the model for preset X gemini-flash-image?"

Check `shared/presets/<skill>_styles.yaml` — model assignments live there. Rationale lives in the skill's spec doc (e.g. `docs/skills/icon-creator.md`).

### If a user reports a broken icon / failed validation

1. Check `output/<run-id>/logs/` for structured logs
2. Check `metadata.json` for the prompt, model, seed used
3. The `prompt-debug.txt` has the full positive + negative prompt
4. Likely causes:
   - Validator threshold too strict (see `docs/quality/retry-validation.md`)
   - Model produced text artifacts (see `quality_validator.no_text_artifacts`)
   - Adaptive icon clipping (see `docs/platforms/android.md`)

### If a user asks "what's left before v1.0"

Look at `docs/phases/README.md`. The phase that's not yet "done" is the next one to work on.

## Conventions

- **Tests:** unit tests in `<package>/tests/`, integration tests gated behind `RUN_LIVE_TESTS=1`.
- **Logging:** structured JSON-line logs into `output/<run-id>/logs/`, no global stdout spam.
- **Errors:** subclass `IconSkillsError`, see `shared/errors.py` (after phase 0).
- **Configuration:** YAML in `shared/presets/`, never hardcoded in Python.
- **Prompts:** Jinja templates in `shared/presets/prompt_templates/`, never hardcoded.
- **API key:** env var only (`OPENROUTER_API_KEY`). Never logged. Never written to any output file.

## Phase plan (TL;DR)

One preflight phase plus 18 implementation phases. Built in dependency order. Most-valuable combination (`icon-creator` + `app-icon-pack`) ships by phase 4. Mascot (the hardest skill) split across phases 8-11.

| Phase | What lands |
|---|---|
| 00-preflight | OpenRouter API/model reality check, no code |
| 00 | shared/ skeleton, OpenRouter client, image utils |
| 01 | icon-creator v0.1 — single-shot, no presets |
| 02 | icon-creator v0.2 — 9 style presets + reference image |
| 03 | icon-creator v0.3 — multi-shot, validator, iteration |
| 04 | app-icon-pack v1.0 — iOS + Android + Web |
| 05 | app-icon-pack v1.1 — macOS + watchOS + Windows |
| 06 | png-to-svg v0.1 — vtracer integration |
| 07 | png-to-svg v0.2 — potrace + imagetracer + auto-select |
| 08 | mascot-creator v0.1 — master generation, 17 presets |
| 09 | mascot-creator v0.2 — multi-view character sheet |
| 10 | mascot-creator v0.3 — pose + expression variants |
| 11 | mascot-creator v0.4 — outfits, style-guide.md |
| 12 | mascot-pack v1.0 — social/sticker/print/web deliverables |
| 13 | icon-set-creator v1.0 — coherent icon families |
| 14 | cross-skill — brand kit, style memory, replay |
| 15 | polish — error UX, retry tuning, doctor command |
| 16 | docs — getting-started, recipes, troubleshooting |
| 17 | release — v1.0.0 to PyPI + GitHub |

After phase 4, the toolkit is **demo-shippable** for icon use cases. After phase 11, mascot users can use it. After phase 13, set generation lands. Phase 14+ is hardening and release.

## Common pitfalls when working in this repo

- **Don't edit a SKILL.md without checking the phase doc.** Skill specs evolve per phase; the SKILL.md for `icon-creator` after phase 1 is different from after phase 3. Read the active phase doc first.
- **Don't add features cross-phase.** If you're in phase 4 and notice phase 14 features missing, that's expected — do not preempt.
- **Don't bake API keys into anywhere.** Even in tests, mock the client; never embed a real key.
- **Don't skip the manual-acceptance step.** Generation quality is human-judged; "tests pass" doesn't mean a phase is done.
- **Don't break the "no skill imports another skill" rule.** Cross-skill composition is via the agent layer or shared modules, never via Python imports across skill boundaries.
- **Don't merge a phase without committing the acceptance record** (`docs/phases/phase-NN-acceptance.md`).

## When in doubt

Read `docs/vision.md` first. Then the relevant skill's spec. Then the active phase doc. Then ask the user.
