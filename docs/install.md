# Install

## Requirements

- Python 3.11+
- A local API key for at least one generation provider: OpenRouter, OpenAI, or Google Gemini
- Optional native tools for best vectorization quality: `potrace`, `cairosvg`, `vtracer`

## From a clone

```bash
git clone https://github.com/kaanygit/icon-creator-skills.git
cd icon-creator-skills
python -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
```

## API keys and provider defaults

Preferred for OpenCode / GUI-launched agents:

```bash
mkdir -p ~/.icon-skills
printf '%s\n' 'sk-or-v1-your-key' > ~/.icon-skills/openrouter.key
printf '%s\n' 'sk-your-openai-key' > ~/.icon-skills/openai.key
printf '%s\n' 'your-google-gemini-key' > ~/.icon-skills/google.key
chmod 600 ~/.icon-skills/openrouter.key
chmod 600 ~/.icon-skills/openai.key
chmod 600 ~/.icon-skills/google.key
```

`~/.icon-skills/config.yaml`:

```yaml
image_generation:
  provider: openrouter

openrouter:
  api_key_file: ~/.icon-skills/openrouter.key
  model: sourceful/riverflow-v2-fast-preview

openai:
  api_key_file: ~/.icon-skills/openai.key
  model: gpt-image-1

google:
  api_key_file: ~/.icon-skills/google.key
  model: gemini-2.5-flash-image
```

Shell-only alternatives:

```bash
export OPENROUTER_API_KEY="sk-or-v1-your-key"
export OPENAI_API_KEY="sk-your-openai-key"
export GEMINI_API_KEY="your-google-gemini-key"
```

Override provider and model per run when needed:

```bash
python skills/icon-creator/scripts/generate.py \
  --description "minimal fox" \
  --provider openrouter \
  --model google/gemini-2.5-flash-image
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
