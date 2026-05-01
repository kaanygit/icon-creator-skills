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

from shared.config import USER_CONFIG, load_config
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
            return doctor(fix=args.fix)
        if args.command == "cost":
            return cost_summary()
        if args.command == "estimate":
            return estimate_command(args)
        if args.command in {
            "create-icon",
            "create-app-icon-pack",
            "create-mascot",
            "create-icon-set",
        }:
            return create_command(args)
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
    doctor_parser = sub.add_parser("doctor", help="Check environment and optional dependencies")
    doctor_parser.add_argument("--fix", action="store_true", help="Create local config scaffolding")
    sub.add_parser("cost", help="Show local OpenRouter cost summary")
    _add_estimate_parser(sub)
    _add_create_parsers(sub)
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


def doctor(*, fix: bool = False) -> int:
    if fix:
        _doctor_fix()
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


def estimate_command(args: argparse.Namespace) -> int:
    estimate = _estimate(args)
    print(f"Skill: {estimate['skill']}")
    print(f"Estimated provider requests: {estimate['requests']}")
    print(f"Estimated output images: {estimate['images']}")
    if estimate.get("notes"):
        print("Notes:")
        for note in estimate["notes"]:
            print(f"- {note}")
    return 0


def create_command(args: argparse.Namespace) -> int:
    return _run(_create_command(args))


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


def _add_estimate_parser(sub: argparse._SubParsersAction) -> None:
    estimate = sub.add_parser("estimate", help="Estimate provider calls without making API calls")
    estimate_sub = estimate.add_subparsers(dest="estimate_kind", required=True)

    icon = estimate_sub.add_parser("icon", help="Estimate icon generation")
    icon.add_argument("--variants", type=int, default=3)
    icon.add_argument("--include-retry", action="store_true")

    mascot = estimate_sub.add_parser("mascot", help="Estimate mascot generation")
    mascot.add_argument("--variants", type=int, default=3)
    mascot.add_argument("--views", default="")
    mascot.add_argument("--poses", default="")
    mascot.add_argument("--expressions", default="")
    mascot.add_argument("--outfits", default="")
    mascot.add_argument("--matrix", action="store_true")
    mascot.add_argument("--best-of-n", type=int, default=3)

    icon_set = estimate_sub.add_parser("icon-set", help="Estimate icon-set generation")
    icon_set.add_argument("--icons", required=True, help="JSON list or comma-separated subjects")
    icon_set.add_argument("--best-of-n", type=int, default=3)
    icon_set.add_argument("--reference-icon", action="store_true")


def _add_create_parsers(sub: argparse._SubParsersAction) -> None:
    icon = sub.add_parser("create-icon", help="Generate one icon via icon-creator")
    icon.add_argument("--description", required=True)
    icon.add_argument("--style-preset", default="flat")
    icon.add_argument("--colors", default=None)
    icon.add_argument("--reference-image", default=None)
    icon.add_argument("--style", default=None)
    icon.add_argument("--variants", type=int, default=3)
    icon.add_argument("--seed", type=int, default=None)
    icon.add_argument("--refine", default=None)
    _add_provider_args(icon)
    icon.add_argument("--output-dir", default="output")

    pack = sub.add_parser("create-app-icon-pack", help="Package a master icon for platforms")
    pack.add_argument("--master", required=True)
    pack.add_argument("--app-name", default="MyApp")
    pack.add_argument("--platforms", default="all")
    pack.add_argument("--bg-color", default="#FFFFFF")
    pack.add_argument("--no-zip", action="store_true")
    pack.add_argument("--no-validate", action="store_true")
    pack.add_argument("--output-dir", default="output")

    mascot = sub.add_parser("create-mascot", help="Generate a mascot via mascot-creator")
    mascot.add_argument("--description", required=True)
    mascot.add_argument("--type", required=True, dest="mascot_type")
    mascot.add_argument("--preset", default=None)
    mascot.add_argument("--personality", default=None)
    mascot.add_argument("--variants", type=int, default=3)
    mascot.add_argument("--seed", type=int, default=None)
    mascot.add_argument("--views", default=None)
    mascot.add_argument("--poses", default=None)
    mascot.add_argument("--expressions", default=None)
    mascot.add_argument("--outfits", default=None)
    mascot.add_argument("--matrix", action="store_true")
    mascot.add_argument("--best-of-n", type=int, default=3)
    mascot.add_argument("--reference-image", default=None)
    mascot.add_argument("--style", default=None)
    mascot.add_argument("--mascot-name", default=None)
    _add_provider_args(mascot)
    mascot.add_argument("--output-dir", default="output")

    icon_set = sub.add_parser("create-icon-set", help="Generate a coherent icon family")
    icon_set.add_argument("--icons", required=True)
    icon_set.add_argument("--style-preset", required=True)
    icon_set.add_argument("--colors", default=None)
    icon_set.add_argument("--reference-icon", default=None)
    icon_set.add_argument("--style", default=None)
    icon_set.add_argument("--set-name", default=None)
    icon_set.add_argument("--stroke-width", default=None)
    icon_set.add_argument("--corner-radius", default=None)
    icon_set.add_argument("--seed-base", type=int, default=None)
    icon_set.add_argument("--best-of-n", type=int, default=3)
    _add_provider_args(icon_set)
    icon_set.add_argument("--output-dir", default="output")


