# Phase 03 acceptance

## Phase

- Phase: 03
- Commit: this commit
- Date: 2026-05-01
- Reviewer: kaanygit / Codex
- Environment: macOS, zsh, Python 3.14.4 in local `.venv`

## Scope completed

- [x] `shared/quality_validator.py` added.
- [x] Validator profiles implemented for app icons, UI icons, favicons, logo marks, and mascot masters.
- [x] `icon-creator` now defaults to 3 variants.
- [x] `--variants`, `--seed`, and `--refine` added.
- [x] All candidates are saved under `variants/`.
- [x] Validator auto-picks the best candidate and promotes it to `master.png`.
- [x] `preview.png` grid generated for quick review.
- [x] `metadata.json` records variants, validation results, retry count, selected variant, and refinement links.
- [x] One validation-failure retry is implemented with a quality-correction prompt.
- [x] Default image model switched to `sourceful/riverflow-v2-fast-preview`.
- [x] Riverflow pricing recorded as `$0.03` per output image.
- [x] README, `SKILL.md`, skill README, model matrix, and quality docs updated.

## Automated checks

```bash
.venv/bin/python -m pytest
# result: 28 passed
```

```bash
.venv/bin/python -m ruff check .
# result: All checks passed
```

## Live generation checks

Default model:

```text
sourceful/riverflow-v2-fast-preview
```

Multi-variant run:

```bash
python skills/icon-creator/scripts/generate.py \
  --description "geometric fox app icon" \
  --style-preset gradient \
  --variants 3 \
  --seed 42
```

Result:

- [x] Output: `output/geometric-fox-app-icon-20260501-101843/`
- [x] `variants/1.png`, `variants/2.png`, and `variants/3.png` created.
- [x] `preview.png` created.
- [x] `master.png` promoted from picked variant `2`.
- [x] `metadata.json` reports `picked_passed: true`.
- [x] Cost recorded as `$0.09`.

Refinement run:

```bash
python skills/icon-creator/scripts/generate.py \
  --refine output/geometric-fox-app-icon-20260501-101843/master.png \
  --description "more minimal geometric fox" \
  --style-preset gradient \
  --variants 2 \
  --seed 99
```

Result:

- [x] Output: `output/geometric-fox-app-icon-refined-20260501-102011/`
- [x] `variants/1.png` and `variants/2.png` created.
- [x] `preview.png` created.
- [x] `master.png` promoted from picked variant `1`.
- [x] `metadata.json` reports `picked_passed: true`.
- [x] `refinement_of` links back to the parent `master.png` and `metadata.json`.
- [x] Cost recorded as `$0.06`.

Final live outputs copied to:

```text
/Users/kaanygit/Desktop/icon-phase03-variants/
```

## Manual checks

- [x] User reviewed current generated outputs and confirmed the flow is working well.
- [x] Extra 5-preset live sweep intentionally stopped to preserve OpenRouter credits.
- [x] Phase 02 already covered 9-preset visual generation; Phase 03 live check focused on multi-shot, validator selection, and refinement with the final Riverflow model.

## OpenCode / harness check

- Required for this phase: yes
- Command or invocation:
  - `/icon-creator "fox" --variants 3`
  - `/icon-creator --refine output/fox-{prev-ts}/master.png "more geometric"`
- Result: not run in OpenCode in this environment
- Notes: terminal live generation passed; OpenCode harness validation remains a manual follow-up.

## Known issues

- `no_text_artifacts` uses a lightweight local heuristic in Phase 03, not OCR. Full OCR-backed text detection remains future hardening.
- App icons can validly have opaque backgrounds, so `transparent_bg` is optional for the `app-icon` profile and remains required for `ui-icon` / `favicon`.
- Sourceful lists a 4.5MB image-input request limit; large refinement references may need URL-based upload support in a later phase.

## Sign-off

- [x] Phase implementation accepted
- [x] Multi-variant generation accepted
- [x] Validator auto-pick accepted
- [x] Refinement accepted
- [ ] OpenCode harness check accepted
- [x] Safe to start Phase 04 after OpenCode validation is run or explicitly deferred
