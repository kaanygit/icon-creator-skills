"""png-to-svg CLI."""

from __future__ import annotations

import argparse
import json
import math
import shutil
import sys
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from PIL import Image, ImageChops, ImageFilter, ImageStat

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from shared.errors import InputError  # noqa: E402
from shared.image_utils import (  # noqa: E402
    compare_perceptual_similarity,
    composite_on_bg,
    ensure_alpha,
    load_image,
    rasterize_svg,
    save_png,
)

Algorithm = Literal["auto", "vtracer", "potrace", "imagetracer"]


@dataclass(frozen=True)
class Suitability:
    classification: Literal["good", "marginal", "poor"]
    color_count_estimate: int
    edge_density_estimate: float
    gradient_prevalence: float
    transparency: bool
    reason: str


@dataclass(frozen=True)
class VectorizeRun:
    run_dir: Path
    svg_path: Path
    comparison_path: Path | None
    stats_path: Path


def vectorize(
    *,
    input_path: str | Path,
    output_dir: str | Path = "output",
    output_path: str | Path | None = None,
    algorithm: Algorithm = "auto",
    color_count: int | None = None,
    simplify: int = 50,
    optimize: bool = True,
    comparison: bool = True,
    force: bool = False,
    timestamp: datetime | None = None,
) -> VectorizeRun:
    source_path = Path(input_path)
    if not source_path.exists():
        raise InputError(f"Input image not found: {source_path}")
    if algorithm not in {"auto", "vtracer", "potrace", "imagetracer"}:
        raise InputError(f"Unknown algorithm: {algorithm}")
    if simplify < 0 or simplify > 100:
        raise InputError("--simplify must be between 0 and 100")

    original = ensure_alpha(load_image(source_path))
    suitability = analyze_suitability(original)
    if suitability.classification == "poor" and not force:
        raise InputError(
            f"Input suitability is poor: {suitability.reason}. Use --force to proceed."
        )

    chosen = choose_algorithm(suitability, algorithm)
    colors = color_count or _default_color_count(chosen, suitability)
    timestamp = timestamp or datetime.now(UTC)
    run_id = f"{slugify(source_path.stem)}-svg-{timestamp.strftime('%Y%m%d-%H%M%S')}"
    run_dir = Path(output_dir) / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    svg_path = Path(output_path) if output_path else run_dir / f"{source_path.stem}.svg"
    svg_path.parent.mkdir(parents=True, exist_ok=True)
    traced, path_count = trace_image(
        original,
        algorithm=chosen,
        color_count=colors,
        simplify=simplify,
    )
    svg_text = optimize_svg(traced) if optimize else traced
    svg_path.write_text(svg_text, encoding="utf-8")

    rendered = rasterize_svg(svg_path, original.size)
    similarity = compare_perceptual_similarity(original, rendered)
    comparison_path = None
    if comparison:
        comparison_path = run_dir / f"{source_path.stem}-comparison.png"
        save_png(_comparison_image(original, rendered), comparison_path)

    warnings = []
    if similarity < 0.85:
        warnings.append("Similarity below 0.85; inspect SVG before shipping.")
    if _external_algorithm_missing(chosen):
        warnings.append(f"{chosen} package/binary not installed; used Pillow fallback tracer.")
    if suitability.classification == "marginal":
        warnings.append(f"Suitability marginal: {suitability.reason}")

    stats = {
        "skill": "png-to-svg",
        "version": "0.2.0",
        "run_id": run_id,
        "input": {
            "path": str(source_path),
            "size_bytes": source_path.stat().st_size,
            "dimensions": list(original.size),
            **asdict(suitability),
        },
        "settings": {
            "algorithm": algorithm,
            "algorithm_used": chosen,
            "color-count": colors,
            "simplify": simplify,
            "optimize": optimize,
            "force": force,
        },
        "output": {
            "path": str(svg_path),
            "size_bytes": svg_path.stat().st_size,
            "size_ratio": round(svg_path.stat().st_size / max(1, source_path.stat().st_size), 4),
            "path_count": path_count,
            "render_similarity": similarity,
        },
        "warnings": warnings,
    }
    stats_path = run_dir / f"{source_path.stem}-stats.json"
    stats_path.write_text(json.dumps(stats, indent=2), encoding="utf-8")
    return VectorizeRun(run_dir, svg_path, comparison_path, stats_path)


