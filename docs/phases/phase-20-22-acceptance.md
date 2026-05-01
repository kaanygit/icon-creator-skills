# Phase 20-22 Acceptance: OpenCode UX, Gallery, Skills CLI Install

Date: 2026-05-02

## Scope

Phase 19 quality matrix is intentionally skipped. This acceptance record covers the next
practical distribution work:

- Phase 20: OpenCode UX polish
- Phase 21: visual gallery
- Phase 22: Skills CLI installation path
- v1.1.0 release packaging

## Acceptance Checklist

- [x] README documents `npx skills add kaanygit/icon-creator-skills`.
- [x] README documents listing skills before install.
- [x] README documents installing all skills and one skill into OpenCode.
- [x] `docs/install.md` makes Skills CLI installation the primary OpenCode path.
- [x] `docs/opencode.md` provides OpenCode prompts, provider config, and cost discipline guidance.
- [x] `docs/gallery.md` shows prompt, command, output image, and expected files.
- [x] `icon-skills doctor` reports default provider, provider models, and provider key status.
- [x] `icon-skills doctor --fix` creates local config scaffolding.
- [x] `icon-skills estimate` reports call/image counts without provider calls.
- [x] `icon-skills create-icon`, `create-app-icon-pack`, `create-mascot`, and `create-icon-set` wrap the long script commands.
- [x] Offline tests cover provider key status checks.
- [x] Marketplace listing copy exists in `docs/marketplace.md`.
- [x] `npx skills add . --list` discovers all 6 skills locally.
- [x] No live provider API calls are required for acceptance.

## Skills CLI Notes

The Vercel Skills CLI discovers skills in a repository under `skills/`, so this repo is
already structurally compatible:

```bash
npx skills add kaanygit/icon-creator-skills --list
npx skills add kaanygit/icon-creator-skills --skill '*' --agent opencode --global --yes
```

OpenCode's global install target is managed by the Skills CLI; users do not need to edit
OpenCode paths manually unless `npx skills` is unavailable.
