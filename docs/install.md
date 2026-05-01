# Install

## Requirements

- Python 3.11+
- A local OpenRouter API key for generation skills
- Optional native tools for best vectorization quality: `potrace`, `cairosvg`, `vtracer`

## From a clone

```bash
git clone https://github.com/kaanygit/icon-creator-skills.git
cd icon-creator-skills
python -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
```

## API key

Preferred for OpenCode / GUI-launched agents:

```bash
mkdir -p ~/.icon-skills
printf '%s\n' 'sk-or-v1-your-key' > ~/.icon-skills/openrouter.key
chmod 600 ~/.icon-skills/openrouter.key
```

`~/.icon-skills/config.yaml`:

```yaml
openrouter:
  api_key_file: ~/.icon-skills/openrouter.key
```

Shell-only alternative:

```bash
export OPENROUTER_API_KEY="sk-or-v1-your-key"
```

## Verify

```bash
icon-skills doctor
python -m pytest
```

## OpenCode skills

Add each skill folder to OpenCode's `skills.paths`:

```json
{
  "skills": {
    "paths": [
      "/absolute/path/icon-creator-skills/skills/icon-creator",
      "/absolute/path/icon-creator-skills/skills/app-icon-pack",
      "/absolute/path/icon-creator-skills/skills/png-to-svg",
      "/absolute/path/icon-creator-skills/skills/mascot-creator",
      "/absolute/path/icon-creator-skills/skills/mascot-pack",
      "/absolute/path/icon-creator-skills/skills/icon-set-creator"
    ]
  }
}
```

Restart OpenCode after editing its config.