def analyze_suitability(image: Image.Image) -> Suitability:
    rgba = ensure_alpha(image)
    colors = _estimate_color_count(rgba)
    edge_density = _edge_density(rgba)
    gradient = _gradient_prevalence(rgba)
    alpha = rgba.getchannel("A")
    transparency = alpha.getextrema()[0] < 255

    if colors > 220 or (edge_density > 0.34 and gradient > 0.50):
        return Suitability(
            "poor",
            colors,
            edge_density,
            gradient,
            transparency,
            "too many colors/edges for useful SVG output",
        )
    if colors > 32 or edge_density > 0.24 or gradient > 0.36:
        return Suitability(
            "marginal",
            colors,
            edge_density,
            gradient,
            transparency,
            "complex artwork may produce a large SVG",
        )
    return Suitability("good", colors, edge_density, gradient, transparency, "icon-like input")


def choose_algorithm(suitability: Suitability, requested: Algorithm) -> Literal[
    "vtracer",
    "potrace",
    "imagetracer",
]:
    if requested != "auto":
        return requested
    if suitability.color_count_estimate <= 2 and suitability.edge_density_estimate < 0.20:
        return "potrace"
    if suitability.color_count_estimate <= 16 and suitability.gradient_prevalence < 0.30:
        return "vtracer"
    return "imagetracer"


def trace_image(
    image: Image.Image,
    *,
    algorithm: Literal["vtracer", "potrace", "imagetracer"],
    color_count: int,
    simplify: int,
) -> tuple[str, int]:
    if algorithm == "potrace":
        return _trace_rects(_posterize_monochrome(image), simplify=simplify)
    return _trace_rects(_quantize(image, color_count), simplify=simplify)


def optimize_svg(svg: str) -> str:
    lines = [line.strip() for line in svg.splitlines() if line.strip()]
    return "\n".join(lines) + "\n"


def slugify(value: str) -> str:
    import re

    return re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-") or "image"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert PNG/JPG icon artwork to SVG.")
    parser.add_argument("--input", required=True, help="Input PNG/JPG path")
    parser.add_argument("--output-dir", default="output", help="Output root directory")
    parser.add_argument("--output-path", default=None, help="Explicit SVG output path")
    parser.add_argument(
        "--algorithm",
        default="auto",
        choices=["auto", "vtracer", "potrace", "imagetracer"],
    )
    parser.add_argument("--color-count", type=int, default=None, help="Quantized color count")
    parser.add_argument("--simplify", type=int, default=50, help="0-100 simplification level")
    parser.add_argument("--force", action="store_true", help="Proceed on poor suitability")
    parser.add_argument("--no-optimize", action="store_true", help="Skip SVG optimization")
    parser.add_argument("--no-comparison", action="store_true", help="Skip comparison PNG")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    run = vectorize(
        input_path=args.input,
        output_dir=args.output_dir,
        output_path=args.output_path,
        algorithm=args.algorithm,
        color_count=args.color_count,
        simplify=args.simplify,
        optimize=not args.no_optimize,
        comparison=not args.no_comparison,
        force=args.force,
    )
    print(run.svg_path)
    return 0


def _default_color_count(
    algorithm: Literal["vtracer", "potrace", "imagetracer"],
    suitability: Suitability,
) -> int:
    if algorithm == "potrace":
        return 2
    if algorithm == "imagetracer":
        return min(32, max(8, suitability.color_count_estimate))
    return min(16, max(4, suitability.color_count_estimate))


def _estimate_color_count(image: Image.Image) -> int:
    sample = composite_on_bg(image, bg_color="#FFFFFF").resize((64, 64), Image.Resampling.NEAREST)
    quantized = sample.convert("RGB").quantize(colors=256, method=Image.Quantize.MEDIANCUT)
    histogram = quantized.histogram()
    return sum(1 for count in histogram if count > 2)


def _edge_density(image: Image.Image) -> float:
    gray = composite_on_bg(image, bg_color="#FFFFFF").convert("L").resize((128, 128))
    edges = gray.filter(ImageFilter.FIND_EDGES)
    values = list(_pixel_data(edges))
    return round(sum(1 for value in values if value > 32) / len(values), 4)


