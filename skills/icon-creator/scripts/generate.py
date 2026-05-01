"""icon-creator CLI."""

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
from shared.quality_validator import QualityValidator
from shared.vision_analyzer import StyleHints, VisionAnalyzer

DEFAULT_MODEL = "sourceful/riverflow-v2-fast-preview"
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
    preview_path: Path | None


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
    variants: int = 3,
    seed: int | None = None,
    refine: str | Path | None = None,
    client: ImageClient | None = None,
    prompt_builder: PromptBuilder | None = None,
    vision_analyzer: VisionAnalyzer | None = None,
    quality_validator: QualityValidator | None = None,
    timestamp: datetime | None = None,
) -> IconRun:
    if variants < 1 or variants > 6:
        raise InputError("--variants must be between 1 and 6")

    refine_path = Path(refine) if refine else None
    base_description, refinement_of = _resolve_description(description, refine_path)
    reference_hints = _analyze_reference(reference_image, vision_analyzer)
    builder = prompt_builder or PromptBuilder()
    prompt = builder.build(
        skill="icon-creator",
        type="app-icon",
        preset=style_preset,
        description=base_description,
        colors=colors,
        reference_hints=reference_hints,
        model_override=model,
    )
    timestamp = timestamp or datetime.now(UTC)
    run_id = f"{slugify(base_description)}-{timestamp.strftime('%Y%m%d-%H%M%S')}"
    run_dir = Path(output_dir) / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    logger = get_run_logger(run_dir, "openrouter")
    image_client = client or OpenRouterClient()
    result = image_client.generate(
        model=prompt.model_recommendation,
        fallback_models=prompt.model_fallbacks or DEFAULT_FALLBACK_MODELS,
        prompt=prompt.positive,
        negative_prompt=prompt.negative,
        n=variants,
        size=(MASTER_SIZE, MASTER_SIZE),
        seed=seed,
        reference_image=refine_path,
        run_logger=logger,
        skill="icon-creator",
    )

    images = result.images
    if not images:
        raise InputError("OpenRouter returned no images")

    processed = [prepare_master(image) for image in images[:variants]]
    variants_dir = run_dir / "variants"
    variants_dir.mkdir(parents=True, exist_ok=True)
    variant_paths = [
        save_png(image, variants_dir / f"{index + 1}.png") for index, image in enumerate(processed)
    ]

    validator = quality_validator or QualityValidator()
    best_index, best_result, validation_results = validator.pick_best(processed, profile="app-icon")
    retry_count = 0
    total_cost = getattr(result, "cost_usd", None)
    if not best_result.passed:
        retry_count = 1
        retry_result = image_client.generate(
            model=prompt.model_recommendation,
            fallback_models=prompt.model_fallbacks or DEFAULT_FALLBACK_MODELS,
            prompt=_augment_prompt_for_retry(prompt.positive, best_result),
            negative_prompt=prompt.negative,
            n=variants,
            size=(MASTER_SIZE, MASTER_SIZE),
            seed=None if seed is None else seed + 1000,
            reference_image=refine_path,
            run_logger=logger,
            skill="icon-creator",
        )
        retry_processed = [prepare_master(image) for image in retry_result.images[:variants]]
        for image in retry_processed:
            variant_paths.append(save_png(image, variants_dir / f"{len(variant_paths) + 1}.png"))
        processed.extend(retry_processed)
        best_index, best_result, validation_results = validator.pick_best(
            processed,
            profile="app-icon",
        )
        retry_cost = getattr(retry_result, "cost_usd", None)
        if total_cost is not None and retry_cost is not None:
            total_cost = round(float(total_cost) + float(retry_cost), 6)
        elif retry_cost is not None:
            total_cost = retry_cost

    master = processed[best_index]
    master_path = save_png(master, run_dir / "master.png")
    preview_path = save_png(_compose_preview(processed), run_dir / "preview.png")

    prompt_path = run_dir / "prompt-debug.txt"
    prompt_path.write_text(
        f"[POSITIVE]\n{prompt.positive}\n\n[NEGATIVE]\n{prompt.negative}\n",
        encoding="utf-8",
    )

    metadata = {
        "skill": "icon-creator",
        "version": "0.3.0",
        "run_id": run_id,
        "timestamp": timestamp.isoformat(),
        "inputs": {
            "description": base_description,
            "type": "app-icon",
            "style-preset": style_preset,
            "colors": colors or [],
            "reference-image": str(reference_image) if reference_image else None,
            "model": model,
            "variants": variants,
            "seed": seed,
            "refine": str(refine_path) if refine_path else None,
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
        "validation": {
            "picked_variant": best_index + 1,
            "picked_passed": best_result.passed,
            "best_attempt": not best_result.passed,
            "retry_count": retry_count,
            "warnings": [] if best_result.passed else _validation_warnings(best_result),
            "all": [result.to_dict() for result in validation_results],
        },
        "cost": {
            "currency": "USD",
            "total": total_cost,
        },
        "outputs": {
            "master": str(master_path),
            "preview": str(preview_path),
            "variants": [str(path) for path in variant_paths],
        },
    }
    if refinement_of:
        metadata["refinement_of"] = refinement_of
    metadata_path = run_dir / "metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    return IconRun(
        run_dir=run_dir,
        master_path=master_path,
        metadata_path=metadata_path,
        prompt_path=prompt_path,
        preview_path=preview_path,
    )


