"""Reference-image analysis used by early icon generation phases."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

from PIL import Image, ImageFilter, ImageStat

from shared.errors import IconSkillsError, InputError
from shared.image_utils import ensure_alpha, load_image


class VisionAnalyzerError(IconSkillsError):
    """Reference image analysis failed."""

    def __init__(self, message: str, *, code: str = "unknown") -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class Color:
    hex: str
    weight: float


@dataclass(frozen=True)
class StyleHints:
    palette: list[Color]
    gradient_prevalence: float
    edge_density: float
    stroke_weight_estimate: str
    art_style: str
    descriptor: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class VisionAnalyzer:
    """Small deterministic analyzer for Phase 02 reference images."""

    def extract_palette(self, image_path: str | Path, *, n_colors: int = 5) -> list[Color]:
        image = ensure_alpha(load_image(image_path))
        if image.width < 4 or image.height < 4:
            raise VisionAnalyzerError("Reference image is too small", code="image-too-small")

        rgb = _flatten_transparency(image).resize((128, 128), Image.Resampling.LANCZOS)
        quantized = rgb.quantize(colors=n_colors, method=Image.Quantize.MEDIANCUT)
        palette = quantized.getpalette() or []
        counts = quantized.getcolors(maxcolors=128 * 128) or []
        total = sum(count for count, _ in counts) or 1

        colors: list[Color] = []
        for count, index in sorted(counts, reverse=True):
            offset = index * 3
            r, g, b = palette[offset : offset + 3]
            colors.append(Color(hex=f"#{r:02X}{g:02X}{b:02X}", weight=round(count / total, 4)))
        return colors[:n_colors]

    def analyze_style(self, image_path: str | Path) -> StyleHints:
        path = Path(image_path)
        if not path.exists():
            raise InputError(f"Reference image not found: {path}")

        image = ensure_alpha(load_image(path))
        palette = self.extract_palette(path)
        edge_density = _edge_density(image)
        gradient_prevalence = _gradient_prevalence(image)
        stroke_weight = _stroke_weight(edge_density)
        art_style = _classify_style(edge_density, gradient_prevalence)
        palette_text = ", ".join(color.hex for color in palette[:3])
        descriptor = (
            f"{art_style} reference with dominant colors {palette_text}, "
            f"{stroke_weight} stroke weight, edge density {edge_density:.2f}, "
            f"gradient prevalence {gradient_prevalence:.2f}"
        )
        return StyleHints(
            palette=palette,
            gradient_prevalence=edge_density if False else gradient_prevalence,
            edge_density=edge_density,
            stroke_weight_estimate=stroke_weight,
            art_style=art_style,
            descriptor=descriptor,
        )


def _flatten_transparency(image: Image.Image) -> Image.Image:
    rgba = ensure_alpha(image)
    background = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
    background.alpha_composite(rgba)
    return background.convert("RGB")


def _edge_density(image: Image.Image) -> float:
    gray = _flatten_transparency(image).convert("L").resize((128, 128), Image.Resampling.LANCZOS)
    edges = gray.filter(ImageFilter.FIND_EDGES)
    stat = ImageStat.Stat(edges)
    return round(min(1.0, (stat.mean[0] or 0) / 80), 4)


def _gradient_prevalence(image: Image.Image) -> float:
    small = _flatten_transparency(image).resize((64, 64), Image.Resampling.LANCZOS).convert("L")
    blurred = small.filter(ImageFilter.GaussianBlur(radius=3))
    diff = ImageStat.Stat(Image.blend(small, blurred, 0.5).filter(ImageFilter.FIND_EDGES))
    return round(min(1.0, (diff.mean[0] or 0) / 64), 4)


def _stroke_weight(edge_density: float) -> str:
    if edge_density < 0.12:
        return "none"
    if edge_density < 0.32:
        return "thin"
    if edge_density < 0.58:
        return "regular"
    return "bold"


def _classify_style(edge_density: float, gradient_prevalence: float) -> str:
    if edge_density > 0.5:
        return "outline"
    if gradient_prevalence > 0.35:
        return "gradient"
    return "flat-vector"

