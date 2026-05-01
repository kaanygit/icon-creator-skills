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

DEFAULT_MODEL = "google/gemini-3-pro-image-preview"
DEFAULT_FALLBACK_MODELS = ["black-forest-labs/flux.2-pro"]
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
    model: str = DEFAULT_MODEL,
    client: ImageClient | None = None,
    timestamp: datetime | None = None,
) -> IconRun:
    prompt = build_prompt(description)
    timestamp = timestamp or datetime.now(UTC)
    run_id = f"{slugify(description)}-{timestamp.strftime('%Y%m%d-%H%M%S')}"
    run_dir = Path(output_dir) / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    logger = get_run_logger(run_dir, "openrouter")
    image_client = client or OpenRouterClient()
    result = image_client.generate(
        model=model,
        fallback_models=DEFAULT_FALLBACK_MODELS,
        prompt=prompt,
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
    prompt_path.write_text(prompt + "\n", encoding="utf-8")

    metadata = {
        "skill": "icon-creator",
        "version": "0.1.0",
        "run_id": run_id,
        "timestamp": timestamp.isoformat(),
        "inputs": {
            "description": description,
            "model": model,
        },
        "model": {
            "id": getattr(result, "model_used", model),
            "fallback_used": bool(getattr(result, "fallback_used", False)),
        },
        "prompt": {
            "positive": prompt,
            "negative": None,
        },
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
    parser.add_argument("--model", default=DEFAULT_MODEL, help="OpenRouter model id")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    run = generate_icon(
        description=args.description,
        output_dir=args.output_dir,
        model=args.model,
    )
    print(run.master_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
