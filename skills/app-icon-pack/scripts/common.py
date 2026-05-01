"""Shared helpers for app-icon-pack platform writers."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from PIL import Image, ImageChops, ImageStat

from shared.errors import InputError
from shared.image_utils import (
    composite_on_bg,
    crop_square,
    ensure_alpha,
    load_image,
    parse_hex_color,
    rasterize_svg,
    save_png,
)


@dataclass
class PackContext:
    master: Image.Image
    master_path: Path
    out_dir: Path
    app_name: str
    bg_color: str
    warnings: list[str] = field(default_factory=list)


def load_master(path: str | Path) -> Image.Image:
    resolved = Path(path)
    if not resolved.exists():
        raise InputError(f"Master image not found: {resolved}")
    if resolved.suffix.lower() == ".svg":
        return rasterize_svg(resolved, (1024, 1024))

    image = ensure_alpha(load_image(resolved))
    if image.width != image.height:
        image = crop_square(image)
    if min(image.size) < 1024:
        raise InputError("Master PNG must be at least 1024x1024 for app icon packaging")
    return image


def resize_icon(image: Image.Image, size: int | tuple[int, int]) -> Image.Image:
    target = (size, size) if isinstance(size, int) else size
    return ensure_alpha(image).resize(target, Image.Resampling.LANCZOS)


def save_resized(
    image: Image.Image,
    path: Path,
    size: int | tuple[int, int],
    *,
    opaque: bool = False,
    bg_color: str = "#FFFFFF",
) -> Path:
    resized = resize_icon(image, size)
    if opaque:
        resized = composite_on_bg(resized, bg_color=bg_color)
    return save_png(resized, path)


def write_json(path: Path, data: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return path


def contents_json(images: list[dict[str, Any]]) -> dict[str, Any]:
    return {"images": images, "info": {"version": 1, "author": "icon-creator-skills"}}


def has_edge_content(image: Image.Image, *, edge_ratio: float = 0.10) -> bool:
    alpha = ensure_alpha(image).getchannel("A")
    width, height = image.size
    inset_x = max(1, int(width * edge_ratio))
    inset_y = max(1, int(height * edge_ratio))
    center = Image.new("L", image.size, 0)
    center.paste(255, (inset_x, inset_y, width - inset_x, height - inset_y))
    edge = ImageChops.multiply(alpha, ImageChops.invert(center))
    return edge.getbbox() is not None


def alpha_bbox(image: Image.Image) -> tuple[int, int, int, int] | None:
    alpha = ensure_alpha(image).getchannel("A")
    if alpha.getextrema()[0] < 255:
        return alpha.point(lambda value: 255 if value > 16 else 0).getbbox()

    background = Image.new("RGBA", image.size, image.getpixel((0, 0)))
    diff = ImageChops.difference(image, background).convert("L")
    return diff.point(lambda value: 255 if value > 12 else 0).getbbox()


def centered_foreground(image: Image.Image, *, canvas: int, content_max: int) -> Image.Image:
    source = ensure_alpha(image)
    bbox = alpha_bbox(source)
    subject = source.crop(bbox) if bbox else source
    subject.thumbnail((content_max, content_max), Image.Resampling.LANCZOS)
    canvas_image = Image.new("RGBA", (canvas, canvas), (0, 0, 0, 0))
    canvas_image.alpha_composite(
        subject,
        ((canvas - subject.width) // 2, (canvas - subject.height) // 2),
    )
    return canvas_image


def solid_image(size: int | tuple[int, int], color: str) -> Image.Image:
    target = (size, size) if isinstance(size, int) else size
    return Image.new("RGBA", target, parse_hex_color(color))


def white_silhouette(image: Image.Image, size: int = 24) -> Image.Image:
    gray = composite_on_bg(image, bg_color="#000000").convert("L")
    alpha_source = (
        ensure_alpha(image).getchannel("A").resize((size, size), Image.Resampling.LANCZOS)
    )
    small = gray.resize((size, size), Image.Resampling.LANCZOS)
    threshold = ImageStat.Stat(small).mean[0]
    output = Image.new("RGBA", (size, size), (255, 255, 255, 0))
    for y in range(size):
        for x in range(size):
            alpha = alpha_source.getpixel((x, y))
            if alpha > 16 and small.getpixel((x, y)) >= threshold:
                output.putpixel((x, y), (255, 255, 255, alpha))
    return output
