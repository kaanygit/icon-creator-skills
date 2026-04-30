# Phase 15: Polish — error handling, retry tuning, UX

Cross-cutting fixes after all skills are functionally complete. This is the "make it actually pleasant to use" phase.

## Goal

A fresh user installs the toolkit and goes through their first 5 runs without hitting any unfriendly errors, confusing output, or unexplained failures.

## Workstreams

### 1. Error message audit

Every `IconSkillsError` raise site reviewed:
- Is the message helpful? (does it tell the user what to do?)
- Does it cite the relevant doc?
- Is the right exception class used?
- Is the API key never echoed in messages?

Common improvements:
- "OpenRouter API call failed" → "OpenRouter API call failed: model 'foo' not found. Available models for this preset: bar, baz. Pin a different model with --model."
- "Validation failed" → "Validation failed: readable_at_16px scored 0.62 (threshold 0.70). Try regenerating with --variants 6 or use a different style preset."

### 2. Retry tuning

Review retry behavior across all skills with real-world output corpus:
- Are validator thresholds set right?
- Are augmented-prompt retries actually helping?
- Are consistency thresholds for mascot variants too strict / loose?
- Cost vs quality tradeoffs adjusted

### 3. Cost UX

- Pre-run estimates accurate vs actual within ±20%
- Per-run summary readable, not buried in JSON
- Lifetime cost log reviewable via `icon-skills cost summary`
- Configurable thresholds documented

### 4. Doctor command

```
> icon-skills doctor
Checking environment...
✓ Python 3.11.4
✓ OPENROUTER_API_KEY set (last 4: ****abcd)
✓ Pillow 10.4.0
✓ rembg model cached at ~/.u2net/u2net.onnx
✓ cairosvg 2.7.0 (libcairo 1.16.0)
⚠ vtracer-py not installed — png-to-svg unavailable. Install: pip install vtracer-py
✗ potrace binary not found — png-to-svg potrace algorithm unavailable. Install: brew install potrace (macOS) / apt install potrace (Ubuntu)
✓ All skill modules importable
```

Lists native deps, optional deps, OPENROUTER_API_KEY presence (not value), version pins. Exits 0 if usable, 1 if critical deps missing.

### 5. Log scrubbing

Audit all log writes; verify no API keys, no full prompts (only hashes), no private file paths leaked.

### 6. Output directory hygiene

- Stable run IDs (slug + timestamp)
- Old runs not auto-deleted (user controls)
- `.gitignore` entry suggested in per-run README

### 7. Performance

- Resize operations parallelized within reason
- Image-to-image latency improvements where possible
- Avoid redundant model calls (cache vision_analyzer results within session)

### 8. Cross-platform install testing

Install from a clean pyproject install on:
- macOS (Apple Silicon + Intel)
- Linux (Ubuntu LTS)
- Windows 11

Document any platform-specific install hints (Cairo on Windows, Potrace on macOS via brew, etc.).

## Implementation steps

1. Sweep all `raise` statements in `shared/` and `skills/`; log a list of ones needing improvement; address top 50%
2. Run the corpus tests collected during phases 09-13 (mascot consistency rates, set coherence rates); tune thresholds
3. Implement `icon-skills doctor` command
4. Implement log scrubbing utilities used by all logging output
5. Write platform-specific install hints in README
6. CI matrix runs install + test on macOS, Linux, Windows

## Acceptance criteria

### Automated
- New CI matrix passes on macOS, Linux, Windows
- Log-scrubber tests demonstrate no key/prompt-text leakage
- Doctor command exits 0 in fully-installed env, 1 with informative report when deps missing

### Manual
- User study: 3 fresh-install attempts on different machines; first-run success without consulting docs is the bar
- Error message review pass: hand-crafted failure scenarios produce helpful messages
- 10-run corpus across all skills with all retries; confirm thresholds feel right (not too strict, not too loose)

### Documentation
- README has a Troubleshooting section
- README has a "What if it doesn't work?" / `icon-skills doctor` mention

## Test in OpenCode

Doctor in OpenCode:
```
> icon-skills doctor
```
Confirm: doctor output appears in the chat / terminal interface, hints are actionable.

## Out of scope for phase 15

- Performance benchmarks vs. competitors (no competitor exists at this scope)
- Localization of error messages (post-v1)
- Telemetry / usage analytics (explicitly never, per ADR-010)

## Risks

- **Threshold tuning is subjective.** Calibrate against the corpus, accept that some users will want to override; document overrides clearly.
- **Cross-platform native dep install always has surprises.** Docs need to be specific; doctor command must catch the common ones.

## Dependencies on prior work

- All prior phases — this is the integration polish that follows feature-complete.
