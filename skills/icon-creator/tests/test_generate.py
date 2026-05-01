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

from shared.quality_validator import Check, QualityResult

SCRIPT_PATH = Path(__file__).parents[1] / "scripts" / "generate.py"


@dataclass
class FakeResult:
    images: list[Image.Image]
    cost_usd: float | None = 0.0144
    model_used: str = "sourceful/riverflow-v2-fast-preview"
    fallback_used: bool = False


class FakeClient:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def generate(self, **kwargs: Any) -> FakeResult:
        self.calls.append(kwargs)
        n = int(kwargs.get("n", 1))
        images = []
        for index in range(n):
            image = Image.new("RGBA", (512, 256), (0, 0, 0, 0))
            for x in range(156, 356):
                for y in range(28, 228):
                    image.putpixel((x, y), (255, 60 + index * 30, 0, 255))
            images.append(image)
        return FakeResult(images=images)


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
    assert run.preview_path and run.preview_path.exists()

    with Image.open(run.master_path) as image:
        assert image.format == "PNG"
        assert image.size == (1024, 1024)
        assert image.mode == "RGBA"

    metadata = json.loads(run.metadata_path.read_text(encoding="utf-8"))
    assert metadata["skill"] == "icon-creator"
    assert metadata["version"] == "0.3.0"
    assert metadata["inputs"]["description"] == "Cute fox"
    assert metadata["inputs"]["style-preset"] == "gradient"
    assert metadata["inputs"]["colors"] == ["#FF6600", "#111111"]
    assert metadata["outputs"]["master"] == str(run.master_path)
    assert len(metadata["outputs"]["variants"]) == 3
    assert metadata["outputs"]["preview"] == str(run.preview_path)
    assert metadata["validation"]["picked_variant"] >= 1
    assert "gradient" in metadata["prompt"]["positive"]
    assert metadata["prompt"]["negative"]

    assert client.calls[0]["model"] == "sourceful/riverflow-v2-fast-preview"
    assert client.calls[0]["n"] == 3
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


def test_refine_sets_reference_image_and_metadata(tmp_path: Path, generate_module: Any) -> None:
    previous_dir = tmp_path / "previous"
    previous_dir.mkdir()
    previous_master = previous_dir / "master.png"
    Image.new("RGBA", (1024, 1024), (0, 0, 0, 0)).save(previous_master)
    (previous_dir / "metadata.json").write_text(
        json.dumps({"inputs": {"description": "fox icon"}}),
        encoding="utf-8",
    )
    client = FakeClient()

    run = generate_module.generate_icon(
        description="more geometric",
        output_dir=tmp_path,
        refine=previous_master,
        client=client,
        timestamp=datetime(2026, 5, 1, 0, 0, 0, tzinfo=UTC),
    )

    metadata = json.loads(run.metadata_path.read_text(encoding="utf-8"))
    assert metadata["refinement_of"]["master"] == str(previous_master)
    assert metadata["inputs"]["description"] == "fox icon, refined: more geometric"
    assert client.calls[0]["reference_image"] == previous_master


def test_validation_failure_triggers_one_retry(tmp_path: Path, generate_module: Any) -> None:
    client = FakeClient()
    validator = FailingThenPassingValidator()

    run = generate_module.generate_icon(
        description="fox",
        output_dir=tmp_path,
        variants=1,
        seed=7,
        client=client,
        quality_validator=validator,
        timestamp=datetime(2026, 5, 1, 0, 0, 0, tzinfo=UTC),
    )

    metadata = json.loads(run.metadata_path.read_text(encoding="utf-8"))
    assert len(client.calls) == 2
    assert "Quality correction" in client.calls[1]["prompt"]
    assert client.calls[1]["seed"] == 1007
    assert metadata["validation"]["retry_count"] == 1
    assert metadata["validation"]["picked_passed"] is True
    assert metadata["cost"]["total"] == 0.0288
    assert len(metadata["outputs"]["variants"]) == 2


class FailingThenPassingValidator:
    def __init__(self) -> None:
        self.calls = 0

    def pick_best(
        self,
        candidates: list[Image.Image],
        *,
        profile: str,
    ) -> tuple[int, QualityResult, list[QualityResult]]:
        self.calls += 1
        if self.calls == 1:
            result = QualityResult(
                passed=False,
                checks={"contrast": Check(False, 0.1, "too low")},
                combined_score=0.1,
            )
            return 0, result, [result for _ in candidates]

        result = QualityResult(
            passed=True,
            checks={"contrast": Check(True, 1.0, "ok")},
            combined_score=1.0,
        )
        return len(candidates) - 1, result, [result for _ in candidates]
