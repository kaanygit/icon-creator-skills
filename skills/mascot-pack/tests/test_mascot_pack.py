from __future__ import annotations

import importlib.util
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from PIL import Image

SCRIPT_PATH = Path(__file__).parents[1] / "scripts" / "pack.py"


def load_module() -> Any:
    script_dir = str(SCRIPT_PATH.parent)
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
    spec = importlib.util.spec_from_file_location("mascot_pack", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_pack_mascot_writes_all_targets(tmp_path: Path) -> None:
    module = load_module()
    source = _fixture_run(tmp_path)

    run = module.pack_mascot(
        master=source / "master.png",
        variants_dir=source,
        targets=["social", "stickers", "print", "web"],
        mascot_name="test mascot",
        output_dir=tmp_path,
        create_zip=True,
        timestamp=datetime(2026, 5, 1, 0, 0, 0, tzinfo=UTC),
    )

    assert (run.run_dir / "master" / "master.png").exists()
    assert (run.run_dir / "social" / "instagram-post-1080x1080.png").exists()
    assert (run.run_dir / "stickers" / "telegram" / "sticker-with-outline-512.png").exists()
    assert (run.run_dir / "stickers" / "discord-emoji" / "per-pose" / "waving-128.png").exists()
    assert (run.run_dir / "print" / "cmyk-preview.tif").exists()
    assert (run.run_dir / "web" / "hero-1200w.png").exists()
    assert (run.run_dir / "web" / "webp" / "hero-1200w.webp").exists()
    assert (run.run_dir / "poses-grid.png").exists()
    assert (run.run_dir / "expressions-grid.png").exists()
    assert (run.run_dir / "README.md").exists()
    assert run.zip_path and run.zip_path.exists()
    with Image.open(run.run_dir / "print" / "cmyk-preview.tif") as image:
        assert image.mode == "CMYK"
    with Image.open(run.run_dir / "web" / "webp" / "hero-1200w.webp") as image:
        assert image.size == (1200, 675)


def _fixture_run(tmp_path: Path) -> Path:
    root = tmp_path / "source"
    (root / "poses").mkdir(parents=True)
    (root / "expressions").mkdir()
    image = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    for x in range(120, 390):
        for y in range(70, 440):
            image.putpixel((x, y), (255, 120, 20, 255))
    image.save(root / "master.png")
    image.save(root / "poses" / "waving.png")
    image.save(root / "expressions" / "happy.png")
    return root
