"""Minimal image-processing primitives used by Phase 00."""

from __future__ import annotations

from collections.abc import Iterable
from io import BytesIO
from pathlib import Path
from xml.etree import ElementTree

from PIL import Image, ImageDraw, ImageFont

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
    """Rasterize an SVG, using cairosvg when available and a basic rect fallback."""

    try:
        import cairosvg
    except ImportError as exc:
        return _rasterize_basic_svg(path, size, exc)

    png_bytes = cairosvg.svg2png(url=str(path), output_width=size[0], output_height=size[1])
    if not isinstance(png_bytes, bytes):
        raise InputError(f"Could not rasterize SVG: {path}")
    with Image.open(BytesIO(png_bytes)) as image:
        return ensure_alpha(image)


def compare_perceptual_similarity(
    a: Image.Image | str | Path,
    b: Image.Image | str | Path,
    *,
    size: int = 64,
) -> float:
    """Return a lightweight 0..1 visual similarity score."""

    first = load_image(a) if isinstance(a, str | Path) else a.copy()
    second = load_image(b) if isinstance(b, str | Path) else b.copy()
    first = composite_on_bg(first, bg_color="#FFFFFF").resize(
        (size, size),
        Image.Resampling.LANCZOS,
    )
    second = composite_on_bg(second, bg_color="#FFFFFF").resize(
        (size, size),
        Image.Resampling.LANCZOS,
    )

    total_delta = 0
    channels = 3
    for left, right in zip(
        _pixel_data(first.convert("RGB")),
        _pixel_data(second.convert("RGB")),
        strict=True,
    ):
        total_delta += sum(abs(left[index] - right[index]) for index in range(channels))
    max_delta = size * size * channels * 255
    return round(max(0.0, 1.0 - (total_delta / max_delta)), 4)


def _rasterize_basic_svg(
    path: str | Path,
    size: tuple[int, int],
    original_error: Exception,
) -> Image.Image:
    """Rasterize the simple rect-based SVGs emitted by png-to-svg's fallback tracer."""

    try:
        root = ElementTree.parse(path).getroot()
    except ElementTree.ParseError as exc:
        raise InputError(
            "SVG rasterization requires cairosvg for non-basic SVG files."
        ) from exc

    namespace = "{http://www.w3.org/2000/svg}"
    viewbox = root.attrib.get("viewBox", f"0 0 {size[0]} {size[1]}").split()
    if len(viewbox) != 4:
        raise InputError("SVG has unsupported viewBox")
    _, _, view_w, view_h = [float(value) for value in viewbox]
    scale_x = size[0] / view_w
    scale_y = size[1] / view_h
    output = Image.new("RGBA", size, (0, 0, 0, 0))

    for rect in root.iter(f"{namespace}rect"):
        fill = rect.attrib.get("fill", "#000000")
        if fill == "none":
            continue
        x = int(round(float(rect.attrib.get("x", 0)) * scale_x))
        y = int(round(float(rect.attrib.get("y", 0)) * scale_y))
        width = max(1, int(round(float(rect.attrib.get("width", 0)) * scale_x)))
        height = max(1, int(round(float(rect.attrib.get("height", 0)) * scale_y)))
        alpha = int(round(float(rect.attrib.get("fill-opacity", "1")) * 255))
        red, green, blue, _ = parse_hex_color(fill)
        patch = Image.new("RGBA", (width, height), (red, green, blue, alpha))
        output.alpha_composite(patch, (x, y))

    return output


def _pixel_data(image: Image.Image):
    if hasattr(image, "get_flattened_data"):
        return image.get_flattened_data()
    return image.getdata()


def compose_grid(
    images: Iterable[Image.Image],
    *,
    columns: int = 3,
    cell_size: int = 256,
    labels: Iterable[str] | None = None,
) -> Image.Image:
    """Compose a simple transparent preview grid."""

    image_list = list(images)
    if not image_list:
        raise InputError("Cannot compose a grid with no images")

    label_list = list(labels or [])
    label_height = 28 if label_list else 0
    rows = (len(image_list) + columns - 1) // columns
    canvas = Image.new(
        "RGBA",
        (columns * cell_size, rows * (cell_size + label_height)),
        (0, 0, 0, 0),
    )
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default()
    for index, image in enumerate(image_list):
        thumb = pad_square(ensure_alpha(image))
        thumb.thumbnail((cell_size, cell_size), Image.Resampling.LANCZOS)
        x = (index % columns) * cell_size + (cell_size - thumb.width) // 2
        row_top = (index // columns) * (cell_size + label_height)
        y = row_top + (cell_size - thumb.height) // 2
        canvas.alpha_composite(thumb, (x, y))
        if index < len(label_list):
            text = label_list[index]
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_x = (index % columns) * cell_size + max(0, (cell_size - text_width) // 2)
            draw.text((text_x, row_top + cell_size + 6), text, fill=(20, 20, 20, 255), font=font)
    return canvas


def _axis_offset(length: int, target: int, anchor: str) -> int:
    if anchor in {"left", "top"}:
        return 0
    if anchor in {"right", "bottom"}:
        return length - target
    return (length - target) // 2
