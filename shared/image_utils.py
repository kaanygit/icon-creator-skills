"""Minimal image-processing primitives used by Phase 00."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from PIL import Image

from shared.errors import InputError

RGBA = tuple[int, int, int, int]


def load_image(path: str | Path) -> Image.Image:
    """Load an image and detach it from the underlying file handle."""

    resolved = Path(path)
    if not resolved.exists():
        raise InputError(f"Image file not found: {resolved}")
    with Image.open(resolved) as image:
        return image.copy()


def save_image(image: Image.Image, path: str | Path, *, format: str | None = None) -> Path:
    """Save an image, creating parent directories as needed."""

    resolved = Path(path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    image.save(resolved, format=format)
    return resolved


def ensure_alpha(image: Image.Image) -> Image.Image:
    """Return an RGBA image."""

    if image.mode == "RGBA":
        return image.copy()
    return image.convert("RGBA")


def detect_alpha(image: Image.Image) -> bool:
    """Return true when the image has at least one transparent pixel."""

    if image.mode not in {"RGBA", "LA"} and "transparency" not in image.info:
        return False

    alpha = ensure_alpha(image).getchannel("A")
    extrema = alpha.getextrema()
    return extrema[0] < 255


def resize(image_or_path: Image.Image | str | Path, size: tuple[int, int]) -> Image.Image:
    """Resize using high-quality Lanczos resampling."""

    image = load_image(image_or_path) if isinstance(image_or_path, str | Path) else image_or_path
    return image.resize(size, Image.Resampling.LANCZOS)


def crop_square(image: Image.Image, *, anchor: str = "center") -> Image.Image:
    """Crop an image to a square."""

    width, height = image.size
    side = min(width, height)
    if width == height:
        return image.copy()

    if width > height:
        left = _axis_offset(width, side, anchor)
        box = (left, 0, left + side, side)
    else:
        top = _axis_offset(height, side, anchor)
        box = (0, top, side, top + side)
    return image.crop(box)


def pad_square(image: Image.Image, *, fill: RGBA = (0, 0, 0, 0)) -> Image.Image:
    """Pad an image to a square canvas."""

    width, height = image.size
    side = max(width, height)
    output = Image.new("RGBA", (side, side), fill)
    output.alpha_composite(ensure_alpha(image), ((side - width) // 2, (side - height) // 2))
    return output


def save_png(image: Image.Image, path: str | Path) -> Path:
    """Save an image as PNG."""

    return save_image(ensure_alpha(image), path, format="PNG")


def compose_grid(
    images: Iterable[Image.Image],
    *,
    columns: int = 3,
    cell_size: int = 256,
) -> Image.Image:
    """Compose a simple transparent preview grid."""

    image_list = list(images)
    if not image_list:
        raise InputError("Cannot compose a grid with no images")

    rows = (len(image_list) + columns - 1) // columns
    canvas = Image.new("RGBA", (columns * cell_size, rows * cell_size), (0, 0, 0, 0))
    for index, image in enumerate(image_list):
        thumb = pad_square(ensure_alpha(image))
        thumb.thumbnail((cell_size, cell_size), Image.Resampling.LANCZOS)
        x = (index % columns) * cell_size + (cell_size - thumb.width) // 2
        y = (index // columns) * cell_size + (cell_size - thumb.height) // 2
        canvas.alpha_composite(thumb, (x, y))
    return canvas


def _axis_offset(length: int, target: int, anchor: str) -> int:
    if anchor in {"left", "top"}:
        return 0
    if anchor in {"right", "bottom"}:
        return length - target
    return (length - target) // 2