def _gradient_prevalence(image: Image.Image) -> float:
    if _estimate_color_count(image) <= 16:
        return 0.0
    gray = composite_on_bg(image, bg_color="#FFFFFF").convert("L").resize((96, 96))
    blurred = gray.filter(ImageFilter.GaussianBlur(radius=2))
    diff = ImageChops.difference(gray, blurred)
    stddev = ImageStat.Stat(diff).stddev[0]
    return round(min(1.0, stddev / 28), 4)


def _quantize(image: Image.Image, color_count: int) -> Image.Image:
    rgba = ensure_alpha(image)
    background = composite_on_bg(rgba, bg_color="#FFFFFF").convert("RGB")
    quantized = background.quantize(
        colors=max(2, min(64, color_count)),
        method=Image.Quantize.MEDIANCUT,
    )
    rgb = quantized.convert("RGBA")
    rgb.putalpha(rgba.getchannel("A"))
    return rgb


def _posterize_monochrome(image: Image.Image) -> Image.Image:
    gray = composite_on_bg(image, bg_color="#FFFFFF").convert("L")
    threshold = ImageStat.Stat(gray).mean[0]
    output = Image.new("RGBA", image.size, (0, 0, 0, 0))
    alpha = ensure_alpha(image).getchannel("A")
    for y in range(image.height):
        for x in range(image.width):
            if alpha.getpixel((x, y)) > 16 and gray.getpixel((x, y)) < threshold:
                output.putpixel((x, y), (0, 0, 0, 255))
    return output


def _trace_rects(image: Image.Image, *, simplify: int) -> tuple[str, int]:
    cell = _cell_size(max(image.size), simplify)
    small_size = (max(1, math.ceil(image.width / cell)), max(1, math.ceil(image.height / cell)))
    small = ensure_alpha(image).resize(small_size, Image.Resampling.BOX)
    rows: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{image.width}" height="{image.height}" '
        f'viewBox="0 0 {image.width} {image.height}">'
    ]
    path_count = 0

    for y in range(small.height):
        x = 0
        while x < small.width:
            color = small.getpixel((x, y))
            if color[3] < 16:
                x += 1
                continue
            run = 1
            while x + run < small.width and small.getpixel((x + run, y)) == color:
                run += 1
            rect_x = x * cell
            rect_y = y * cell
            rect_w = min(run * cell, image.width - rect_x)
            rect_h = min(cell, image.height - rect_y)
            attrs = (
                f'x="{rect_x}" y="{rect_y}" width="{rect_w}" height="{rect_h}" '
                f'fill="#{color[0]:02X}{color[1]:02X}{color[2]:02X}"'
            )
            if color[3] < 255:
                attrs += f' fill-opacity="{round(color[3] / 255, 4)}"'
            rows.append(f"  <rect {attrs}/>")
            path_count += 1
            x += run

    rows.append("</svg>")
    return "\n".join(rows), path_count


def _cell_size(max_side: int, simplify: int) -> int:
    target_cells = int(96 - (simplify / 100 * 64))
    target_cells = max(24, min(96, target_cells))
    return max(1, math.ceil(max_side / target_cells))


def _comparison_image(original: Image.Image, rendered: Image.Image) -> Image.Image:
    left = composite_on_bg(original, bg_color="#FFFFFF")
    right = composite_on_bg(rendered, bg_color="#FFFFFF")
    if left.size != right.size:
        right = right.resize(left.size, Image.Resampling.LANCZOS)
    output = Image.new("RGBA", (left.width * 2, left.height), (255, 255, 255, 255))
    output.alpha_composite(left, (0, 0))
    output.alpha_composite(right, (left.width, 0))
    return output


def _external_algorithm_missing(algorithm: str) -> bool:
    if algorithm == "potrace":
        return shutil.which("potrace") is None
    try:
        __import__({"vtracer": "vtracer", "imagetracer": "imagetracerpy"}[algorithm])
    except (ImportError, KeyError):
        return True
    return False


def _pixel_data(image: Image.Image):
    if hasattr(image, "get_flattened_data"):
        return image.get_flattened_data()
    return image.getdata()


if __name__ == "__main__":
    raise SystemExit(main())
