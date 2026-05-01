"""mascot-pack CLI."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from PIL import Image

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR.parent.parent.parent) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR.parent.parent.parent))
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
for module_name in ("common", "social", "stickers", "web", "print"):
    if module_name in sys.modules:
        existing = Path(getattr(sys.modules[module_name], "__file__", "")).resolve()
        if existing != (SCRIPT_DIR / f"{module_name}.py").resolve():
            del sys.modules[module_name]

import importlib  # noqa: E402

import social  # noqa: E402
import stickers  # noqa: E402
import web  # noqa: E402
from common import (  # noqa: E402
    MascotPackContext,
    discover_variants,
    fit_on_canvas,
    load_master,
    save_fit,
    write_zip,
)

from shared.errors import InputError  # noqa: E402
from shared.image_utils import compose_grid, save_png  # noqa: E402

print_targets = importlib.import_module("print")

DEFAULT_TARGETS = ["social", "stickers", "print", "web"]
ALL_TARGETS = set(DEFAULT_TARGETS)


@dataclass(frozen=True)
class MascotPackRun:
    run_dir: Path
    zip_path: Path | None
    targets: list[str]


def pack_mascot(
    *,
    master: str | Path,
    variants_dir: str | Path | None = None,
    targets: list[str] | None = None,
    mascot_name: str | None = None,
    output_dir: str | Path = "output",
    bg_color: str = "#FFFFFF",
    bg_variants: bool = True,
    webp: bool = True,
    create_zip: bool = True,
    timestamp: datetime | None = None,
) -> MascotPackRun:
    selected = targets or DEFAULT_TARGETS
    unknown = sorted(set(selected) - ALL_TARGETS)
    if unknown:
        raise InputError(f"Unknown target(s): {', '.join(unknown)}")

    timestamp = timestamp or datetime.now(UTC)
    name = mascot_name or Path(master).stem
    run_dir = Path(output_dir) / f"{slugify(name)}-pack-{timestamp.strftime('%Y%m%d-%H%M%S')}"
    run_dir.mkdir(parents=True, exist_ok=True)
    ctx = MascotPackContext(
        master=load_master(master),
        master_path=Path(master),
        variants_dir=Path(variants_dir) if variants_dir else None,
        out_dir=run_dir,
        mascot_name=name,
        bg_color=bg_color,
    )

    _write_master_variants(ctx, bg_variants=bg_variants)
    if "social" in selected:
        social.write(ctx)
    if "stickers" in selected:
        stickers.write(ctx)
    if "print" in selected:
        print_targets.write(ctx)
    if "web" in selected:
        web.write(ctx, webp=webp)

    _write_variant_grids(ctx)
    _write_readme(ctx, selected, webp=webp)
    _write_metadata(ctx, selected, bg_variants=bg_variants, webp=webp)
    zip_path = write_zip(run_dir) if create_zip else None
    return MascotPackRun(run_dir=run_dir, zip_path=zip_path, targets=selected)


def _write_master_variants(ctx: MascotPackContext, *, bg_variants: bool) -> None:
    out = ctx.out_dir / "master"
    save_fit(ctx.master, out / "master.png", (1024, 1024), max_ratio=0.9)
    if bg_variants:
        save_png(
            fit_on_canvas(ctx.master, (1024, 1024), bg_color="#FFFFFF"),
            out / "master-white-bg.png",
        )
        save_png(
            fit_on_canvas(ctx.master, (1024, 1024), bg_color="#111827"),
            out / "master-dark-bg.png",
        )


def _write_variant_grids(ctx: MascotPackContext) -> None:
    variants = discover_variants(ctx.variants_dir)
    for kind, paths in variants.items():
        if not paths:
            continue
        images = [Image.open(path).convert("RGBA") for path in paths]
        grid = compose_grid(
            images,
            columns=min(4, len(images)),
            cell_size=260,
            labels=[p.stem for p in paths],
        )
        save_png(grid, ctx.out_dir / f"{kind}-grid.png")


def _write_readme(ctx: MascotPackContext, targets: list[str], *, webp: bool) -> None:
    lines = [
        f"# {ctx.mascot_name} mascot deliverable pack",
        "",
        f"Master: `{ctx.master_path}`",
        f"Targets: `{', '.join(targets)}`",
        "",
        "## Master",
        "",
        "`master/` contains transparent, white-background, and dark-background variants.",
        "",
    ]
    if "social" in targets:
        lines.extend(["## Social", "", "`social/` contains upload-ready post and story sizes.", ""])
    if "stickers" in targets:
        lines.extend(
            [
                "## Stickers",
                "",
                "`stickers/` contains iMessage, Telegram, WhatsApp, Discord, and Slack exports.",
                "",
            ]
        )
    if "print" in targets:
        lines.extend(
            ["## Print", "", "`print/` contains 300dpi PNGs and an approximate CMYK preview.", ""]
        )
    if "web" in targets:
        suffix = " WebP duplicates are in `web/webp/`." if webp else ""
        lines.extend(
            ["## Web", "", f"`web/` contains responsive hero and avatar assets.{suffix}", ""]
        )
    if ctx.warnings:
        lines.extend(["## Warnings", "", *[f"- {warning}" for warning in ctx.warnings], ""])
    (ctx.out_dir / "README.md").write_text("\n".join(lines), encoding="utf-8")


def _write_metadata(
    ctx: MascotPackContext,
    targets: list[str],
    *,
    bg_variants: bool,
    webp: bool,
) -> None:
    data = {
        "skill": "mascot-pack",
        "version": "1.0.0",
        "mascot_name": ctx.mascot_name,
        "master": str(ctx.master_path),
        "variants_dir": str(ctx.variants_dir) if ctx.variants_dir else None,
        "targets": targets,
        "bg_variants": bg_variants,
        "webp": webp,
        "warnings": ctx.warnings,
    }
    (ctx.out_dir / "metadata.json").write_text(json.dumps(data, indent=2), encoding="utf-8")


def parse_targets(value: str | None) -> list[str]:
    if not value or value == "all":
        return DEFAULT_TARGETS
    return [item.strip() for item in value.split(",") if item.strip()]


def slugify(value: str) -> str:
    import re

    return re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-") or "mascot"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Package mascot deliverables.")
    parser.add_argument("--master", required=True, help="Mascot master PNG")
    parser.add_argument("--variants-dir", default=None, help="Mascot run directory")
    parser.add_argument("--targets", default="all", help="Comma list or all")
    parser.add_argument("--mascot-name", default=None, help="Output name")
    parser.add_argument("--output-dir", default="output", help="Output root")
    parser.add_argument("--bg-color", default="#FFFFFF", help="Background color")
    parser.add_argument("--no-bg-variants", action="store_true")
    parser.add_argument("--no-webp", action="store_true")
    parser.add_argument("--no-zip", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    run = pack_mascot(
        master=args.master,
        variants_dir=args.variants_dir,
        targets=parse_targets(args.targets),
        mascot_name=args.mascot_name,
        output_dir=args.output_dir,
        bg_color=args.bg_color,
        bg_variants=not args.no_bg_variants,
        webp=not args.no_webp,
        create_zip=not args.no_zip,
    )
    print(run.run_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
