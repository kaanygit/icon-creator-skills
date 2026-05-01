"""Shared helpers for mascot-pack writers."""

from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from PIL import Image, ImageChops, ImageFilter

from shared.errors import InputError
from shared.image_utils import ensure_alpha, load_image, parse_hex_color, save_png

PRESET_PATH = Path(__file__).parents[3] / "shared" / "presets" / "platforms" / "social-print.yaml"


@dataclass
class MascotPackContext:
    master: Image.Image
    master_path: Path
    variants_dir: Path | None
    out_dir: Path
    mascot_name: str
    bg_color: str
    warnings: list[str] = field(default_factory=list)


def load_sizes() -> dict[str, Any]:
    with PRESET_PATH.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def load_master(path: str | Path) -> Image.Image:
    resolved = Path(path)
    if not resolved.exists():
        raise InputError(f"Master image not found: {resolved}")
    image = ensure_alpha(load_image(resolved))
    if min(image.size) < 128:
        raise InputError("Master image must be at least 128px on its smallest side")
    return image


def fit_on_canvas(
    image: Image.Image,
    size: tuple[int, int],
    *,
    bg_color: str | None = None,
    max_ratio: float = 0.78,
) -> Image.Image:
    fill = (0, 0, 0, 0) if bg_color is None else parse_hex_color(bg_color)
    canvas = Image.new("RGBA", size, fill)
    subject = trim_alpha(image)
    limit = (max(1, int(size[0] * max_ratio)), max(1, int(size[1] * max_ratio)))
    subject.thumbnail(limit, Image.Resampling.LANCZOS)
    canvas.alpha_composite(
        subject,
        ((size[0] - subject.width) // 2, (size[1] - subject.height) // 2),
    )
    return canvas


def trim_alpha(image: Image.Image) -> Image.Image:
    rgba = ensure_alpha(image)
    bbox = rgba.getchannel("A").point(lambda value: 255 if value > 8 else 0).getbbox()
    return rgba.crop(bbox) if bbox else rgba


def save_fit(
    image: Image.Image,
    path: Path,
    size: tuple[int, int],
    *,
    bg_color: str | None = None,
    max_ratio: float = 0.78,
) -> Path:
    return save_png(fit_on_canvas(image, size, bg_color=bg_color, max_ratio=max_ratio), path)


def add_white_outline(image: Image.Image, *, width: int = 8) -> Image.Image:
    rgba = ensure_alpha(image)
    alpha = rgba.getchannel("A")
    outline = alpha.filter(ImageFilter.MaxFilter(width * 2 + 1))
    stroke_alpha = ImageChops.subtract(outline, alpha)
    stroke = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
    output = Image.new("RGBA", rgba.size, (0, 0, 0, 0))
    output.alpha_composite(Image.merge("RGBA", (*stroke.split()[:3], stroke_alpha)))
    output.alpha_composite(rgba)
    return output


def discover_variants(variants_dir: str | Path | None) -> dict[str, list[Path]]:
    if not variants_dir:
        return {"poses": [], "expressions": []}
    root = Path(variants_dir)
    if not root.exists():
        raise InputError(f"Variants directory not found: {root}")
    return {
        "poses": sorted((root / "poses").glob("*.png")) if (root / "poses").exists() else [],
        "expressions": sorted((root / "expressions").glob("*.png"))
        if (root / "expressions").exists()
        else [],
    }


def write_zip(run_dir: Path) -> Path:
    return Path(shutil.make_archive(str(run_dir), "zip", run_dir))


def save_webp(image: Image.Image, path: Path, *, quality: int = 86) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    ensure_alpha(image).save(path, format="WEBP", quality=quality, method=6)
    return path
