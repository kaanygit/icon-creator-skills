# Decisions log

Architectural decisions, in order made. New decisions append; old decisions are superseded but not deleted (they document past reasoning).

Format: ADR-lite. Each entry has Context, Decision, Consequences.

---

## ADR-001 · Six skills, not one mega-skill

**Context.** The pipeline (generate → vectorize → package) could be a single skill. We considered 1, 2, 3, 4, 6 skill splits.

**Decision.** Six skills: `icon-creator`, `icon-set-creator`, `mascot-creator`, `png-to-svg`, `app-icon-pack`, `mascot-pack`.

**Why.**
- Single responsibility per skill makes maintenance and discovery cleaner
- Each skill is independently useful: someone with an existing master image just needs `app-icon-pack`; someone with a PNG just needs `png-to-svg`
- Mascot ≠ icon: prompts, output structure, consistency requirements all differ
- Icon-set creation is technically distinct from single-icon (consistency anchor, batch validation)

**Consequences.** More files, more docs, more SKILL.md to maintain. Mitigated by aggressive sharing through `shared/`. Six SKILL.md files is far less duplication than two skills with branching logic inside.

---

## ADR-002 · Mascot type/preset taxonomy

**Context.** Mascots vary wildly: cartoon vs photorealistic vs hand-drawn. Each demands a different prompt template, model, and negative prompt. Single-parameter doesn't capture it.

**Decision.** Two-level taxonomy: `type ∈ {stylized, realistic, artistic}` × `preset` (~17 named presets distributed across types).

**Why.**
- Top-level `type` is the binary the user already thinks in ("yapay mı gerçekçi mi")
- Preset is the fine-grained creative direction
- Both map to concrete model selection and prompt-template choices

**Consequences.** Preset list will grow over time. YAML format makes additions PR-able without code changes.

See [docs/presets/mascot-types.md](presets/mascot-types.md) for the full taxonomy.

---

## ADR-003 · Monorepo, not per-skill repos

**Context.** Six skills could be six independent repos.

**Decision.** Single repo (`icon-creator-skills`) containing all six skills under `skills/` and shared code under `shared/`.

**Why.**
- Shared module changes can be tested across all skills in one PR
- Coordinated versioning ("v1.0 of the toolkit")
- Easier onboarding: one repo, one README, one issue tracker
- Image-processing dependencies (Pillow, OpenCV, vtracer) are shared, single requirements file

**Consequences.** A consumer who only wants `png-to-svg` clones the whole thing. Acceptable cost. If usage data ever shows one skill dominating, we revisit.

---

## ADR-004 · Python, not Node.js

**Context.** Either ecosystem can talk to OpenRouter and process images.

**Decision.** Python.

**Why.**
- Pillow + OpenCV + scikit-image + rembg + cairosvg + vtracer-py covers the entire image pipeline natively, with mature C bindings
- The vectorization stack (potrace, vtracer, imagetracer) is best-in-class in Python
- Sharp (Node) is fast but the surrounding ecosystem is thinner for our needs

**Consequences.** The Python install bar is non-zero on macOS/Windows. We ship a `pyproject.toml` and document `pipx install` and `uv tool install` paths.

---

## ADR-005 · OpenRouter only in v1

**Context.** Replicate, fal.ai, direct provider APIs (OpenAI, Stability, Google) all generate images. We could abstract.

**Decision.** OpenRouter as the only backend in v1. No abstraction layer beyond `openrouter_client`.

**Why.**
- One key, one billing surface, model selection is a string
- Premature abstraction adds maintenance with zero immediate benefit
- The seam is still clear: any swap is a single module rewrite, no skill code touches the API

**Consequences.** Users without an OpenRouter account need to create one. The barrier is one signup. v2 may introduce a `Backend` protocol if users genuinely want self-hosted Stable Diffusion or direct provider keys.

---

## ADR-006 · MIT license

**Context.** MIT vs Apache 2.0 vs GPL.

**Decision.** MIT.

**Why.**
- Maximum reusability across commercial and non-commercial projects
- Skill code being embedded in users' own products is the explicit goal
- Apache 2.0's patent grant adds friction for individual contributors with no offsetting benefit at this scale
- GPL would block the primary use case (using generated assets in proprietary apps)

**Consequences.** Forks and proprietary derivatives are allowed. We accept this in exchange for the broadest possible adoption.

---

## ADR-007 · SKILL.md format follows Claude Code's spec

**Context.** Each agent harness has subtly different skill formats. We could invent a portable format.

**Decision.** Author SKILL.md against Claude Code's spec. Document any per-harness adjustments (OpenCode, etc.) as overlays.

**Why.**
- Portability layers always lag behind whichever spec they're tracking
- Claude Code's format is the most widely used and best-documented today
- Most other harnesses (OpenCode included) read SKILL.md compatibly

**Consequences.** If Claude Code's format diverges from the OpenCode reading, we add per-harness adapters at that point. Until then, no portability tax.

---

## ADR-008 · Phase-by-phase build with explicit acceptance tests

**Context.** Big-bang build vs incremental.

**Decision.** Eighteen phases (phase-00 through phase-17), each with a concrete deliverable and concrete acceptance test. No phase merges to main without its acceptance test passing.

**Why.**
- The user explicitly wants to validate each step in their own agent harness as we go
- Generation-quality work needs human sign-off; "looks good" is too vague for a test
- Phased delivery means even an early-cut version of the toolkit is useful

**Consequences.** Slower than big-bang. The benefit is that each phase ships something testable, and bad assumptions surface phase 3 instead of phase 17.

See [docs/phases/](phases/) for the full plan.

---

## ADR-009 · Output is always a flat directory + optional zip

**Context.** Should output always be zipped, or always be a directory, or configurable?

**Decision.** Always write a flat `output/{run-slug}/` directory. Zipping is a separate, optional step.

**Why.**
- Directories are inspectable mid-run (debug, partial recovery)
- Zipping is cheap to add but expensive to undo when you need to peek
- Skills that consume previous outputs (`app-icon-pack` reading from `icon-creator`'s output) work naturally on directories

**Consequences.** The user has to opt into the zip if they want one. Default for `app-icon-pack` and `mascot-pack` is to produce both — the zip is what gets shared, the directory is what gets debugged.

---

## ADR-010 · No telemetry, ever

**Context.** Knowing which presets users pick, which models are popular, would inform priorities.

**Decision.** No telemetry of any kind. No phone-home. No anonymous metrics.

**Why.**
- Open-source trust starts with "this thing only does what I told it to do"
- The user's prompts and reference images are sometimes sensitive (unreleased branding, NDA work)
- Information about model choices and presets surfaces through GitHub issues and discussions, which is enough signal

**Consequences.** We learn slower. Acceptable.
