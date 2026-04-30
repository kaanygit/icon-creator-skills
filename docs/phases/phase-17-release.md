# Phase 17: Release — v1.0.0

Publish to GitHub publicly, tag v1.0.0, list in any agent-skill marketplaces, announce.

## Goal

The world can `pip install icon-creator-skills`, install the SKILL.md files into Claude Code or OpenCode, and use the toolkit. v1.0.0 is tagged. The repo is announce-ready.

## Pre-release checklist

### Code quality

- [ ] All phases 0–16 acceptance criteria met
- [ ] CI passes on macOS / Linux / Windows
- [ ] Lint clean (ruff)
- [ ] Type-check clean (mypy strict on shared/, optional on skills/)
- [ ] No TODO comments referencing post-v1 features without ticket links

### Tests

- [ ] All unit tests pass
- [ ] Snapshot tests pass with current templates
- [ ] Manual acceptance corpus reviewed and signed off:
  - 9 icon-creator presets eyeballed
  - 17 mascot-creator presets eyeballed
  - 12-icon set test passes coherence eye-test
  - Mascot variant consistency eye-tested at ≥4.0/5 average
  - All 6 platforms in app-icon-pack tested in real Xcode / Android Studio / browser

### Documentation

- [ ] README polished
- [ ] All `docs/` files current
- [ ] CHANGELOG.md committed at 1.0.0
- [ ] CONTRIBUTING.md current
- [ ] LICENSE present (MIT)
- [ ] All worked examples in `docs/examples/` runnable

### Security

- [ ] Log scrubber covers all log writes
- [ ] No secrets in any committed file
- [ ] `.gitignore` covers `.env`, `*.env`, `.env.local`, `output/`, `~/.icon-skills/cost-log.json`
- [ ] No telemetry code anywhere

### Packaging

- [ ] `pyproject.toml` declares all deps with sensible version bounds
- [ ] Console script `icon-skills` registered
- [ ] Skill packaging: each skill folder is self-contained and installable
- [ ] Distribution build (`python -m build`) produces wheel and sdist without errors
- [ ] Test install from wheel into a fresh venv

## Implementation steps

### 1. Final code freeze and audit
- Tag a `release-candidate` commit
- Run full CI matrix
- Manual acceptance corpus reviewed

### 2. Version bump
- `pyproject.toml` version → `1.0.0`
- All SKILL.md files reference v1.0.0
- CHANGELOG.md "1.0.0 — {date}" entry

### 3. Repository housekeeping
- Repo description, topics, social preview image
- `.github/ISSUE_TEMPLATE/` for bug, feature, preset proposal
- `.github/PULL_REQUEST_TEMPLATE.md`
- README badge row (CI status, PyPI version, license, Python version)

### 4. Publish to PyPI
- Test publish to TestPyPI first
- Verify install from TestPyPI in clean venv
- Publish to PyPI for real
- Verify `pip install icon-creator-skills` works

### 5. Tag and release on GitHub
- `git tag v1.0.0`
- Push tag
- Create GitHub Release with CHANGELOG content
- Attach `pyproject.toml` artifacts and a "skills/" zip

### 6. Skill marketplace submissions
- Submit to Claude Code skills directory (when available)
- Submit to OpenCode skills directory (when available)
- Cross-link in README

### 7. Announce
- Repo public
- Project Hunt submission (optional, post-v1)
- Twitter/X / LinkedIn / dev forums announcement (one paragraph + screenshot of preview grids)
- Blog post on lessons learned (post-v1, optional)

## Acceptance criteria

### Automated
- `pip install icon-creator-skills` from PyPI works in a fresh venv
- Console script `icon-skills doctor` runs and reports green
- CI passes on the v1.0.0 tag commit

### Manual
- A new user, given only the README, can:
  1. Install the package
  2. Set OPENROUTER_API_KEY
  3. Run `icon-creator "fox"` and get a usable icon
  4. Run `app-icon-pack` and get a working iOS/Android/Web pack
  5. Drop the pack into a real project and ship

- The 12-icon coherent set, the multi-pose mascot, and the 17-preset mascot comparison are all in `docs/examples/` as demo material

### Communications
- README has a clear "What this is, who it's for, what to read first"
- Announcement post is short, has a screenshot, links to repo and getting-started

## Out of scope for v1.0.0

- v1.1 features tracked in GitHub Issues / a `ROADMAP.md`:
  - Cloud style sync
  - GUI editor for `.iconrc.json`
  - Animated stickers
  - LoRA / IP-Adapter integration
  - Splash screens
  - visionOS support
  - Multi-pass region-based vectorization
  - Hosted docs site

These are deliberately deferred. Shipping v1.0.0 with a small, quality scope is the goal.

## Risks

- **PyPI name collision.** Reserve `icon-creator-skills` early. Have a backup name ready.
- **Marketplace listing requirements** vary by platform (Claude Code, OpenCode). Each may need its own README format or metadata file.
- **Real-world feedback after release** will surface issues. v1.0.1 patch release expected within 2 weeks of v1.0.0 to address.

## Dependencies on prior work

- Every prior phase. v1.0.0 is the integration of the whole.
