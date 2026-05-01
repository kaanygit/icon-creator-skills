"""app-icon-pack CLI."""

from __future__ import annotations

import argparse
import shutil
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from xml.etree import ElementTree

from PIL import Image

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR.parent.parent.parent) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR.parent.parent.parent))
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import android  # noqa: E402
import ios  # noqa: E402
import macos  # noqa: E402
import watchos  # noqa: E402
import web  # noqa: E402
import windows  # noqa: E402
from common import PackContext, load_master  # noqa: E402

from shared.errors import InputError  # noqa: E402

DEFAULT_PLATFORMS = ["ios", "android", "web"]
ALL_PLATFORMS = ["ios", "android", "web", "macos", "watchos", "windows"]
WRITERS = {
    "ios": ios.write,
    "android": android.write,
    "web": web.write,
    "macos": macos.write,
    "watchos": watchos.write,
    "windows": windows.write,
}


@dataclass(frozen=True)
class PackRun:
    run_dir: Path
    zip_path: Path | None
    platforms: list[str]


def pack_icons(
    *,
    master: str | Path,
    app_name: str = "MyApp",
    platforms: list[str] | None = None,
    output_dir: str | Path = "output",
    bg_color: str = "#FFFFFF",
    create_zip: bool = True,
    validate: bool = True,
    timestamp: datetime | None = None,
) -> PackRun:
    selected = platforms or DEFAULT_PLATFORMS
    unknown = sorted(set(selected) - set(ALL_PLATFORMS))
    if unknown:
        raise InputError(f"Unknown platform(s): {', '.join(unknown)}")

    timestamp = timestamp or datetime.now(UTC)
    run_dir = Path(output_dir) / f"{slugify(app_name)}-icons-{timestamp.strftime('%Y%m%d-%H%M%S')}"
    run_dir.mkdir(parents=True, exist_ok=True)

    ctx = PackContext(
        master=load_master(master),
        master_path=Path(master),
        out_dir=run_dir,
        app_name=app_name,
        bg_color=bg_color,
    )
    for platform in selected:
        WRITERS[platform](ctx)

    _write_readme(ctx, selected)
    if validate:
        validate_pack(run_dir, selected)

    zip_path = None
    if create_zip:
        zip_path = Path(shutil.make_archive(str(run_dir), "zip", run_dir))
    return PackRun(run_dir=run_dir, zip_path=zip_path, platforms=selected)


def validate_pack(run_dir: Path, platforms: list[str]) -> None:
    for platform in platforms:
        if platform in {"ios", "macos", "watchos"}:
            contents = run_dir / platform / "AppIcon.appiconset" / "Contents.json"
            _assert_json(contents)
        if platform == "web":
            _assert_json(run_dir / "web" / "manifest.json")
            ElementTree.parse(run_dir / "web" / "browserconfig.xml")
            with Image.open(run_dir / "web" / "favicon.ico") as image:
                if image.size not in {(16, 16), (32, 32), (48, 48)}:
                    raise InputError("favicon.ico did not decode to an expected size")
        if platform == "android":
            ElementTree.parse(run_dir / "android" / "mipmap-anydpi-v26" / "ic_launcher.xml")
        if platform == "windows":
            ElementTree.parse(run_dir / "windows" / "manifest-snippet.xml")


def slugify(value: str) -> str:
    import re

    return re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-") or "app"


def parse_platforms(value: str | None) -> list[str]:
    if not value:
        return DEFAULT_PLATFORMS
    if value == "all":
        return ALL_PLATFORMS
    return [item.strip() for item in value.split(",") if item.strip()]


def _assert_json(path: Path) -> None:
    import json

    json.loads(path.read_text(encoding="utf-8"))


def _write_readme(ctx: PackContext, platforms: list[str]) -> None:
    sections = [
        f"# {ctx.app_name} icon asset pack",
        "",
        f"Master: `{ctx.master_path}`",
        f"Platforms: `{', '.join(platforms)}`",
        "",
    ]
    if "ios" in platforms:
        sections += [
            "## iOS",
            "Drag `ios/AppIcon.appiconset/` into `Assets.xcassets` and select it as "
            "the app icon source.",
            "",
        ]
    if "android" in platforms:
        sections += [
            "## Android",
            "Copy the contents of `android/` into `app/src/main/res/`.",
            "",
        ]
    if "web" in platforms:
        sections += [
            "## Web",
            "Copy `web/` to your site root and add favicon/manifest links from "
            "`web/manifest.json` as needed.",
            "",
        ]
    if "macos" in platforms:
        sections += [
            "## macOS",
            "Drag `macos/AppIcon.appiconset/` into the Mac app asset catalog.",
            "",
        ]
    if "watchos" in platforms:
        sections += [
            "## watchOS",
            "Drag `watchos/AppIcon.appiconset/` into the Watch app asset catalog.",
            "",
        ]
    if "windows" in platforms:
        sections += [
            "## Windows",
            "Copy `windows/*.png` into `Assets/` and merge `windows/manifest-snippet.xml`.",
            "",
        ]
    if ctx.warnings:
        sections += ["## Warnings", *[f"- {warning}" for warning in ctx.warnings], ""]
    (ctx.out_dir / "README.md").write_text("\n".join(sections), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create platform app icon asset packs.")
    parser.add_argument("--master", required=True, help="Source master PNG or SVG")
    parser.add_argument("--app-name", default="MyApp", help="App name for manifests and output")
    parser.add_argument(
        "--platforms",
        default=",".join(DEFAULT_PLATFORMS),
        help="Comma list or all",
    )
    parser.add_argument("--output-dir", default="output", help="Output root")
    parser.add_argument("--bg-color", default="#FFFFFF", help="Opaque asset background color")
    parser.add_argument("--no-zip", action="store_true", help="Skip zip output")
    parser.add_argument("--no-validate", action="store_true", help="Skip generated-file validation")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    run = pack_icons(
        master=args.master,
        app_name=args.app_name,
        platforms=parse_platforms(args.platforms),
        output_dir=args.output_dir,
        bg_color=args.bg_color,
        create_zip=not args.no_zip,
        validate=not args.no_validate,
    )
    print(run.run_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
