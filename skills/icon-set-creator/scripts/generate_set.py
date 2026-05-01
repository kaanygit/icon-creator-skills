"""icon-set-creator CLI."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol

from PIL import Image

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR.parent.parent.parent) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR.parent.parent.parent))

from shared.consistency_checker import ConsistencyChecker, ConsistencyScore  # noqa: E402
from shared.errors import InputError  # noqa: E402
from shared.image_utils import (  # noqa: E402
    compose_grid,
    ensure_alpha,
    load_image,
    pad_square,
    resize,
    save_png,
)
from shared.logging_setup import get_run_logger  # noqa: E402
from shared.openrouter_client import OpenRouterClient  # noqa: E402
from shared.prompt_builder import PromptBuilder  # noqa: E402
from shared.quality_validator import QualityValidator  # noqa: E402
from shared.style_memory import load_style  # noqa: E402
from shared.vision_analyzer import IconSetStyleGuide, VisionAnalyzer  # noqa: E402

MASTER_SIZE = 1024
DEFAULT_FALLBACK_MODELS = ["black-forest-labs/flux.2-pro"]


class ImageClient(Protocol):
    def generate(self, **kwargs: object) -> Any:
        """Generate image result compatible with shared.openrouter_client.GenerateResult."""


@dataclass(frozen=True)
class IconSetRun:
    run_dir: Path
    preview_path: Path
    metadata_path: Path
    style_guide_path: Path
    anchor_path: Path


@dataclass(frozen=True)
class IconRecord:
    subject: str
    path: Path
    score: ConsistencyScore | None
    attempts: int
    passed: bool
    prompt_hash: str

    def to_dict(self) -> dict[str, object]:
        return {
            "subject": self.subject,
            "path": str(self.path),
            "score": self.score.to_dict() if self.score else None,
            "attempts": self.attempts,
            "passed": self.passed,
            "prompt_hash": self.prompt_hash,
        }


def generate_icon_set(
    *,
    icons: list[str],
    style_preset: str,
    colors: list[str] | None = None,
    reference_icon: str | Path | None = None,
    style: str | None = None,
    set_name: str | None = None,
    stroke_width: str | None = None,
    corner_radius: str | None = None,
    model: str | None = None,
    output_dir: str | Path = "output",
    seed_base: int | None = None,
    best_of_n: int = 3,
    consistency_threshold: float = 0.80,
    client: ImageClient | None = None,
    prompt_builder: PromptBuilder | None = None,
    vision_analyzer: VisionAnalyzer | None = None,
    quality_validator: QualityValidator | None = None,
    consistency_checker: ConsistencyChecker | None = None,
    timestamp: datetime | None = None,
) -> IconSetRun:
    subjects = [item.strip() for item in icons if item.strip()]
    if not subjects:
        raise InputError("icons list cannot be empty")
    if best_of_n < 1 or best_of_n > 6:
        raise InputError("--best-of-n must be between 1 and 6")
    if style and not reference_icon:
        reference_icon = load_style(style).path / "style-anchor.png"

    builder = prompt_builder or PromptBuilder()
    analyzer = vision_analyzer or VisionAnalyzer()
    validator = quality_validator or QualityValidator()
    checker = consistency_checker or ConsistencyChecker()
    image_client = client or OpenRouterClient()
    timestamp = timestamp or datetime.now(UTC)
    name = set_name or f"{subjects[0]} icon set"
    run_dir = Path(output_dir) / f"{slugify(name)}-{timestamp.strftime('%Y%m%d-%H%M%S')}"
    run_dir.mkdir(parents=True, exist_ok=True)
    logger = get_run_logger(run_dir, "openrouter")
    icons_dir = run_dir / "icons"
    icons_dir.mkdir(parents=True, exist_ok=True)

    records: list[IconRecord] = []
    total_cost: float | None = None
    if reference_icon:
        anchor = prepare_icon(load_image(reference_icon))
        anchor_subject = "reference"
    else:
        anchor_prompt = _build_icon_prompt(
            builder=builder,
            subject=subjects[0],
            style_preset=style_preset,
            colors=colors,
            model=model,
            style_guide=None,
            stroke_width=stroke_width,
            corner_radius=corner_radius,
        )
        result = image_client.generate(
            model=anchor_prompt.model_recommendation,
            fallback_models=anchor_prompt.model_fallbacks or DEFAULT_FALLBACK_MODELS,
            prompt=anchor_prompt.positive,
            negative_prompt=anchor_prompt.negative,
            n=min(3, best_of_n),
            size=(MASTER_SIZE, MASTER_SIZE),
            seed=seed_base,
            run_logger=logger,
            skill="icon-set-creator",
        )
        total_cost = _add_cost(total_cost, getattr(result, "cost_usd", None))
        candidates = [prepare_icon(image) for image in result.images]
        best_index, best_result, _ = validator.pick_best(candidates, profile="app-icon")
        anchor = candidates[best_index]
        anchor_subject = subjects[0]
        path = save_png(anchor, icons_dir / f"{slugify(subjects[0], max_length=48)}.png")
        records.append(
            IconRecord(
                subject=subjects[0],
                path=path,
                score=None,
                attempts=1,
                passed=best_result.passed,
                prompt_hash=anchor_prompt.prompt_hash,
            )
        )

    anchor_path = save_png(anchor, run_dir / "style-anchor.png")
    style_guide = analyzer.extract_icon_set_style(anchor, colors=colors)

    remaining = subjects if reference_icon else subjects[1:]
    for index, subject in enumerate(remaining):
        record, total_cost = _generate_member(
            subject=subject,
            style_preset=style_preset,
            colors=colors,
            model=model,
            stroke_width=stroke_width,
            corner_radius=corner_radius,
            style_guide=style_guide,
            seed=None if seed_base is None else seed_base + index + 1,
            best_of_n=best_of_n,
            threshold=consistency_threshold,
            anchor_path=anchor_path,
            icons_dir=icons_dir,
            client=image_client,
            builder=builder,
            checker=checker,
            logger=logger,
            total_cost=total_cost,
        )
        records.append(record)

    preview_path = _write_preview(run_dir, records)
    style_guide_path = _write_style_guide(
        run_dir=run_dir,
        set_name=name,
        style_preset=style_preset,
        colors=colors or [],
        style_guide=style_guide,
        anchor_path=anchor_path,
        records=records,
        stroke_width=stroke_width,
        corner_radius=corner_radius,
        timestamp=timestamp,
    )
    metadata_path = _write_metadata(
        run_dir=run_dir,
        name=name,
        subjects=subjects,
        anchor_subject=anchor_subject,
        style_preset=style_preset,
        colors=colors or [],
        style_guide=style_guide,
        records=records,
        total_cost=total_cost,
        reference_icon=reference_icon,
        style=style,
    )
    return IconSetRun(
        run_dir=run_dir,
        preview_path=preview_path,
        metadata_path=metadata_path,
        style_guide_path=style_guide_path,
        anchor_path=anchor_path,
    )


def _generate_member(
    *,
    subject: str,
    style_preset: str,
    colors: list[str] | None,
    model: str | None,
    stroke_width: str | None,
    corner_radius: str | None,
    style_guide: IconSetStyleGuide,
    seed: int | None,
    best_of_n: int,
    threshold: float,
    anchor_path: Path,
    icons_dir: Path,
    client: ImageClient,
    builder: PromptBuilder,
    checker: ConsistencyChecker,
    logger: Any,
    total_cost: float | None,
) -> tuple[IconRecord, float | None]:
    prompt = _build_icon_prompt(
        builder=builder,
        subject=subject,
        style_preset=style_preset,
        colors=colors,
        model=model,
        style_guide=style_guide,
        stroke_width=stroke_width,
        corner_radius=corner_radius,
    )
    best_image: Image.Image | None = None
    best_score: ConsistencyScore | None = None
    attempts = 0
    for attempt in range(best_of_n):
        attempts += 1
        result = client.generate(
            model=prompt.model_recommendation,
            fallback_models=prompt.model_fallbacks or DEFAULT_FALLBACK_MODELS,
            prompt=prompt.positive,
            negative_prompt=prompt.negative,
            n=1,
            size=(MASTER_SIZE, MASTER_SIZE),
            seed=None if seed is None else seed + attempt,
            reference_image=anchor_path,
            strength=0.55,
            run_logger=logger,
            skill="icon-set-creator",
        )
        total_cost = _add_cost(total_cost, getattr(result, "cost_usd", None))
        candidate = prepare_icon(result.images[0])
        score = checker.score(candidate, anchor_path, threshold=threshold)
        if best_score is None or score.combined > best_score.combined:
            best_image = candidate
            best_score = score
        if score.passed:
            break
    if best_image is None:
        raise InputError(f"No image returned for icon subject: {subject}")
    path = save_png(best_image, icons_dir / f"{slugify(subject, max_length=48)}.png")
    return (
        IconRecord(
            subject=subject,
            path=path,
            score=best_score,
            attempts=attempts,
            passed=bool(best_score and best_score.passed),
            prompt_hash=prompt.prompt_hash,
        ),
        total_cost,
    )


def _build_icon_prompt(
    *,
    builder: PromptBuilder,
    subject: str,
    style_preset: str,
    colors: list[str] | None,
    model: str | None,
    style_guide: IconSetStyleGuide | None,
    stroke_width: str | None,
    corner_radius: str | None,
):
    extras = [
        "single icon in a coherent icon family",
        "same palette, stroke weight, corner radius, padding, and visual rhythm as the set",
    ]
    if style_guide:
        extras.append(f"locked style guide: {style_guide.descriptor}")
    if stroke_width:
        extras.append(f"stroke width: {stroke_width}")
    if corner_radius:
        extras.append(f"corner radius: {corner_radius}")
    return builder.build(
        skill="icon-creator",
        type="app-icon",
        preset=style_preset,
        description=subject,
        colors=colors,
        user_extras=", ".join(extras),
        model_override=model,
    )


def prepare_icon(image: Image.Image) -> Image.Image:
    square = pad_square(ensure_alpha(image))
    if square.size != (MASTER_SIZE, MASTER_SIZE):
        square = resize(square, (MASTER_SIZE, MASTER_SIZE))
    return ensure_alpha(square)


def _write_preview(run_dir: Path, records: list[IconRecord]) -> Path:
    images = [Image.open(record.path).convert("RGBA") for record in records]
    labels = [record.subject for record in records]
    grid = compose_grid(images, columns=min(4, len(images)), cell_size=260, labels=labels)
    return save_png(grid, run_dir / "preview.png")


def _write_style_guide(
    *,
    run_dir: Path,
    set_name: str,
    style_preset: str,
    colors: list[str],
    style_guide: IconSetStyleGuide,
    anchor_path: Path,
    records: list[IconRecord],
    stroke_width: str | None,
    corner_radius: str | None,
    timestamp: datetime,
) -> Path:
    lines = [
        f"# Style guide: {set_name}",
        "",
        f"Generated {timestamp.isoformat()} by icon-set-creator v1.0.0.",
        "",
        "## Visual language",
        "",
        f"- Preset: {style_preset}",
        f"- Stroke width: {stroke_width or style_guide.stroke_weight_estimate}",
        f"- Corner radius: {corner_radius or 'preset default'}",
        f"- Art style: {style_guide.art_style}",
        f"- Anchor: {anchor_path}",
        "",
        "## Palette",
        "",
        *[f"- {color}" for color in (colors or style_guide.colors)],
        "",
        "## Icons",
        "",
        *[f"- {record.subject}: `{record.path}`" for record in records],
        "",
        "## To add matching icons later",
        "",
        f"Use `--reference-icon {anchor_path}` with the same preset and colors.",
    ]
    path = run_dir / "style-guide.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _write_metadata(
    *,
    run_dir: Path,
    name: str,
    subjects: list[str],
    anchor_subject: str,
    style_preset: str,
    colors: list[str],
    style_guide: IconSetStyleGuide,
    records: list[IconRecord],
    total_cost: float | None,
    reference_icon: str | Path | None,
    style: str | None,
) -> Path:
    data = {
        "skill": "icon-set-creator",
        "version": "1.0.0",
        "set_name": name,
        "subjects": subjects,
        "anchor_subject": anchor_subject,
        "reference_icon": str(reference_icon) if reference_icon else None,
        "style": style,
        "style_preset": style_preset,
        "colors": colors,
        "style_guide": style_guide.to_dict(),
        "icons": [record.to_dict() for record in records],
        "cost": {"currency": "USD", "total": total_cost},
    }
    path = run_dir / "metadata.json"
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return path


def _add_cost(current: float | None, addition: float | None) -> float | None:
    if current is None:
        return addition
    if addition is None:
        return current
    return round(float(current) + float(addition), 6)


def parse_icons(value: str) -> list[str]:
    stripped = value.strip()
    if not stripped:
        raise InputError("icons cannot be empty")
    if stripped.startswith("["):
        parsed = json.loads(stripped)
        if not isinstance(parsed, list):
            raise InputError("icons JSON must be a list")
        return [str(item) for item in parsed]
    return [item.strip() for item in stripped.split(",") if item.strip()]


def parse_colors(value: str | None) -> list[str] | None:
    if not value:
        return None
    return [item.strip() for item in value.split(",") if item.strip()]


def slugify(value: str, *, max_length: int = 40) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    slug = re.sub(r"-{2,}", "-", slug)
    return (slug[:max_length].strip("-") or "icon-set")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a coherent icon set.")
    parser.add_argument("--icons", required=True, help="JSON list or comma-separated subjects")
    parser.add_argument("--style-preset", required=True, help="Icon style preset")
    parser.add_argument("--colors", default=None, help="Comma-separated hex colors")
    parser.add_argument("--reference-icon", default=None, help="Existing anchor icon")
    parser.add_argument("--style", default=None, help="Saved style name from icon-skills styles")
    parser.add_argument("--set-name", default=None, help="Output set name")
    parser.add_argument("--stroke-width", default=None, help="thin|regular|bold")
    parser.add_argument("--corner-radius", default=None, help="sharp|rounded|pill")
    parser.add_argument("--model", default=None, help="OpenRouter model override")
    parser.add_argument("--output-dir", default="output", help="Output root")
    parser.add_argument("--seed-base", type=int, default=None, help="Base seed")
    parser.add_argument("--best-of-n", type=int, default=3, help="Attempts per member")
    parser.add_argument("--consistency-threshold", type=float, default=0.80)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    run = generate_icon_set(
        icons=parse_icons(args.icons),
        style_preset=args.style_preset,
        colors=parse_colors(args.colors),
        reference_icon=args.reference_icon,
        style=args.style,
        set_name=args.set_name,
        stroke_width=args.stroke_width,
        corner_radius=args.corner_radius,
        model=args.model,
        output_dir=args.output_dir,
        seed_base=args.seed_base,
        best_of_n=args.best_of_n,
        consistency_threshold=args.consistency_threshold,
    )
    print(run.run_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
