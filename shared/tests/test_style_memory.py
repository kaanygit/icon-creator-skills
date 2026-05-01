from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

from shared.style_memory import list_styles, load_style, remove_style, save_style


def test_style_memory_roundtrip(tmp_path: Path) -> None:
    run = tmp_path / "run"
    run.mkdir()
    Image.new("RGBA", (64, 64), (255, 0, 0, 255)).save(run / "master.png")
    (run / "style-guide.md").write_text("# Style\n", encoding="utf-8")
    (run / "metadata.json").write_text(
        json.dumps({"skill": "icon-creator", "inputs": {"style-preset": "flat"}}),
        encoding="utf-8",
    )
    root = tmp_path / "styles"

    saved = save_style(run_dir=run, name="brand flat", root=root)
    loaded = load_style("brand-flat", root=root)

    assert saved.name == "brand-flat"
    assert loaded.metadata["source_skill"] == "icon-creator"
    assert (loaded.path / "style-anchor.png").exists()
    assert [style.name for style in list_styles(root=root)] == ["brand-flat"]

    remove_style("brand-flat", root=root)
    assert list_styles(root=root) == []
