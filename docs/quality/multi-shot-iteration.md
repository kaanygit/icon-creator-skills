# Quality feature: multi-shot generation + iteration

Image generation is non-deterministic. A single shot is rarely the best output. Every generation skill produces multiple variants and supports refining on a chosen one.

## Multi-shot generation

### Default: 3 variants per call

`icon-creator`, `icon-set-creator` (per member), and `mascot-creator` (for master selection) all default to producing **3 variants** per call. The user picks; the skill stores the rest for later reference.

### Why 3?

- Cheap enough to be the universal default (3× a single-icon cost is sub-dollar at typical pricing)
- Enough diversity to surface stylistic alternatives
- Few enough that the user can scan all three and pick without choice paralysis

User can override:
- `--variants 1` for single-shot (fast, cheap, accept-as-is)
- `--variants 6` for max diversity (or 9 in rare cases)

Soft cap: 6 by default. Going higher requires `--allow-variants-over-cap` to prevent accidental cost spikes.

### Diversity strategy

- Same prompt, **different seeds** (seed = `base_seed + i`)
- Some skills additionally vary one prompt knob: e.g. `icon-creator` slightly perturbs the style phrase across variants ("flat-style" vs "modern flat" vs "minimalist flat")
- For mascot-master, variants vary in slight pose/expression to give the user a range

Logged in `metadata.json` per variant so reruns are reproducible.

### Auto-pick vs user-pick

Two modes:

**Auto-pick (default).** `quality_validator` scores all variants; the highest-scoring one is named `master.png`. The others remain in `variants/`. User reviews if dissatisfied.

**User-pick.** With `--interactive` (or when running through an agent that supports it), the skill presents the variants in a preview grid and asks the user which to promote. Selected variant becomes `master.png`.

Auto-pick is the default because most agent harness invocations are non-interactive. User-pick is opt-in for cases where the user wants to drive selection.

## Iteration

### "Refine on this one"

After a run, the user has `master.png` and the variants. They might want to refine:

- "Same icon but more minimal"
- "Same fox but with different ear shape"
- "Same color scheme but tweaked angle"

The skill exposes `--refine path/to/master.png` (or `--refine variant-2`) which:

1. Loads the chosen image
2. Extracts style hints via `vision_analyzer`
3. Reconstructs the original prompt (from sibling `metadata.json` if present)
4. Builds a new prompt: `"<original> + <user refinement instruction>"`
5. Runs image-to-image with the chosen image as reference (when model supports)
6. Produces a new run directory tagged as a refinement, linked back to the parent run

```
output/mountain-icon-20260429-153122/
output/mountain-icon-20260429-153815-refinement-of-153122/
```

`metadata.json` includes `refinement_of: "../mountain-icon-20260429-153122"` for traceability.

### Refinement vs full regeneration

If the user provides `--refine` AND `--description` (a fresh description), the description wins; the previous run is treated as **style anchor only**, not as content reference. This is how style-memory works (see [brand-kit.md](brand-kit.md)).

If the user provides `--refine` only, the previous prompt is reused with the modification appended.

## Cost control around multi-shot

Multi-shot generation is the biggest cost multiplier. Cost-tracking surfaces:

- **Pre-run estimate** for any call producing > 1 variant; printed as `"This will produce 3 variants × ~$0.02 ≈ $0.06"`
- **Per-variant cost in metadata.json**
- **Cumulative session cost**

If estimated cost exceeds the user's threshold (default $1.00 per call, $5.00 per session), confirmation is requested before the run.

## Variant retention

By default, all variants are kept on disk. Disk is cheap; regenerating is expensive. Future enhancement: `--cleanup-variants` flag for users who want only the master after auto-pick.

## Best-of-N for hardest cases (mascot pose/expression)

For mascot variants where consistency matters, a special "best-of-N" mode runs N candidates per pose/expression, runs `consistency_checker` on each, and keeps the best. Default N = 3 for high-stakes variants. User can override with `--best-of-n 5` for extra effort at the cost of more API calls.
