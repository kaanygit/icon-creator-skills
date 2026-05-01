"""icon-skills command line entrypoint."""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image

from shared.config import load_config
from shared.errors import IconSkillsError, InputError
from shared.image_clients import resolve_model_for_provider, resolve_provider
from shared.openrouter_client import COST_LOG_PATH
from shared.security import scrub_text
from shared.style_memory import list_styles, load_style, remove_style, save_style


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "doctor":
            return doctor()
        if args.command == "cost":
            return cost_summary()
        if args.command == "styles":
            return styles_command(args)
        if args.command == "replay":
            return replay(args.run_dir)
    except IconSkillsError as exc:
        print(f"Error: {scrub_text(str(exc))}", file=sys.stderr)
        return 1
    parser.print_help()
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Utilities for icon-creator-skills.")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("doctor", help="Check environment and optional dependencies")
    sub.add_parser("cost", help="Show local OpenRouter cost summary")
    replay_parser = sub.add_parser("replay", help="Replay a supported previous run")
    replay_parser.add_argument("run_dir")

    styles = sub.add_parser("styles", help="Manage saved styles")
    styles_sub = styles.add_subparsers(dest="styles_command", required=True)
    save = styles_sub.add_parser("save")
    save.add_argument("--from", dest="from_dir", required=True)
    save.add_argument("--name", required=True)
    styles_sub.add_parser("list")
    show = styles_sub.add_parser("show")
    show.add_argument("name")
    remove = styles_sub.add_parser("remove")
    remove.add_argument("name")
    return parser


def doctor() -> int:
    config = load_config()
    print("Checking icon-creator-skills environment...")
    print(f"Python: {platform.python_version()}")
    print(f"Platform: {platform.platform()}")
    print(f"Pillow: {Image.__version__}")
    selected_provider = resolve_provider(config=config)
    print(f"Default image provider: {selected_provider}")
    for provider in ("openrouter", "openai", "google"):
        key_status = _api_key_status(config, provider)
        model = resolve_model_for_provider(
            provider=provider,
            requested_model=None,
            prompt_model="sourceful/riverflow-v2-fast-preview",
            config=config,
        )
        marker = " (default)" if provider == selected_provider else ""
        print(f"{provider} API key{marker}: {key_status}")
        print(f"{provider} model{marker}: {model}")
    for module in ("yaml", "jinja2", "requests"):
        print(f"{module}: {'ok' if _module_exists(module) else 'missing'}")
    for optional in ("cairosvg", "vtracer", "imagetracer", "cv2"):
        print(f"{optional}: {'ok' if _module_exists(optional) else 'optional missing'}")
    print(f"potrace: {'ok' if shutil.which('potrace') else 'optional missing'}")
    return 0 if _api_key_status(config, selected_provider) != "missing" else 1


def cost_summary() -> int:
    if not COST_LOG_PATH.exists():
        print("No local cost log found.")
        return 0
    entries = json.loads(COST_LOG_PATH.read_text(encoding="utf-8"))
    total = sum(float(item.get("cost_usd") or 0) for item in entries)
    print(f"Entries: {len(entries)}")
    print(f"Total estimated cost: ${total:.4f}")
    by_skill: dict[str, float] = {}
    for item in entries:
        skill = str(item.get("skill") or "unknown")
        by_skill[skill] = by_skill.get(skill, 0.0) + float(item.get("cost_usd") or 0)
    for skill, value in sorted(by_skill.items()):
        print(f"- {skill}: ${value:.4f}")
    return 0


def styles_command(args: argparse.Namespace) -> int:
    if args.styles_command == "save":
        style = save_style(run_dir=args.from_dir, name=args.name)
        print(style.path)
        return 0
    if args.styles_command == "list":
        for style in list_styles():
            print(style.name)
        return 0
    if args.styles_command == "show":
        style = load_style(args.name)
        print(json.dumps(style.metadata, indent=2))
        return 0
    if args.styles_command == "remove":
        remove_style(args.name)
        print(f"Removed {args.name}")
        return 0
    return 1


def replay(run_dir: str | Path) -> int:
    source = Path(run_dir)
    metadata_path = source / "metadata.json"
    if not metadata_path.exists():
        raise InputError(f"metadata.json not found in {source}")
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    skill = metadata.get("skill")
    if skill == "mascot-pack":
        return _run(
            [
                sys.executable,
                "skills/mascot-pack/scripts/pack.py",
                "--master",
                str(metadata["master"]),
                "--targets",
                ",".join(metadata["targets"]),
            ]
        )
    if skill == "app-icon-pack":
        inputs = metadata.get("inputs", {})
        return _run(
            [
                sys.executable,
                "skills/app-icon-pack/scripts/pack.py",
                "--master",
                str(inputs.get("master") or metadata.get("master")),
                "--app-name",
                str(inputs.get("app_name") or "ReplayApp"),
                "--platforms",
                ",".join(inputs.get("platforms") or ["ios", "android", "web"]),
            ]
        )
    raise InputError(f"Replay is not automated for skill '{skill}' yet")


def _run(command: list[str]) -> int:
    completed = subprocess.run(command, check=False)
    return completed.returncode


def _api_key_status(config: dict[str, object], provider: str = "openrouter") -> str:
    env_names = {
        "openrouter": ("OPENROUTER_API_KEY",),
        "openai": ("OPENAI_API_KEY",),
        "google": ("GEMINI_API_KEY", "GOOGLE_API_KEY"),
    }
    for env_name in env_names.get(provider, ()):
        if os.getenv(env_name):
            return f"set in environment ({env_name})"
    provider_config = config.get(provider) or {}
    path_value = provider_config.get("api_key_file")  # type: ignore[union-attr]
    if path_value and Path(str(path_value)).expanduser().exists():
        return f"configured via {path_value}"
    return "missing"


def _openrouter_api_key_status(config: dict[str, object]) -> str:
    """Backward-compatible helper for older internal imports."""

    if os.getenv("OPENROUTER_API_KEY"):
        return "set in environment"
    path_value = (config.get("openrouter") or {}).get("api_key_file")  # type: ignore[union-attr]
    if path_value and Path(str(path_value)).expanduser().exists():
        return f"configured via {path_value}"
    return "missing"


def _module_exists(name: str) -> bool:
    import importlib.util

    return importlib.util.find_spec(name) is not None


if __name__ == "__main__":
    raise SystemExit(main())