def prepare_master(image: Image.Image) -> Image.Image:
    """Normalize generated output to a 1024x1024 transparent PNG canvas."""

    square = pad_square(ensure_alpha(image))
    if square.size != (MASTER_SIZE, MASTER_SIZE):
        square = resize(square, (MASTER_SIZE, MASTER_SIZE))
    return ensure_alpha(square)


def _validation_warnings(result: Any) -> list[str]:
    warnings = []
    for name, check in result.checks.items():
        if not check.passed:
            warnings.append(f"{name}: {check.message}")
    return warnings


def _augment_prompt_for_retry(prompt: str, result: Any) -> str:
    failed_checks = "; ".join(_validation_warnings(result))
    return (
        f"{prompt}\n\n"
        "Quality correction: regenerate as a clean, centered, square app icon with strong "
        "contrast, a readable silhouette at 16x16, no letters, no words, no UI mockup, "
        f"and fix these validation issues: {failed_checks}"
    )


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
    parser.add_argument(
        "--variants",
        type=int,
        default=3,
        help="Number of variants to generate, 1-6",
    )
    parser.add_argument("--seed", type=int, default=None, help="Optional reproducibility seed")
    parser.add_argument("--refine", default=None, help="Existing master.png to refine")
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
        variants=args.variants,
        seed=args.seed,
        refine=args.refine,
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


def _resolve_description(
    description: str,
    refine_path: Path | None,
) -> tuple[str, dict[str, str] | None]:
    description = description.strip()
    if not description and not refine_path:
        raise InputError("--description cannot be empty")
    if not refine_path:
        return description, None

    if not refine_path.exists():
        raise InputError(f"--refine image not found: {refine_path}")

    metadata_path = refine_path.parent / "metadata.json"
    previous_description = ""
    if metadata_path.exists():
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        previous_description = metadata.get("inputs", {}).get("description", "")

    if description and previous_description:
        resolved = f"{previous_description}, refined: {description}"
    else:
        resolved = description or previous_description or "refined icon"

    return resolved, {"master": str(refine_path), "metadata": str(metadata_path)}


def _compose_preview(images: list[Image.Image]) -> Image.Image:
    from shared.image_utils import compose_grid

    return compose_grid(images, columns=min(3, len(images)), cell_size=320)


if __name__ == "__main__":
    raise SystemExit(main())
