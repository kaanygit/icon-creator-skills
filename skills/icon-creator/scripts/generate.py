"""Phase 01 icon-creator CLI."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol

from PIL import Image

from shared.errors import InputError
from shared.image_utils import ensure_alpha, pad_square, resize, save_png
from shared.logging_setup import get_run_logger
from shared.openrouter_client import OpenRouterClient
from shared.prompt_builder import PromptBuilder
from shared.vision_analyzer import StyleHints, VisionAnalyzer

DEFAULT_MODEL = "google/gemini-3.1-flash-image-preview"
DEFAULT_FALLBACK_MODELS = ["black-forest-labs/flux.2-pro"]
DEFAULT_STYLE_PRESET = "flat"
MASTER_SIZE = 1024


class ImageClient(Protocol):
    def generate(self, **kwargs: object) -> Any:
        """Generate image result compatible with shared.openrouter_client.GenerateResult."""


@dataclass(frozen=True)
class IconRun:
    run_dir: Path
    master_path: Path
    metadata_path: Path
    prompt_path: Path


def build_prompt(description: str) -> str:
    description = description.strip()
    if not description:
        raise InputError("--description cannot be empty")
    return f"{description}, app icon, centered, transparent background, square, no text"


def generate_icon(
    *,
    description: str,
    output_dir: str | Path = "output",
    model: str | None = None,
    style_preset: str = DEFAULT_STYLE_PRESET,
    colors: list[str] | None = None,
    reference_image: str | Path | None = None,
    client: ImageClient | None = None,
    prompt_builder: PromptBuilder | None = None,
    vision_analyzer: VisionAnalyzer | None = None,
    timestamp: datetime | None = None,
) -> IconRun:
    if not description.strip():
        raise InputError("--description cannot be empty")

    reference_hints = _analyze_reference(reference_image, vision_analyzer)
    builder = prompt_builder or PromptBuilder()
    prompt = builder.build(
        skill="icon-creator",
        type="app-icon",
        preset=style_preset,
        description=description,
        colors=colors,
        reference_hints=reference_hints,
        model_override=model,
    )
    timestamp = timestamp or datetime.now(UTC)
    run_id = f"{slugify(description)}-{timestamp.strftime('%Y%m%d-%H%M%S')}"
    run_dir = Path(output_dir) / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    logger = get_run_logger(run_dir, "openrouter")
    image_client = client or OpenRouterClient()
    result = image_client.generate(
        model=prompt.model_recommendation,
        fallback_models=prompt.model_fallbacks or DEFAULT_FALLBACK_MODELS,
        prompt=prompt.positive,
        negative_prompt=prompt.negative,
        n=1,
        size=(MASTER_SIZE, MASTER_SIZE),
        run_logger=logger,
        skill="icon-creator",
    )

    images = result.images
    if not images:
        raise InputError("OpenRouter returned no images")

    master = prepare_master(images[0])
    master_path = save_png(master, run_dir / "master.png")

    prompt_path = run_dir / "prompt-debug.txt"
    prompt_path.write_text(
        f"[POSITIVE]\n{prompt.positive}\n\n[NEGATIVE]\n{prompt.negative}\n",
        encoding="utf-8",
    )

    metadata = {
        "skill": "icon-creator",
        "version": "0.2.0",
        "run_id": run_id,
        "timestamp": timestamp.isoformat(),
        "inputs": {
            "description": description,
            "type": "app-icon",
            "style-preset": style_preset,
            "colors": colors or [],
            "reference-image": str(reference_image) if reference_image else None,
            "model": model,
        },
        "model": {
            "id": getattr(result, "model_used", prompt.model_recommendation),
            "fallback_used": bool(getattr(result, "fallback_used", False)),
            "requested": prompt.model_recommendation,
        },
        "prompt": {
            "positive": prompt.positive,
            "negative": prompt.negative,
            "hash": prompt.prompt_hash,
            "template": prompt.template,
        },
        "reference_hints": reference_hints.to_dict() if reference_hints else None,
        "cost": {
            "currency": "USD",
            "total": getattr(result, "cost_usd", None),
        },
        "outputs": {
            "master": str(master_path),
        },
    }
    metadata_path = run_dir / "metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    return IconRun(
        run_dir=run_dir,
        master_path=master_path,
        metadata_path=metadata_path,
        prompt_path=prompt_path,
    )


def prepare_master(image: Image.Image) -> Image.Image:
    """Normalize generated output to a 1024x1024 transparent PNG canvas."""

    square = pad_square(ensure_alpha(image))
    if square.size != (MASTER_SIZE, MASTER_SIZE):
        square = resize(square, (MASTER_SIZE, MASTER_SIZE))
    return ensure_alpha(square)


def slugify(value: str, *, max_length: int = 30) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    slug = re.sub(r"-{2,}", "-", slug)
    return (slug[:max_length].strip("-") or "icon")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a single icon PNG.")
    parser.add_argument("--description", required=True, help="Icon description")
    parser.add_argument("--output-dir", default="output", help="Output root directory")
    parser.add_argument("--model", default=None, help="OpenRouter model id override")
    parser.add_argument(
        "--style-preset",
        default=DEFAULT_STYLE_PRESET,
        choices=[
            "flat",
            "gradient",
            "glass-morphism",
            "outline",
            "3d-isometric",
            "skeuomorphic",
            "neumorphic",
            "material",
            "ios-style",
        ],
        help="Icon style preset",
    )
    parser.add_argument(
        "--colors",
        default=None,
        help="Comma-separated color palette, e.g. '#FF5733,#1A1A1A'",
    )
    parser.add_argument("--reference-image", default=None, help="Reference PNG/JPG path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    run = generate_icon(
        description=args.description,
        output_dir=args.output_dir,
        model=args.model,
        style_preset=args.style_preset,
        colors=parse_colors(args.colors),
        reference_image=args.reference_image,
    )
    print(run.master_path)
    return 0


def parse_colors(value: str | None) -> list[str] | None:
    if not value:
        return None
    colors = [item.strip() for item in value.split(",") if item.strip()]
    return colors or None


def _analyze_reference(
    reference_image: str | Path | None,
    analyzer: VisionAnalyzer | None,
) -> StyleHints | None:
    if not reference_image:
        return None
    return (analyzer or VisionAnalyzer()).analyze_style(reference_image)


if __name__ == "__main__":
    raise SystemExit(main())
