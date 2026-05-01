# Contributing

## Setup

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
```

## Checks

```bash
python -m pytest
python -m ruff check .
```

## Add a preset

1. Add a YAML entry under `shared/presets/`.
2. Add one or more Jinja templates under `shared/presets/prompt_templates/`.
3. Add or update tests.
4. Document the preset in `docs/presets/`.

## Review expectations

- No API keys or generated secrets in commits.
- No OpenRouter calls in automated tests.
- Keep skill folders self-contained.