def _add_provider_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--provider", default=None, help="openrouter, openai, or google")
    parser.add_argument("--model", default=None, help="Provider model override")


def _estimate(args: argparse.Namespace) -> dict[str, object]:
    if args.estimate_kind == "icon":
        requests = 2 if args.include_retry else 1
        return {
            "skill": "icon-creator",
            "requests": requests,
            "images": args.variants * requests,
            "notes": ["Validation retry is only used when the first batch fails."]
            if args.include_retry
            else ["Use --include-retry for worst-case retry estimate."],
        }
    if args.estimate_kind == "mascot":
        views = _csv(args.views)
        poses = _csv(args.poses)
        expressions = _csv(args.expressions)
        outfits = _csv(args.outfits)
        named = len(views) + len(poses) + len(expressions) + len(outfits)
        matrix = len(poses) * len(expressions) if args.matrix else 0
        variant_requests = (named + matrix) * args.best_of_n
        return {
            "skill": "mascot-creator",
            "requests": 1 + variant_requests,
            "images": args.variants + variant_requests,
            "notes": [
                "Master generation is one request with --variants images.",
                "Each requested variant can use up to --best-of-n attempts.",
            ],
        }
    if args.estimate_kind == "icon-set":
        icons = _parse_items(args.icons)
        if not icons:
            raise InputError("--icons cannot be empty")
        member_count = len(icons) if args.reference_icon else max(0, len(icons) - 1)
        requests = (0 if args.reference_icon else 1) + member_count * args.best_of_n
        return {
            "skill": "icon-set-creator",
            "requests": requests,
            "images": (0 if args.reference_icon else min(3, args.best_of_n))
            + member_count * args.best_of_n,
            "notes": [
                "Without --reference-icon, the first icon is generated as the style anchor.",
                "Each remaining icon can use up to --best-of-n attempts.",
            ],
        }
    raise InputError(f"Unknown estimate kind: {args.estimate_kind}")


