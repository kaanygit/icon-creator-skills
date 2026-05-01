from __future__ import annotations

import importlib.util
import json
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from PIL import Image

SCRIPT_PATH = Path(__file__).parents[1] / "scripts" / "generate.py"


@dataclass
class FakeResult:
    images: list[Image.Image]
    cost_usd: float | None = 0.0144
    model_used: str = "google/gemini-3.1-flash-image-preview"
    fallback_used: bool = False


class FakeClient:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def generate(self, **kwargs: Any) -> FakeResult:
        self.calls.append(kwargs)
        return FakeResult(images=[Image.new("RGBA", (512, 256), (255, 0, 0, 255))])


@pytest.fixture
def generate_module() -> Any:
    spec = importlib.util.spec_from_file_location("icon_creator_generate", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_generate_icon_writes_master_and_metadata(tmp_path: Path, generate_module: Any) -> None:
    client = FakeClient()

    run = generate_module.generate_icon(
        description="Cute fox",
        output_dir=tmp_path,
        client=client,
        style_preset="gradient",
        colors=["#FF6600", "#111111"],
        timestamp=datetime(2026, 5, 1, 0, 0, 0, tzinfo=UTC),
    )

    assert run.master_path.exists()
    assert run.metadata_path.exists()
    assert run.prompt_path.exists()

    with Image.open(run.master_path) as image:
        assert image.format == "PNG"
        assert image.size == (1024, 1024)
        assert image.mode == "RGBA"

    metadata = json.loads(run.metadata_path.read_text(encoding="utf-8"))
    assert metadata["skill"] == "icon-creator"
    assert metadata["version"] == "0.2.0"
    assert metadata["inputs"]["description"] == "Cute fox"
    assert metadata["inputs"]["style-preset"] == "gradient"
    assert metadata["inputs"]["colors"] == ["#FF6600", "#111111"]
    assert metadata["outputs"]["master"] == str(run.master_path)
    assert "gradient" in metadata["prompt"]["positive"]
    assert metadata["prompt"]["negative"]

    assert client.calls[0]["model"] == "google/gemini-3.1-flash-image-preview"
    assert client.calls[0]["n"] == 1
    assert client.calls[0]["size"] == (1024, 1024)
    assert client.calls[0]["negative_prompt"]


def test_slugify_limits_length(generate_module: Any) -> None:
    slug = generate_module.slugify("A very long app icon description for a mountain dashboard")

    assert slug == "a-very-long-app-icon-descripti"
    assert len(slug) <= 30


def test_empty_description_fails(generate_module: Any) -> None:
    with pytest.raises(Exception, match="description"):
        generate_module.build_prompt("   ")


def test_every_style_preset_smoke_generates(tmp_path: Path, generate_module: Any) -> None:
    presets = [
        "flat",
        "gradient",
        "glass-morphism",
        "outline",
        "3d-isometric",
        "skeuomorphic",
        "neumorphic",
        "material",
        "ios-style",
    ]

    for preset in presets:
        run = generate_module.generate_icon(
            description=f"{preset} mountain",
            output_dir=tmp_path,
            style_preset=preset,
            client=FakeClient(),
            timestamp=datetime(2026, 5, 1, 0, 0, 0, tzinfo=UTC),
        )
        assert run.master_path.exists()


def test_reference_image_adds_hints(tmp_path: Path, generate_module: Any) -> None:
    reference = tmp_path / "reference.png"
    Image.new("RGBA", (32, 32), (0, 128, 255, 255)).save(reference)

    run = generate_module.generate_icon(
        description="lighthouse",
        output_dir=tmp_path,
        reference_image=reference,
        client=FakeClient(),
        timestamp=datetime(2026, 5, 1, 0, 0, 0, tzinfo=UTC),
    )

    metadata = json.loads(run.metadata_path.read_text(encoding="utf-8"))
    assert metadata["reference_hints"]["palette"]
    assert "reference" in metadata["prompt"]["positive"]
