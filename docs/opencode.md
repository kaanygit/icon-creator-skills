# OpenCode Usage

## Install

Preferred:

```bash
npx skills add kaanygit/icon-creator-skills \
  --skill '*' \
  --agent opencode \
  --global \
  --yes
```

List available skills:

```bash
npx skills add kaanygit/icon-creator-skills --list
```

Update later:

```bash
npx skills update icon-creator -g -y
```

## Configure Provider

OpenCode may not inherit your shell startup files, so key files are usually more reliable
than shell exports.

```bash
mkdir -p ~/.icon-skills
printf '%s\n' 'sk-or-v1-your-key' > ~/.icon-skills/openrouter.key
chmod 600 ~/.icon-skills/openrouter.key
```

`~/.icon-skills/config.yaml`:

```yaml
image_generation:
  provider: openrouter

openrouter:
  api_key_file: ~/.icon-skills/openrouter.key
  model: sourceful/riverflow-v2-fast-preview
```

You can pin a different OpenRouter model:

```yaml
openrouter:
  api_key_file: ~/.icon-skills/openrouter.key
  model: google/gemini-2.5-flash-image
```

## What to Ask OpenCode

Generate an icon:

```text
Use icon-creator to create a gradient app icon for "geometric fox finance app".
Use 3 variants and copy the output folder path back to me.
```

Generate a mascot:

```text
Use mascot-creator to create a stylized cartoon-2d mascot: friendly fox explorer.
Keep the test cheap with --variants 1 --best-of-n 1.
```

Package an existing master icon:

```text
Use app-icon-pack on output/my-icon/master.png for iOS, Android, and Web.
```

## Cost Discipline

Mascot and icon-set generation can fan out into many provider calls. For quick checks, ask
OpenCode to use `--variants 1 --best-of-n 1`, or use existing output files with packaging
skills that do not call an image provider.
