"""mascot-creator CLI."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol

import yaml
from PIL import Image

from shared.consistency_checker import ConsistencyChecker, ConsistencyScore
from shared.errors import InputError
from shared.image_utils import compose_grid, ensure_alpha, pad_square, resize, save_png
from shared.logging_setup import get_run_logger
from shared.openrouter_client import OpenRouterClient
from shared.prompt_builder import PromptBuilder
from shared.quality_validator import QualityValidator
from shared.style_memory import load_style
from shared.vision_analyzer import CharacterTraits, VisionAnalyzer

DEFAULT_FALLBACK_MODELS = ["sourceful/riverflow-v2-fast-preview"]
DEFAULT_TYPE_PRESETS = {
    "stylized": "flat-vector",
    "realistic": "photoreal-3d",
    "artistic": "watercolor",
}
MASTER_SIZE = 1024
PRESETS_PATH = Path(__file__).parents[3] / "shared" / "presets" / "mascot-creator_styles.yaml"


class ImageClient(Protocol):
    def generate(self, **kwargs: object) -> Any:
        """Generate image result compatible with shared.openrouter_client.GenerateResult."""


@dataclass(frozen=True)
class MascotRun:
    run_dir: Path
    master_path: Path
    metadata_path: Path
    style_guide_path: Path
    character_sheet_path: Path | None


@dataclass(frozen=True)
class VariantRecord:
    kind: str
    name: str
    path: Path
    score: ConsistencyScore | None
    attempts: int
    passed: bool
    prompt_hash: str

    def to_dict(self) -> dict[str, object]:
        return {
            "kind": self.kind,
            "name": self.name,
            "path": str(self.path),
            "score": self.score.to_dict() if self.score else None,
            "attempts": self.attempts,
            "passed": self.passed,
            "prompt_hash": self.prompt_hash,
        }


def generate_mascot(
    *,
    description: str,
    mascot_type: str,
    preset: str | None = None,
    personality: str | None = None,
    output_dir: str | Path = "output",
    model: str | None = None,
    variants: int = 3,
    seed: int | None = None,
    views: list[str] | None = None,
    poses: list[str] | None = None,
    expressions: list[str] | None = None,
    outfits: list[str] | None = None,
    matrix: bool = False,
    best_of_n: int = 3,
    consistency_threshold: float = 0.85,
    reference_image: str | Path | None = None,
    style: str | None = None,
    mascot_name: str | None = None,
    client: ImageClient | None = None,
    prompt_builder: PromptBuilder | None = None,
    vision_analyzer: VisionAnalyzer | None = None,
    quality_validator: QualityValidator | None = None,
    consistency_checker: ConsistencyChecker | None = None,
    timestamp: datetime | None = None,
) -> MascotRun:
    description = description.strip()
    mascot_type = mascot_type.strip().lower()
    if not description:
        raise InputError("--description cannot be empty")
    if mascot_type not in DEFAULT_TYPE_PRESETS:
        raise InputError("--type must be one of: stylized, realistic, artistic")
    if variants < 1 or variants > 6:
        raise InputError("--variants must be between 1 and 6")
    if best_of_n < 1 or best_of_n > 6:
        raise InputError("--best-of-n must be between 1 and 6")

    preset = preset or DEFAULT_TYPE_PRESETS[mascot_type]
    presets = _load_presets()
    preset_config = presets.get(preset)
    if not preset_config:
        raise InputError(f"Unknown mascot preset: {preset}")
    if preset_config.get("type") != mascot_type:
        raise InputError(f"Preset '{preset}' belongs to type '{preset_config.get('type')}'")

    view_names = _parse_or_default(views, [])
    pose_names = _parse_or_default(poses, [])
    expression_names = _parse_or_default(expressions, [])
    outfit_names = _parse_or_default(outfits, [])
    if matrix and (not pose_names or not expression_names):
        raise InputError("--matrix requires both --poses and --expressions")
    if style and not reference_image:
        reference_image = load_style(style).path / "style-anchor.png"

    builder = prompt_builder or PromptBuilder()
    analyzer = vision_analyzer or VisionAnalyzer()
    validator = quality_validator or QualityValidator()
    checker = consistency_checker or ConsistencyChecker()
    image_client = client or OpenRouterClient()
    timestamp = timestamp or datetime.now(UTC)
    run_id = f"{slugify(mascot_name or description)}-{timestamp.strftime('%Y%m%d-%H%M%S')}"
    run_dir = Path(output_dir) / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    logger = get_run_logger(run_dir, "openrouter")

    master_prompt = builder.build(
        skill="mascot-creator",
        type=mascot_type,
        preset=preset,
        description=description,
        personality=personality,
        model_override=model,
    )
    result = image_client.generate(
        model=master_prompt.model_recommendation,
        fallback_models=master_prompt.model_fallbacks or DEFAULT_FALLBACK_MODELS,
        prompt=master_prompt.positive,
        negative_prompt=master_prompt.negative,
        n=variants,
        size=(MASTER_SIZE, MASTER_SIZE),
        seed=seed,
        reference_image=reference_image,
        run_logger=logger,
        skill="mascot-creator",
    )
    processed = [prepare_mascot(image) for image in result.images[:variants]]
    variants_dir = run_dir / "variants"
    variants_dir.mkdir(parents=True, exist_ok=True)
    variant_paths = [
        save_png(image, variants_dir / f"{index + 1}.png") for index, image in enumerate(processed)
    ]
    best_index, best_result, validation_results = validator.pick_best(
        processed,
        profile="mascot-master",
    )
    master = processed[best_index]
    master_path = save_png(master, run_dir / "master.png")
    traits = analyzer.extract_character_traits(
        master,
        description=description,
        personality=personality,
    )

    total_cost = getattr(result, "cost_usd", None)
    variant_records: list[VariantRecord] = []
    new_records, total_cost = _generate_named_variants(
        kind="view",
        names=view_names,
        prompt_variable="view",
        output_subdir="views",
        description=description,
        mascot_type=mascot_type,
        preset=preset,
        preset_config=preset_config,
        personality=personality,
        model=model,
        seed=seed,
        threshold=0.80,
        best_of_n=best_of_n,
        master_path=master_path,
        anchor_traits=traits,
        run_dir=run_dir,
        client=image_client,
        builder=builder,
        checker=checker,
        logger=logger,
        total_cost=total_cost,
    )
    variant_records.extend(new_records)
    new_records, total_cost = _generate_named_variants(
        kind="pose",
        names=pose_names,
        prompt_variable="pose",
        output_subdir="poses",
        description=description,
        mascot_type=mascot_type,
        preset=preset,
        preset_config=preset_config,
        personality=personality,
        model=model,
        seed=seed,
        threshold=consistency_threshold,
        best_of_n=best_of_n,
        master_path=master_path,
        anchor_traits=traits,
        run_dir=run_dir,
        client=image_client,
        builder=builder,
        checker=checker,
        logger=logger,
        total_cost=total_cost,
    )
    variant_records.extend(new_records)
    new_records, total_cost = _generate_named_variants(
        kind="expression",
        names=expression_names,
        prompt_variable="expression",
        output_subdir="expressions",
        description=description,
        mascot_type=mascot_type,
        preset=preset,
        preset_config=preset_config,
        personality=personality,
        model=model,
        seed=seed,
        threshold=consistency_threshold,
        best_of_n=best_of_n,
        master_path=master_path,
        anchor_traits=traits,
        run_dir=run_dir,
        client=image_client,
        builder=builder,
        checker=checker,
        logger=logger,
        total_cost=total_cost,
    )
    variant_records.extend(new_records)
    new_records, total_cost = _generate_named_variants(
        kind="outfit",
        names=outfit_names,
        prompt_variable="outfit",
        output_subdir="outfits",
        description=description,
        mascot_type=mascot_type,
        preset=preset,
        preset_config=preset_config,
        personality=personality,
        model=model,
        seed=seed,
        threshold=consistency_threshold,
        best_of_n=best_of_n,
        master_path=master_path,
        anchor_traits=traits,
        run_dir=run_dir,
        client=image_client,
        builder=builder,
        checker=checker,
        logger=logger,
        total_cost=total_cost,
    )
    variant_records.extend(new_records)
    if matrix:
        matrix_records, total_cost = _generate_matrix_variants(
            poses=pose_names,
            expressions=expression_names,
            description=description,
            mascot_type=mascot_type,
            preset=preset,
            preset_config=preset_config,
            personality=personality,
            model=model,
            seed=seed,
            threshold=consistency_threshold,
            best_of_n=best_of_n,
            master_path=master_path,
            anchor_traits=traits,
            run_dir=run_dir,
            client=image_client,
            builder=builder,
            checker=checker,
            logger=logger,
            total_cost=total_cost,
        )
        variant_records.extend(matrix_records)

    character_sheet_path = _write_character_sheet(
        run_dir=run_dir,
        master_path=master_path,
        records=variant_records,
    )
    style_guide_path = _write_style_guide(
        run_dir=run_dir,
        mascot_name=mascot_name or description,
        description=description,
        mascot_type=mascot_type,
        preset=preset,
        personality=personality,
        traits=traits,
        master_path=master_path,
        records=variant_records,
        timestamp=timestamp,
    )
    prompt_path = run_dir / "prompt-debug.txt"
    prompt_path.write_text(
        (
            f"[MASTER POSITIVE]\n{master_prompt.positive}\n\n"
            f"[MASTER NEGATIVE]\n{master_prompt.negative}\n"
        ),
        encoding="utf-8",
    )
    metadata = {
        "skill": "mascot-creator",
        "version": "0.4.0",
        "run_id": run_id,
        "timestamp": timestamp.isoformat(),
        "inputs": {
            "description": description,
            "type": mascot_type,
            "preset": preset,
            "personality": personality,
            "model": model,
            "variants": variants,
            "seed": seed,
            "views": view_names,
            "poses": pose_names,
            "expressions": expression_names,
            "outfits": outfit_names,
            "matrix": matrix,
            "best_of_n": best_of_n,
            "consistency_threshold": consistency_threshold,
            "reference_image": str(reference_image) if reference_image else None,
            "style": style,
        },
        "model": {
            "id": getattr(result, "model_used", master_prompt.model_recommendation),
            "fallback_used": bool(getattr(result, "fallback_used", False)),
            "requested": master_prompt.model_recommendation,
        },
        "prompt": {
            "positive": master_prompt.positive,
            "negative": master_prompt.negative,
            "hash": master_prompt.prompt_hash,
            "template": master_prompt.template,
        },
        "anchor_traits": traits.to_dict(),
        "validation": {
            "picked_variant": best_index + 1,
            "picked_passed": best_result.passed,
            "all": [item.to_dict() for item in validation_results],
        },
        "consistency": [record.to_dict() for record in variant_records],
        "cost": {"currency": "USD", "total": total_cost},
        "outputs": {
            "master": str(master_path),
            "variants": [str(path) for path in variant_paths],
            "character_sheet": str(character_sheet_path) if character_sheet_path else None,
            "style_guide": str(style_guide_path),
        },
    }
    metadata_path = run_dir / "metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    return MascotRun(
        run_dir=run_dir,
        master_path=master_path,
        metadata_path=metadata_path,
        style_guide_path=style_guide_path,
        character_sheet_path=character_sheet_path,
    )


def _generate_named_variants(
    *,
    kind: str,
    names: list[str],
    prompt_variable: str,
    output_subdir: str,
    description: str,
    mascot_type: str,
    preset: str,
    preset_config: dict[str, Any],
    personality: str | None,
    model: str | None,
    seed: int | None,
    threshold: float,
    best_of_n: int,
    master_path: Path,
    anchor_traits: CharacterTraits,
    run_dir: Path,
    client: ImageClient,
    builder: PromptBuilder,
    checker: ConsistencyChecker,
    logger: Any,
    total_cost: float | None,
) -> tuple[list[VariantRecord], float | None]:
    records: list[VariantRecord] = []
    if not names:
        return records, total_cost
    output_dir = run_dir / output_subdir
    output_dir.mkdir(parents=True, exist_ok=True)
    template_override = preset_config["variant_templates"][kind]
    for index, name in enumerate(names):
        prompt = builder.build(
            skill="mascot-creator",
            type=mascot_type,
            preset=preset,
            description=description,
            personality=personality,
            model_override=model,
            template_override=template_override,
            anchor_text=anchor_traits.anchor_text,
            **{prompt_variable: name},
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
                seed=None if seed is None else seed + 100 + index + attempt,
                reference_image=master_path,
                strength=0.62,
                run_logger=logger,
                skill="mascot-creator",
            )
            total_cost = _add_cost(total_cost, getattr(result, "cost_usd", None))
            candidate = prepare_mascot(result.images[0])
            score = checker.score(candidate, master_path, threshold=threshold)
            if best_score is None or score.combined > best_score.combined:
                best_image = candidate
                best_score = score
            if score.passed:
                break
        if best_image is None:
            raise InputError(f"No image returned for {kind}: {name}")
        path = save_png(best_image, output_dir / f"{slugify(name, max_length=40)}.png")
        records.append(
            VariantRecord(
                kind=kind,
                name=name,
                path=path,
                score=best_score,
                attempts=attempts,
                passed=bool(best_score and best_score.passed),
                prompt_hash=prompt.prompt_hash,
            )
        )
    return records, total_cost


def _generate_matrix_variants(
    *,
    poses: list[str],
    expressions: list[str],
    description: str,
    mascot_type: str,
    preset: str,
    preset_config: dict[str, Any],
    personality: str | None,
    model: str | None,
    seed: int | None,
    threshold: float,
    best_of_n: int,
    master_path: Path,
    anchor_traits: CharacterTraits,
    run_dir: Path,
    client: ImageClient,
    builder: PromptBuilder,
    checker: ConsistencyChecker,
    logger: Any,
    total_cost: float | None,
) -> tuple[list[VariantRecord], float | None]:
    records: list[VariantRecord] = []
    output_dir = run_dir / "pose-expression-matrix"
    output_dir.mkdir(parents=True, exist_ok=True)
    template_override = preset_config["variant_templates"]["matrix"]
    for pose_index, pose in enumerate(poses):
        for expression_index, expression in enumerate(expressions):
            prompt = builder.build(
                skill="mascot-creator",
                type=mascot_type,
                preset=preset,
                description=description,
                personality=personality,
                model_override=model,
                template_override=template_override,
                anchor_text=anchor_traits.anchor_text,
                pose=pose,
                expression=expression,
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
                    seed=(
                        None
                        if seed is None
                        else seed + 1000 + pose_index * 10 + expression_index + attempt
                    ),
                    reference_image=master_path,
                    strength=0.62,
                    run_logger=logger,
                    skill="mascot-creator",
                )
                total_cost = _add_cost(total_cost, getattr(result, "cost_usd", None))
                candidate = prepare_mascot(result.images[0])
                score = checker.score(candidate, master_path, threshold=threshold)
                if best_score is None or score.combined > best_score.combined:
                    best_image = candidate
                    best_score = score
                if score.passed:
                    break
            if best_image is None:
                raise InputError(f"No image returned for matrix: {pose}-{expression}")
            name = f"{pose}-{expression}"
            path = save_png(best_image, output_dir / f"{slugify(name, max_length=60)}.png")
            records.append(
                VariantRecord(
                    kind="matrix",
                    name=name,
                    path=path,
                    score=best_score,
                    attempts=attempts,
                    passed=bool(best_score and best_score.passed),
                    prompt_hash=prompt.prompt_hash,
                )
            )
    return records, total_cost


def prepare_mascot(image: Image.Image) -> Image.Image:
    square = pad_square(ensure_alpha(image))
    if square.size != (MASTER_SIZE, MASTER_SIZE):
        square = resize(square, (MASTER_SIZE, MASTER_SIZE))
    return ensure_alpha(square)


def _write_character_sheet(
    *,
    run_dir: Path,
    master_path: Path,
    records: list[VariantRecord],
) -> Path | None:
    selected = [record for record in records if record.kind in {"view", "pose", "expression"}]
    if not selected:
        return None
    images = [
        Image.open(master_path).copy(),
        *[Image.open(record.path).copy() for record in selected],
    ]
    labels = ["master", *[f"{record.kind}: {record.name}" for record in selected]]
    sheet = compose_grid(images, columns=min(4, len(images)), cell_size=300, labels=labels)
    return save_png(sheet, run_dir / "character-sheet.png")


def _write_style_guide(
    *,
    run_dir: Path,
    mascot_name: str,
    description: str,
    mascot_type: str,
    preset: str,
    personality: str | None,
    traits: CharacterTraits,
    master_path: Path,
    records: list[VariantRecord],
    timestamp: datetime,
) -> Path:
    by_kind: dict[str, list[str]] = {}
    for record in records:
        by_kind.setdefault(record.kind, []).append(record.name)
    lines = [
        f"# Style guide: {mascot_name}",
        "",
        f"Generated {timestamp.isoformat()} by mascot-creator v0.4.0.",
        "",
        "## Character",
        "",
        traits.anchor_text,
        "",
        "## Visual identity",
        "",
        f"- Description: {description}",
        f"- Type: {mascot_type}",
        f"- Preset: {preset}",
        f"- Personality: {personality or '-'}",
        f"- Master: {master_path}",
        "",
        "## Palette",
        "",
        *[f"- {color}" for color in traits.colors],
        "",
        "## Distinguishing features",
        "",
        *[f"- {feature}" for feature in traits.distinguishing_features],
    ]
    if traits.accessories:
        lines.extend(["", "## Accessories", "", *[f"- {item}" for item in traits.accessories]])
    lines.extend(["", "## Variants produced in this run"])
    for kind in ("view", "pose", "expression", "outfit", "matrix"):
        names = by_kind.get(kind, [])
        if names:
            lines.extend(["", f"### {kind.title()}", *[f"- {name}" for name in names]])
    lines.extend(
        [
            "",
            "## To extend this mascot later",
            "",
            "Use the master image and this anchor text as the locked identity reference.",
        ]
    )
    path = run_dir / "style-guide.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _load_presets() -> dict[str, Any]:
    with PRESETS_PATH.open("r", encoding="utf-8") as handle:
        return (yaml.safe_load(handle) or {}).get("mascot-creator", {})


def _add_cost(current: float | None, addition: float | None) -> float | None:
    if current is None:
        return addition
    if addition is None:
        return current
    return round(float(current) + float(addition), 6)


def _parse_or_default(values: list[str] | None, default: list[str]) -> list[str]:
    if values is None:
        return list(default)
    return [value.strip() for value in values if value.strip()]


def parse_csv(value: str | None) -> list[str] | None:
    if value is None:
        return None
    return [item.strip() for item in value.split(",") if item.strip()]


def slugify(value: str, *, max_length: int = 30) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    slug = re.sub(r"-{2,}", "-", slug)
    return (slug[:max_length].strip("-") or "mascot")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate mascot artwork and variants.")
    parser.add_argument("--description", required=True, help="Mascot description")
    parser.add_argument(
        "--type",
        required=True,
        dest="mascot_type",
        help="stylized|realistic|artistic",
    )
    parser.add_argument("--preset", default=None, help="Mascot preset")
    parser.add_argument("--personality", default=None, help="Optional personality descriptor")
    parser.add_argument("--output-dir", default="output", help="Output root directory")
    parser.add_argument("--model", default=None, help="OpenRouter model id override")
    parser.add_argument("--variants", type=int, default=3, help="Master variants, 1-6")
    parser.add_argument("--seed", type=int, default=None, help="Optional seed")
    parser.add_argument("--views", default=None, help="Comma-separated views")
    parser.add_argument("--poses", default=None, help="Comma-separated poses")
    parser.add_argument("--expressions", default=None, help="Comma-separated expressions")
    parser.add_argument("--outfits", default=None, help="Comma-separated outfits")
    parser.add_argument("--matrix", action="store_true", help="Generate pose x expression matrix")
    parser.add_argument("--best-of-n", type=int, default=3, help="Attempts per variant")
    parser.add_argument("--consistency-threshold", type=float, default=0.85)
    parser.add_argument("--reference-image", default=None, help="Optional reference image")
    parser.add_argument("--style", default=None, help="Saved style name from icon-skills styles")
    parser.add_argument("--mascot-name", default=None, help="Output naming override")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    run = generate_mascot(
        description=args.description,
        mascot_type=args.mascot_type,
        preset=args.preset,
        personality=args.personality,
        output_dir=args.output_dir,
        model=args.model,
        variants=args.variants,
        seed=args.seed,
        views=parse_csv(args.views),
        poses=parse_csv(args.poses),
        expressions=parse_csv(args.expressions),
        outfits=parse_csv(args.outfits),
        matrix=args.matrix,
        best_of_n=args.best_of_n,
        consistency_threshold=args.consistency_threshold,
        reference_image=args.reference_image,
        style=args.style,
        mascot_name=args.mascot_name,
    )
    print(run.run_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
