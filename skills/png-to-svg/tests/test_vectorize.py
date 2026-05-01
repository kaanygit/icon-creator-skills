from __future__ import annotations

import importlib.util
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from PIL import Image

SCRIPT_PATH = Path(__file__).parents[1] / "scripts" / "vectorize.py"


def load_vectorize_module() -> Any:
    spec = importlib.util.spec_from_file_location("png_to_svg_vectorize", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_vectorize_flat_icon_writes_svg_comparison_and_stats(tmp_path: Path) -> None:
    vectorize = load_vectorize_module()
    source = tmp_path / "flat.png"
    _write_flat_icon(source)

    run = vectorize.vectorize(
        input_path=source,
        output_dir=tmp_path,
        algorithm="vtracer",
        color_count=4,
        simplify=20,
        timestamp=datetime(2026, 5, 1, 0, 0, 0, tzinfo=UTC),
    )

    assert run.svg_path.exists()
    assert run.comparison_path and run.comparison_path.exists()
    stats = json.loads(run.stats_path.read_text(encoding="utf-8"))
    assert stats["version"] == "0.2.0"
    assert stats["settings"]["algorithm_used"] == "vtracer"
    assert stats["output"]["path_count"] > 0
    assert stats["output"]["render_similarity"] >= 0.90


def test_auto_selects_potrace_for_two_color_icon(tmp_path: Path) -> None:
    vectorize = load_vectorize_module()
    source = tmp_path / "mono.png"
    _write_mono_icon(source)

    run = vectorize.vectorize(
        input_path=source,
        output_dir=tmp_path,
        algorithm="auto",
        timestamp=datetime(2026, 5, 1, 0, 0, 0, tzinfo=UTC),
    )

    stats = json.loads(run.stats_path.read_text(encoding="utf-8"))
    assert stats["settings"]["algorithm_used"] == "potrace"


def test_auto_selects_imagetracer_for_gradient_icon(tmp_path: Path) -> None:
    vectorize = load_vectorize_module()
    source = tmp_path / "gradient.png"
    _write_gradient_icon(source)

    run = vectorize.vectorize(
        input_path=source,
        output_dir=tmp_path,
        algorithm="auto",
        force=True,
        timestamp=datetime(2026, 5, 1, 0, 0, 0, tzinfo=UTC),
    )

    stats = json.loads(run.stats_path.read_text(encoding="utf-8"))
    assert stats["settings"]["algorithm_used"] == "imagetracer"


def test_photo_like_input_refuses_without_force(tmp_path: Path) -> None:
    vectorize = load_vectorize_module()
    source = tmp_path / "photo.png"
    _write_photo_like(source)

    with pytest.raises(Exception, match="suitability is poor"):
        vectorize.vectorize(input_path=source, output_dir=tmp_path)


def _write_flat_icon(path: Path) -> None:
    image = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    for x in range(48, 208):
        for y in range(48, 208):
            image.putpixel((x, y), (255, 90, 20, 255))
    image.save(path)


def _write_mono_icon(path: Path) -> None:
    image = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    for x in range(70, 186):
        for y in range(70, 186):
            image.putpixel((x, y), (0, 0, 0, 255))
    image.save(path)


def _write_gradient_icon(path: Path) -> None:
    image = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    for x in range(40, 216):
        for y in range(40, 216):
            image.putpixel((x, y), (x, y, 180, 255))
    image.save(path)


def _write_photo_like(path: Path) -> None:
    image = Image.new("RGBA", (256, 256), (0, 0, 0, 255))
    for x in range(256):
        for y in range(256):
            value = (x * 17 + y * 31 + (x * y) % 97) % 256
            image.putpixel((x, y), (value, (value * 3) % 256, (value * 7) % 256, 255))
    image.save(path)
