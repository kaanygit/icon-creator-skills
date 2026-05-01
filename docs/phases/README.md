# Phased build plan

The toolkit is built in one preflight phase plus 18 implementation phases. Each phase produces a concrete, testable deliverable. No phase merges to main without its acceptance test passing.

## Why phased

- The user wants to test each step in their own agent harness as we go.
- Generation-quality work needs human sign-off; "looks good" is too vague for a CI test.
- Phased delivery means even an early-cut version is useful (after phase 4, you can ship icons to App Store).

## Phase ordering rationale

Phases are ordered to deliver **the most value as early as possible**:

1. **Phase 00-preflight** verifies OpenRouter's current image API and model availability before code exists
2. **Phase 00** establishes the shared infrastructure that everything depends on
3. **Phases 1-4** deliver the icon-creator + app-icon-pack flow — this is the most-demanded combination, immediately useful
4. **Phase 5** rounds out app-icon-pack with the less-common platforms
5. **Phases 6-7** vectorization (lower demand, easier to delay)
6. **Phases 8-11** mascot-creator, the hardest skill, broken into four sub-phases by feature
7. **Phase 12** mascot-pack
8. **Phase 13** icon-set-creator (relatively easier given prior work)
9. **Phases 14-17** cross-cutting polish, docs, release

## Phase index

| # | Skill | Version | Goal | Doc |
|---|---|---|---|---|
| **00-preflight** | planning | — | Verify OpenRouter API + model matrix before implementation | [phase-00-preflight.md](phase-00-preflight.md) |
| **00** | shared/ | — | Skeleton: openrouter_client, image_utils, config | [phase-00-skeleton.md](phase-00-skeleton.md) |
| **01** | icon-creator | v0.1 | Single shot, no presets, master only | [phase-01-icon-creator-v0.1.md](phase-01-icon-creator-v0.1.md) |
| **02** | icon-creator | v0.2 | All 9 style presets + reference image | [phase-02-icon-creator-v0.2.md](phase-02-icon-creator-v0.2.md) |
| **03** | icon-creator | v0.3 | Multi-shot, validator, iteration | [phase-03-icon-creator-v0.3.md](phase-03-icon-creator-v0.3.md) |
| **04** | app-icon-pack | v1.0 | iOS + Android + Web | [phase-04-app-icon-pack-v1.0.md](phase-04-app-icon-pack-v1.0.md) |
| **05** | app-icon-pack | v1.1 | + macOS + watchOS + Windows | [phase-05-app-icon-pack-v1.1.md](phase-05-app-icon-pack-v1.1.md) |
| **06** | png-to-svg | v0.1 | vtracer integration, flat icons | [phase-06-png-to-svg-v0.1.md](phase-06-png-to-svg-v0.1.md) |
| **07** | png-to-svg | v0.2 | + potrace + imagetracer + auto-select | [phase-07-png-to-svg-v0.2.md](phase-07-png-to-svg-v0.2.md) |
| **08** | mascot-creator | v0.1 | Master generation, type+preset | [phase-08-mascot-creator-v0.1.md](phase-08-mascot-creator-v0.1.md) |
| **09** | mascot-creator | v0.2 | Multi-view character sheet | [phase-09-mascot-creator-v0.2.md](phase-09-mascot-creator-v0.2.md) |
| **10** | mascot-creator | v0.3 | Pose + expression variants | [phase-10-mascot-creator-v0.3.md](phase-10-mascot-creator-v0.3.md) |
| **11** | mascot-creator | v0.4 | Outfit variants, style-guide.md | [phase-11-mascot-creator-v0.4.md](phase-11-mascot-creator-v0.4.md) |
| **12** | mascot-pack | v1.0 | Social + sticker + print + web | [phase-12-mascot-pack-v1.0.md](phase-12-mascot-pack-v1.0.md) |
| **13** | icon-set-creator | v1.0 | Coherent icon family | [phase-13-icon-set-creator-v1.0.md](phase-13-icon-set-creator-v1.0.md) |
| **14** | cross-skill | — | brand kit, style memory, replay | [phase-14-cross-skill.md](phase-14-cross-skill.md) |
| **15** | polish | — | Error handling, retry tuning, cost UX | [phase-15-polish.md](phase-15-polish.md) |
| **16** | docs | — | README, examples, install, troubleshooting | [phase-16-docs.md](phase-16-docs.md) |
| **17** | release | — | GitHub publish, version 1.0.0 | [phase-17-release.md](phase-17-release.md) |

## Acceptance test discipline

Each phase document has a section "Acceptance criteria." A phase is **not done** until:

- All listed automated tests pass
- All listed manual checks have been verified
- The acceptance test record is committed alongside the code/docs (a `phase-NN-acceptance.md` in the phase folder, based on [phase-acceptance-template.md](phase-acceptance-template.md))

This discipline is heavy-handed by design. We're building generation quality, not just code; visual checks need to be deliberate.

## What "test in OpenCode" means at each phase

The user wants to validate each phase in their own agent harness (OpenCode) as we go. Each phase doc has a "Test in OpenCode" section describing:

- The exact skill invocation to run
- What output to look for
- What to flag if anything looks off

This is the user's manual checkpoint before moving to the next phase.

## Estimated effort

Approximate; not a contract. Sized by complexity, not by calendar time.

| Phase | Size |
|---|---|
| 00-preflight | XS (documentation and API/model verification only) |
| 00 | M (shared infra is broad but well-understood) |
| 01 | S (smallest happy path, most pieces already in place after 00) |
| 02 | M (preset matrix + reference handling) |
| 03 | M (validator + iteration are nontrivial) |
| 04 | L (three platforms, lots of asset rules) |
| 05 | M (extending pattern from 04) |
| 06 | M (vtracer integration, suitability check) |
| 07 | M (multiple algorithm support, auto-select logic) |
| 08 | M (mascot type/preset matrix) |
| 09 | L (multi-view consistency is the first real consistency challenge) |
| 10 | XL (pose + expression variants, image-to-image, the hardest phase) |
| 11 | M (outfits + style-guide gen) |
| 12 | M (lots of size tables but mechanical) |
| 13 | L (set-level consistency is its own challenge) |
| 14 | M (cross-cutting, integration heavy) |
| 15 | M (polish work scales with surface area) |
| 16 | M (docs are long) |
| 17 | S (mechanical release work) |

Total: roughly 18 weeks of focused work for a single developer; less if some phases run in parallel after phase 04.
