# Shared modules

Pure-Python primitives used by every skill. No skill UX, no prompt content, no domain-specific logic. Each module owns one concern, exposes a small API, and is testable in isolation.

## Modules

| Module | Owns | Used by |
|---|---|---|
| [openrouter-client.md](openrouter-client.md) | OpenRouter API calls, retry, cost tracking, fallbacks | every skill that generates images |
| [vision-analyzer.md](vision-analyzer.md) | Reference-image analysis, style extraction, brand-similarity warnings | icon-creator, icon-set-creator, mascot-creator |
| [prompt-builder.md](prompt-builder.md) | Template engine, preset injection, negative-prompt assembly | every generation skill |
| [image-utils.md](image-utils.md) | Resize, crop, padding, bg removal, format conversion, alpha cleanup | every skill |
| [consistency-checker.md](consistency-checker.md) | Histogram, edge density, perceptual hash, similarity scoring | icon-set-creator, mascot-creator |
| [quality-validator.md](quality-validator.md) | Readability, contrast, centering, "is this a usable icon" checks | icon-creator, icon-set-creator |

## Design principles

1. **No skill imports another skill.** All shared logic lives here. Skills import from `shared/`; never from `skills/<other-skill>/`.
2. **Fail loudly on missing native deps.** Each module's optional native dependencies (potrace, vtracer, rembg) are guarded; missing deps produce actionable errors with install commands, never silent fallbacks.
3. **Pure functions over stateful classes.** Most APIs take inputs and return outputs. Stateful classes only where genuinely needed (e.g. `OpenRouterClient` to hold session + cost log).
4. **Configuration in YAML, not Python.** Style presets, model mappings, platform size tables — all YAML in `shared/presets/`. Python loads them; doesn't define them.
5. **Logging is structured.** Every shared module emits structured logs (JSON line format) under `logs/{module}.log`. Skills aggregate these into the run directory.

## Cross-cutting: error model

A shared `IconSkillsError` base with subclasses for each failure category:

```python
class IconSkillsError(Exception): ...
class OpenRouterError(IconSkillsError): ...           # API failures, rate limit, invalid model
class DependencyMissingError(IconSkillsError): ...    # native lib not installed
class ValidationError(IconSkillsError): ...           # quality / consistency check failed
class InputError(IconSkillsError): ...                # bad user input
class CostThresholdError(IconSkillsError): ...        # estimated cost exceeds confirmation
```

Skills catch and translate these to user-friendly messages.

## Cross-cutting: configuration loading

```python
from shared.config import load_config
cfg = load_config()
# Merges in priority order:
#   1. shared/defaults.yaml
#   2. ~/.icon-skills/config.yaml
#   3. {project_root}/.iconrc.json
#   4. per-call args (passed in by skill)
```

`OPENROUTER_API_KEY` is **only** read from environment; never from the merged config blob. This is a deliberate isolation.

## Cross-cutting: testing

Each module ships a `tests/` directory with unit tests. The shared layer has zero external API calls in tests; OpenRouter calls are mocked. Skill-level integration tests in `skills/<skill>/tests/` may make real API calls, gated behind a `RUN_LIVE_TESTS=1` env var.
