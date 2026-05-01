"""Minimal image-processing primitives used by Phase 00."""

from __future__ import annotations

from collections.abc import Iterable
from io import BytesIO
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


def parse_hex_color(value: str) -> RGBA:
    """Parse #RGB or #RRGGBB into an opaque RGBA tuple."""

    raw = value.strip().lstrip("#")
    if len(raw) == 3:
        raw = "".join(character * 2 for character in raw)
    if len(raw) != 6:
        raise InputError(f"Expected hex color like #FFFFFF, got: {value}")
    try:
        red = int(raw[0:2], 16)
        green = int(raw[2:4], 16)
        blue = int(raw[4:6], 16)
    except ValueError as exc:
        raise InputError(f"Invalid hex color: {value}") from exc
    return red, green, blue, 255


def composite_on_bg(
    image_or_path: Image.Image | str | Path,
    *,
    bg_color: str = "#FFFFFF",
    size: tuple[int, int] | None = None,
) -> Image.Image:
    """Composite an image onto a solid opaque background."""

    image = (
        load_image(image_or_path)
        if isinstance(image_or_path, str | Path)
        else image_or_path.copy()
    )
    rgba = ensure_alpha(image)
    if size and rgba.size != size:
        rgba = rgba.resize(size, Image.Resampling.LANCZOS)

    background = Image.new("RGBA", rgba.size, parse_hex_color(bg_color))
    background.alpha_composite(rgba)
    return background


def write_ico_multires(
    path: str | Path,
    entries: Iterable[tuple[int, Image.Image]],
) -> Path:
    """Write a multi-resolution ICO using Pillow."""

    normalized: list[Image.Image] = []
    for size, image in sorted(entries, key=lambda item: item[0]):
        if image.width != image.height:
            raise InputError("ICO entries must be square")
        normalized.append(ensure_alpha(image).resize((size, size), Image.Resampling.LANCZOS))

    if not normalized:
        raise InputError("Cannot write ICO with no entries")

    resolved = Path(path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    sizes = [(image.width, image.height) for image in normalized]
    normalized[-1].save(resolved, format="ICO", sizes=sizes, append_images=normalized[:-1])
    return resolved


def rasterize_svg(path: str | Path, size: tuple[int, int]) -> Image.Image:
    """Rasterize an SVG when cairosvg is installed."""

    try:
        import cairosvg
    except ImportError as exc:
        raise InputError(
            "SVG input requires cairosvg. Install it or use a PNG master for app-icon-pack."
        ) from exc

    png_bytes = cairosvg.svg2png(url=str(path), output_width=size[0], output_height=size[1])
    if not isinstance(png_bytes, bytes):
        raise InputError(f"Could not rasterize SVG: {path}")
    with Image.open(BytesIO(png_bytes)) as image:
        return ensure_alpha(image)


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
