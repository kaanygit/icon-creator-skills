# Risks and mitigations

Tracked risks, their severity, and the concrete plan to handle each. Updated as we learn.

Severity scale: **HIGH** (could kill the project's usefulness), **MEDIUM** (degrades quality on common inputs), **LOW** (rare or cosmetic).

---

## R-001 · Mascot character consistency across pose/expression variants — **HIGH**

**The problem.** Generating "the same character" in different poses is the hardest open problem in this space. Naive prompt-only approaches drift: hair color shifts, proportions change, the face becomes a different face.

**Mitigations.**
- Use **image-to-image** with the master as the reference, not text-only regeneration
- Pin **seed** within a small range
- Use models with explicit character-preservation features when available on OpenRouter (Flux Redux, character LoRAs, IP-Adapter style references where exposed)
- Run `consistency_checker` on every variant; auto-regenerate variants below a similarity threshold (default 0.85 perceptual hash similarity vs master)
- Plan B: "best of N" — generate N candidates per variant, surface them to the user, let them pick
- Document this risk to the user. The README must say honestly: "mascot variant consistency is the hardest part; expect occasional misses, you can regenerate cheaply"

**Owner.** Phase 10.

---

## R-002 · OpenRouter image-gen model availability changes — **MEDIUM**

**The problem.** The set of image-generation models on OpenRouter shifts. A model we depend on for `realistic` could be deprecated; pricing could spike; a new better model could appear.

**Mitigations.**
- Model selection lives in `shared/presets/models.yaml`, not in code
- Each preset declares a **primary** and **fallback** model
- `openrouter_client` checks model availability before the call; falls back automatically with a logged warning
- Quarterly review of the preset → model mapping; pin in CHANGELOG when changes happen

**Owner.** Phase 0 (initial mapping), ongoing maintenance.

---

## R-003 · PNG-to-SVG produces poor results on photographic inputs — **MEDIUM**

**The problem.** Vectorization works well on flat / geometric / icon-like inputs. Photographs and complex shaded mascots vectorize into a blob of paths that's larger than the source PNG and looks worse.

**Mitigations.**
- `png-to-svg` runs a **suitability check** before tracing: estimate color count, edge density, gradient prevalence
- If unsuitable, the skill returns a warning and either refuses or proceeds only with explicit user override
- Default `algorithm: auto` picks `potrace` for flat 2-color, `vtracer` for moderate-color, refuses for high-detail photo inputs
- For mascots specifically, the default is **don't vectorize** unless the user opts in

**Owner.** Phase 6.

---

## R-004 · Android adaptive icon safe-zone errors cause Play Store rejection — **MEDIUM**

**The problem.** Android adaptive icons require the foreground to fit inside a 72dp safe zone within the 108dp canvas. Get this wrong, parts of the icon get cropped at runtime; in extreme cases the Play Store flags it.

**Mitigations.**
- Hardcode the math (108dp canvas, 72dp safe area, transform matrix) in `app-icon-pack`
- Render preview tile showing safe-zone overlay as part of run output
- Auto-detect when source content extends beyond safe area, scale down with padding rather than risk clipping
- Acceptance test in phase 4: render adaptive icon in Android Studio device preview, confirm visible content fits

**Owner.** Phase 4.

---

## R-005 · Apple platform asset matrix shifts annually — **MEDIUM**

**The problem.** Apple adds new device classes (Vision Pro, etc.) and occasionally changes required sizes. Hardcoded tables go stale.

**Mitigations.**
- All size tables in `shared/presets/platforms/{platform}.yaml`, no Python changes to update
- A `pinned_xcode_version` field per table, so users know what's targeted
- Release cadence: review on every major iOS / macOS release
- `app-icon-pack` validates against the Xcode-expected `Contents.json` schema if available; warns on schema mismatch

**Owner.** Ongoing maintenance.

---

## R-006 · OpenRouter API key leaks via accidental commits or logs — **HIGH**

**The problem.** The user's API key is sensitive. A skill that logs it, writes it to metadata, or accepts it as a CLI arg invites accidents.

**Mitigations.**
- Key only ever read from `OPENROUTER_API_KEY` env var, never from CLI args, never written to any file the skill creates
- `metadata.json` explicitly excludes any header-bearing data; only the model name is captured
- `.gitignore` ships with `.env`, `*.env`, `.env.local`
- Phase 15 polish step adds an explicit log scrubber that redacts any string matching the key pattern even if it slips into a debug log

**Owner.** Phase 0 (initial design), phase 15 (audit).

---

## R-007 · Cost surprises burn user trust — **MEDIUM**

**The problem.** Image generation is not free. A user who runs a 12-icon set with 3 variants each is silently doing 36 generations. Without visibility, the bill shocks them.

**Mitigations.**
- `openrouter_client` tracks per-call cost using OpenRouter's per-model pricing
- Every run prints a final cost summary
- `~/.icon-skills/cost-log.json` accumulates lifetime cost per model (opt-out)
- Skills that fan out (icon-set, mascot variants) print an **estimated cost before the run** and require confirmation past a configurable threshold (default $1.00)

**Owner.** Phase 1 (basic), phase 14 (full).

---

## R-008 · User uploads a copyrighted reference image — **LOW (legal), HIGH (ethical/PR)**

**The problem.** A user drops a competitor's logo as reference and asks for "something like this." The skill happily produces a near-clone.

**Mitigations.**
- `vision_analyzer` runs a logo-detection / brand-similarity heuristic on reference images (lightweight, not foolproof)
- Warning printed when the reference looks like a known logo or contains identifiable trademark cues
- README and SKILL.md text clearly state: user is responsible for reference-image rights
- We do not block the generation; we surface the risk

**Owner.** Phase 2.

---

## R-009 · Background removal degrades icons with intentional transparent regions — **LOW**

**The problem.** `rembg` and similar models sometimes erase intentional negative space inside icons (e.g., a "hole" in a donut icon).

**Mitigations.**
- Background removal is a **post-processing fallback**, only invoked when the model didn't produce a transparent background
- Detection: check alpha channel before invoking removal
- Configurable per-call: `--no-bg-removal` flag for cases where the user wants to handle it manually

**Owner.** Phase 3.

---

## R-010 · Vectorizer dependency hell on user machines — **MEDIUM**

**The problem.** `vtracer-py`, `potrace`, ImageMagick, cairosvg — each has native dependencies that fail to install on some machines.

**Mitigations.**
- Each shared module guards its imports; missing deps surface as actionable errors with install commands ("brew install potrace" / "apt install libpotrace-dev")
- `pyproject.toml` pins versions known to install cleanly on macOS, Linux, and Windows
- Each skill runs a **doctor check** at startup, listing what's available
- Pure-Python fallbacks where they exist (e.g., for trivial image ops)

**Owner.** Phase 0, phase 15.

---

## R-011 · Model output drift breaks acceptance tests — **MEDIUM**

**The problem.** Acceptance tests for "did the icon come out right?" can't be exact-pixel comparisons; the model is non-deterministic.

**Mitigations.**
- Acceptance tests are **structural** (file exists, transparent bg, square aspect, file size in expected range), not visual
- Visual sign-off is a manual step at phase boundaries, documented in each phase doc
- Where automatic visual checks are needed, use perceptual similarity to a known-good reference, not exact match

**Owner.** Each phase's acceptance criteria.

---

## R-012 · Skill format diverges between Claude Code and OpenCode — **LOW**

**The problem.** The user wants to test in OpenCode. If OpenCode doesn't read SKILL.md the same way Claude Code does, we ship broken.

**Mitigations.**
- Phase 1 explicitly tests the skill in OpenCode as well as Claude Code
- Differences (if any) get a short overlay file per harness, not a runtime branch
- We track upstream changes in both projects' skill specs

**Owner.** Phase 1, phase 17.
