"""Live OpenRouter smoke test for Phase 00."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from shared.image_utils import save_png
from shared.logging_setup import get_run_logger
from shared.openrouter_client import OpenRouterClient


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a single smoke-test image.")
    parser.add_argument("description")
    parser.add_argument("--model", default="sourceful/riverflow-v2-fast-preview")
    parser.add_argument("--output-dir", default="output")
    args = parser.parse_args()

    timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    slug = _slug(args.description)
    run_dir = Path(args.output_dir) / f"smoke-{slug}-{timestamp}"
    run_dir.mkdir(parents=True, exist_ok=True)

    logger = get_run_logger(run_dir, "openrouter")
    client = OpenRouterClient()
    prompt = f"{args.description}, centered icon, transparent background, square, no text"
    result = client.generate(
        model=args.model,
        fallback_models=["black-forest-labs/flux.2-pro"],
        prompt=prompt,
        n=1,
        run_logger=logger,
        skill="smoke-test",
    )

    master_path = save_png(result.images[0], run_dir / "master.png")
    metadata = {
        "skill": "smoke-test",
        "timestamp": datetime.now(UTC).isoformat(),
        "description": args.description,
        "model_used": result.model_used,
        "fallback_used": result.fallback_used,
        "cost_usd": result.cost_usd,
    }
    (run_dir / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(master_path)
    return 0


def _slug(value: str) -> str:
    chars = [char.lower() if char.isalnum() else "-" for char in value.strip()]
    slug = "".join(chars).strip("-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug[:30] or "image"


if __name__ == "__main__":
    raise SystemExit(main())

