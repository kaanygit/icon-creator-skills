# Phase 14: Cross-skill features — brand kit, style memory, replay

Add `.iconrc.json` brand kit support, the style-memory store, the `replay` command, and full pre-run cost confirmation across all skills.

## Goal

A user with a `.iconrc.json` in their project root never re-types brand colors and preset preferences. Saved styles are recallable by name. Any past run is replayable.

## Deliverables

### `.iconrc.json` support

- `shared/config.py` extended to discover `.iconrc.json` upward from CWD
- Schema validation against bundled JSON Schema
- Resolution order: hardcoded defaults → user config → project config → CLI args (per [docs/quality/brand-kit.md](../quality/brand-kit.md))

### Style memory

```
~/.icon-skills/styles/
└── {style-name}/
    ├── style-anchor.png
    ├── style-guide.md
    └── metadata.json
```

CLI commands:
- `icon-skills styles save --from <run-dir> --name <name>`
- `icon-skills styles list`
- `icon-skills styles show <name>`
- `icon-skills styles remove <name>`
- All generation skills accept `--style <name>` to recall

### Replay

```
icon-skills replay <run-dir>
```

Re-runs the same skill with the captured inputs from `metadata.json`. Output is a new run dir tagged `replay-of`.

### Cost confirmation

- Every skill that estimates cost above the threshold (default $1.00) prompts before proceeding
- Hard cap (default $10.00 per call) requires `--allow-large-cost` flag
- Session cumulative tracker; warning at $5.00 default

### `icon-skills` CLI entrypoint

A single CLI that dispatches to skills:
```
icon-skills <command> [args]
```
Where commands include `replay`, `styles`, `cost`, `doctor` (per phase 15).

## Implementation steps

1. Implement `.iconrc.json` discovery and merge logic in `config.py`
2. Add JSON Schema for `.iconrc.json` (bundled with package)
3. Implement style-memory store + CLI subcommands
4. Implement `replay` command (load metadata, dispatch to skill, write new run dir with cross-link)
5. Implement cost-confirmation prompt machinery in `openrouter_client` (pre-run estimate API + confirmation hook)
6. Wire confirmation across all skills' run start
7. Build `icon-skills` console script entrypoint via pyproject `project.scripts`
8. Update all skill READMEs with the new flags and commands
9. Tests:
   - `.iconrc.json` discovery from nested directories
   - Style save / load / list / remove
   - Replay produces valid output with `replay_of` set
   - Cost confirmation required above threshold; refused declines abort cleanly

## Acceptance criteria

### Automated
- Config merge tested with synthetic configs at each layer
- Style memory roundtrip: save → load → recall produces correct anchor and palette
- Replay roundtrip: known run replayed produces a valid new run dir with metadata cross-link
- Cost-threshold tests: above threshold → confirmation; refusal aborts; allowed proceeds

### Manual
- Set up a `.iconrc.json` in a project, run icon-creator and icon-set-creator without explicit args, confirm brand defaults applied
- Save a style from an icon-creator run, run icon-creator again with `--style <name>`, confirm output reflects saved palette/style
- Replay an old mascot-creator run, confirm output mascot is recognizably the same character

### Documentation
- README adds a "brand-kit setup" section with example `.iconrc.json`
- README adds a "save and reuse styles" section
- Per-skill SKILL.md mentions `--style` recall

## Test in OpenCode

```
> /icon-creator "rocket"          # in a directory with .iconrc.json present
... uses brand colors and preset automatically

> icon-skills styles save --from output/rocket-{ts}/ --name brand-flat
> /icon-creator "anchor" --style brand-flat
... uses the saved style

> icon-skills replay output/rocket-{ts}/
... new run with replay_of metadata
```

## Out of scope for phase 14

- Cloud-synced style memory (post-v1)
- Team-shared brand kits (post-v1)
- Editable GUI for `.iconrc.json` (post-v1)
- Auto-suggesting a brand kit from existing project assets (post-v1)
- Cost forecasts beyond per-call estimate (no rolling daily budget enforcement) (post-v1)

## Risks

- **`.iconrc.json` discovery edge cases**: nested projects, symlinks. Tests cover common cases; document limitations.
- **Style memory diverges from current preset list** if YAML is refactored. Style metadata records preset version SHA; warn on mismatch when recalling old styles.
- **Cost confirmation in non-interactive contexts** (CI, batch jobs). Provide `--yes` to auto-accept up to a configurable limit.

## Dependencies on prior work

- All prior phases (skills produce metadata that replay and styles depend on)