def _create_command(args: argparse.Namespace) -> list[str]:
    root = Path(__file__).resolve().parents[1]
    if args.command == "create-icon":
        command = [sys.executable, str(root / "skills/icon-creator/scripts/generate.py")]
        _append(command, "--description", args.description)
        _append(command, "--style-preset", args.style_preset)
        _append_optional(command, "--colors", args.colors)
        _append_optional(command, "--reference-image", args.reference_image)
        _append_optional(command, "--style", args.style)
        _append(command, "--variants", args.variants)
        _append_optional(command, "--seed", args.seed)
        _append_optional(command, "--refine", args.refine)
        _append_provider(command, args)
        _append(command, "--output-dir", args.output_dir)
        return command
    if args.command == "create-app-icon-pack":
        command = [sys.executable, str(root / "skills/app-icon-pack/scripts/pack.py")]
        _append(command, "--master", args.master)
        _append(command, "--app-name", args.app_name)
        _append(command, "--platforms", args.platforms)
        _append(command, "--bg-color", args.bg_color)
        _append(command, "--output-dir", args.output_dir)
        _append_flag(command, "--no-zip", args.no_zip)
        _append_flag(command, "--no-validate", args.no_validate)
        return command
    if args.command == "create-mascot":
        command = [sys.executable, str(root / "skills/mascot-creator/scripts/generate.py")]
        _append(command, "--description", args.description)
        _append(command, "--type", args.mascot_type)
        _append_optional(command, "--preset", args.preset)
        _append_optional(command, "--personality", args.personality)
        _append(command, "--variants", args.variants)
        _append_optional(command, "--seed", args.seed)
        _append_optional(command, "--views", args.views)
        _append_optional(command, "--poses", args.poses)
        _append_optional(command, "--expressions", args.expressions)
        _append_optional(command, "--outfits", args.outfits)
        _append_flag(command, "--matrix", args.matrix)
        _append(command, "--best-of-n", args.best_of_n)
        _append_optional(command, "--reference-image", args.reference_image)
        _append_optional(command, "--style", args.style)
        _append_optional(command, "--mascot-name", args.mascot_name)
        _append_provider(command, args)
        _append(command, "--output-dir", args.output_dir)
        return command
    if args.command == "create-icon-set":
        command = [sys.executable, str(root / "skills/icon-set-creator/scripts/generate_set.py")]
        _append(command, "--icons", args.icons)
        _append(command, "--style-preset", args.style_preset)
        _append_optional(command, "--colors", args.colors)
        _append_optional(command, "--reference-icon", args.reference_icon)
        _append_optional(command, "--style", args.style)
        _append_optional(command, "--set-name", args.set_name)
        _append_optional(command, "--stroke-width", args.stroke_width)
        _append_optional(command, "--corner-radius", args.corner_radius)
        _append_optional(command, "--seed-base", args.seed_base)
        _append(command, "--best-of-n", args.best_of_n)
        _append_provider(command, args)
        _append(command, "--output-dir", args.output_dir)
        return command
    raise InputError(f"Unknown create command: {args.command}")


def _doctor_fix() -> None:
    user_dir = Path("~/.icon-skills").expanduser()
    user_dir.mkdir(parents=True, exist_ok=True)
    (user_dir / "styles").mkdir(exist_ok=True)
    config_path = Path(USER_CONFIG).expanduser()
    if not config_path.exists():
        config_path.write_text(_default_user_config(), encoding="utf-8")
        print(f"Created {config_path}")
    else:
        print(f"Config exists: {config_path}")
    print(f"Key directory ready: {user_dir}")


def _run(command: list[str]) -> int:
    completed = subprocess.run(command, check=False)
    return completed.returncode


def _append(command: list[str], flag: str, value: object) -> None:
    command.extend([flag, str(value)])


def _append_optional(command: list[str], flag: str, value: object | None) -> None:
    if value is not None:
        _append(command, flag, value)


def _append_flag(command: list[str], flag: str, enabled: bool) -> None:
    if enabled:
        command.append(flag)


def _append_provider(command: list[str], args: argparse.Namespace) -> None:
    _append_optional(command, "--provider", args.provider)
    _append_optional(command, "--model", args.model)


def _csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def _parse_items(value: str) -> list[str]:
    stripped = value.strip()
    if not stripped:
        return []
    if stripped.startswith("["):
        parsed = json.loads(stripped)
        if not isinstance(parsed, list):
            raise InputError("--icons JSON must be a list")
        return [str(item).strip() for item in parsed if str(item).strip()]
    return _csv(stripped)


def _default_user_config() -> str:
    return """image_generation:
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
"""


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
