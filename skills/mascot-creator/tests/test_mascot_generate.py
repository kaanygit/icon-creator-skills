from __future__ import annotations

import importlib.util
import json
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
import yaml
from PIL import Image

from shared.consistency_checker import ConsistencyChecker
from shared.prompt_builder import PromptBuilder

SCRIPT_PATH = Path(__file__).parents[1] / "scripts" / "generate.py"
PRESETS_PATH = Path(__file__).parents[3] / "shared" / "presets" / "mascot-creator_styles.yaml"


@dataclass
class FakeResult:
    images: list[Image.Image]
    cost_usd: float | None = 0.02
    model_used: str = "sourceful/riverflow-v2-fast-preview"
    fallback_used: bool = False


class FakeClient:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def generate(self, **kwargs: Any) -> FakeResult:
        self.calls.append(kwargs)
        n = int(kwargs.get("n", 1))
        images = []
        color_shift = len(self.calls) * 7
        for index in range(n):
            image = Image.new("RGBA", (768, 512), (255, 255, 255, 255))
            for x in range(250, 520):
                for y in range(90, 420):
                    image.putpixel((x, y), (220, 90 + color_shift + index, 40, 255))
            for x in range(330, 440):
                for y in range(35, 160):
                    image.putpixel((x, y), (250, 140, 70, 255))
            images.append(image)
        return FakeResult(images=images)


@pytest.fixture
def generate_module() -> Any:
    spec = importlib.util.spec_from_file_location("mascot_creator_generate", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_every_mascot_preset_and_variant_template_renders() -> None:
    presets = yaml.safe_load(PRESETS_PATH.read_text(encoding="utf-8"))["mascot-creator"]
    builder = PromptBuilder()

    assert len(presets) == 19
    for preset, config in presets.items():
        master = builder.build(
            skill="mascot-creator",
            type=config["type"],
            preset=preset,
            description="a fox character",
            personality="friendly",
        )
        assert "fox" in master.positive
        assert master.negative
        for kind, template in config["variant_templates"].items():
            prompt = builder.build(
                skill="mascot-creator",
                type=config["type"],
                preset=preset,
                description="a fox character",
                template_override=template,
                anchor_text="same orange fox with explorer scarf",
                view="side",
                pose="waving",
                expression="happy",
                outfit="adventurer",
            )
            assert "same" in prompt.positive
            assert kind in {"view", "pose", "expression", "outfit", "matrix"}


def test_generate_mascot_full_phase_08_to_11_outputs(
    tmp_path: Path,
    generate_module: Any,
) -> None:
    client = FakeClient()

    run = generate_module.generate_mascot(
        description="fox, friendly explorer",
        mascot_type="stylized",
        preset="cartoon-2d",
        personality="curious",
        output_dir=tmp_path,
        variants=1,
        seed=5,
        views=["front", "side"],
        poses=["idle", "running"],
        expressions=["happy", "curious"],
        outfits=["adventurer", "scientist"],
        matrix=True,
        best_of_n=1,
        client=client,
        timestamp=datetime(2026, 5, 1, 0, 0, 0, tzinfo=UTC),
    )

    assert run.master_path.exists()
    assert run.character_sheet_path and run.character_sheet_path.exists()
    assert run.style_guide_path.exists()
    assert run.metadata_path.exists()
    assert (run.run_dir / "views" / "front.png").exists()
    assert (run.run_dir / "poses" / "running.png").exists()
    assert (run.run_dir / "expressions" / "happy.png").exists()
    assert (run.run_dir / "outfits" / "scientist.png").exists()
    assert (run.run_dir / "pose-expression-matrix" / "running-curious.png").exists()

    metadata = json.loads(run.metadata_path.read_text(encoding="utf-8"))
    assert metadata["skill"] == "mascot-creator"
    assert metadata["version"] == "0.4.0"
    assert metadata["inputs"]["preset"] == "cartoon-2d"
    assert metadata["anchor_traits"]["anchor_text"]
    assert len(metadata["consistency"]) == 12
    assert metadata["outputs"]["style_guide"] == str(run.style_guide_path)
    assert len(client.calls) == 13


def test_missing_type_fails(generate_module: Any) -> None:
    with pytest.raises(Exception, match="type"):
        generate_module.generate_mascot(
            description="fox",
            mascot_type="unknown",
            client=FakeClient(),
        )


def test_default_preset_by_type(tmp_path: Path, generate_module: Any) -> None:
    run = generate_module.generate_mascot(
        description="gentle bear",
        mascot_type="artistic",
        output_dir=tmp_path,
        variants=1,
        best_of_n=1,
        client=FakeClient(),
        timestamp=datetime(2026, 5, 1, 0, 0, 0, tzinfo=UTC),
    )
    metadata = json.loads(run.metadata_path.read_text(encoding="utf-8"))

    assert metadata["inputs"]["preset"] == "watercolor"


def test_consistency_checker_scores_similar_images_higher(tmp_path: Path) -> None:
    anchor = tmp_path / "anchor.png"
    similar = tmp_path / "similar.png"
    different = tmp_path / "different.png"
    Image.new("RGBA", (64, 64), (240, 100, 50, 255)).save(anchor)
    Image.new("RGBA", (64, 64), (242, 104, 55, 255)).save(similar)
    Image.new("RGBA", (64, 64), (20, 30, 220, 255)).save(different)

    checker = ConsistencyChecker()
    assert checker.score(similar, anchor).combined > checker.score(different, anchor).combined
