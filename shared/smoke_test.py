"""Live image-provider smoke test."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from shared.config import load_config
from shared.image_clients import (
    create_image_client,
    fallback_models_for_provider,
    resolve_model_for_provider,
    resolve_provider,
)
from shared.image_utils import save_png
from shared.logging_setup import get_run_logger


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a single smoke-test image.")
    parser.add_argument("description")
    parser.add_argument("--provider", default=None, help="openrouter, openai, or google")
    parser.add_argument("--model", default=None, help="Provider model override")
    parser.add_argument("--output-dir", default="output")
    args = parser.parse_args()
    config = load_config()
    provider = resolve_provider(args.provider, config=config)

    timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    slug = _slug(args.description)
    run_dir = Path(args.output_dir) / f"smoke-{slug}-{timestamp}"
    run_dir.mkdir(parents=True, exist_ok=True)

    logger = get_run_logger(run_dir, provider)
    client = create_image_client(provider, config=config)
    prompt = f"{args.description}, centered icon, transparent background, square, no text"
    model = resolve_model_for_provider(
        provider=provider,
        requested_model=args.model,
        prompt_model="sourceful/riverflow-v2-fast-preview",
        config=config,
    )
    fallback_models = fallback_models_for_provider(
        provider=provider,
        requested_model=args.model,
        prompt_fallbacks=["black-forest-labs/flux.2-pro"],
        config=config,
    )
    result = client.generate(
        model=model,
        fallback_models=fallback_models,
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
        "provider": provider,
        "requested_model": model,
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
