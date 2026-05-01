from __future__ import annotations

import importlib.util
import json
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from PIL import Image

SCRIPT_PATH = Path(__file__).parents[1] / "scripts" / "generate_set.py"


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
        for index in range(n):
            image = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
            for x in range(140, 372):
                for y in range(140, 372):
                    image.putpixel((x, y), (37, 99 + index, 235, 255))
            images.append(image)
        return FakeResult(images=images)


def load_module() -> Any:
    spec = importlib.util.spec_from_file_location("icon_set_generate", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_generate_icon_set_writes_icons_preview_and_style_guide(tmp_path: Path) -> None:
    module = load_module()
    client = FakeClient()

    run = module.generate_icon_set(
        icons=["home", "search", "profile", "settings"],
        style_preset="flat",
        colors=["#2563EB", "#1E40AF"],
        set_name="nav icons",
        output_dir=tmp_path,
        seed_base=10,
        best_of_n=1,
        client=client,
        timestamp=datetime(2026, 5, 1, 0, 0, 0, tzinfo=UTC),
    )

    assert run.anchor_path.exists()
    assert run.preview_path.exists()
    assert run.style_guide_path.exists()
    assert run.metadata_path.exists()
    assert (run.run_dir / "icons" / "home.png").exists()
    assert (run.run_dir / "icons" / "settings.png").exists()
    metadata = json.loads(run.metadata_path.read_text(encoding="utf-8"))
    assert metadata["skill"] == "icon-set-creator"
    assert metadata["style_preset"] == "flat"
    assert len(metadata["icons"]) == 4
    assert len(client.calls) == 4


def test_reference_icon_skips_anchor_generation(tmp_path: Path) -> None:
    module = load_module()
    anchor = tmp_path / "anchor.png"
    Image.new("RGBA", (1024, 1024), (0, 0, 0, 0)).save(anchor)
    client = FakeClient()

    run = module.generate_icon_set(
        icons=["search", "settings"],
        style_preset="flat",
        reference_icon=anchor,
        output_dir=tmp_path,
        best_of_n=1,
        client=client,
        timestamp=datetime(2026, 5, 1, 0, 0, 0, tzinfo=UTC),
    )

    assert len(client.calls) == 2
    assert (run.run_dir / "icons" / "search.png").exists()


def test_parse_icons_accepts_json_and_csv() -> None:
    module = load_module()

    assert module.parse_icons('["home", "search"]') == ["home", "search"]
    assert module.parse_icons("home,search") == ["home", "search"]
