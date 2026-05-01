from __future__ import annotations

import importlib.util
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

from PIL import Image

SCRIPT_PATH = Path(__file__).parents[1] / "scripts" / "pack.py"


def load_pack_module() -> Any:
    spec = importlib.util.spec_from_file_location("app_icon_pack", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_pack_all_platforms_from_synthetic_master(tmp_path: Path) -> None:
    pack = load_pack_module()
    master = tmp_path / "master.png"
    _write_master(master)

    run = pack.pack_icons(
        master=master,
        app_name="Peak",
        platforms=["ios", "android", "web", "macos", "watchos", "windows"],
        output_dir=tmp_path,
        bg_color="#224466",
        create_zip=True,
        timestamp=datetime(2026, 5, 1, 0, 0, 0, tzinfo=UTC),
    )

    assert run.run_dir.exists()
    assert run.zip_path and run.zip_path.exists()
    assert (run.run_dir / "README.md").exists()
    _assert_png(run.run_dir / "ios/AppIcon.appiconset/icon-1024.png", (1024, 1024))
    _assert_png(run.run_dir / "android/drawable/ic_launcher_foreground.png", (432, 432))
    _assert_png(run.run_dir / "android/drawable/ic_launcher_background.png", (432, 432))
    _assert_png(run.run_dir / "android/play-store/ic_launcher_512.png", (512, 512))
    _assert_png(run.run_dir / "web/apple-touch-icon.png", (180, 180))
    _assert_png(run.run_dir / "web/og-image.png", (1200, 630))
    _assert_png(run.run_dir / "macos/AppIcon.appiconset/icon-512@2x.png", (1024, 1024))
    _assert_png(run.run_dir / "watchos/AppIcon.appiconset/icon-watch-1024.png", (1024, 1024))
    _assert_png(run.run_dir / "windows/Wide310x150Logo.png", (310, 150))

    _assert_contents(run.run_dir / "ios/AppIcon.appiconset/Contents.json", "ios-marketing")
    _assert_contents(run.run_dir / "macos/AppIcon.appiconset/Contents.json", "mac")
    _assert_contents(run.run_dir / "watchos/AppIcon.appiconset/Contents.json", "watch")
    manifest = json.loads((run.run_dir / "web/manifest.json").read_text(encoding="utf-8"))
    assert manifest["name"] == "Peak"
    assert manifest["icons"][2]["purpose"] == "maskable"
    ElementTree.parse(run.run_dir / "web/browserconfig.xml")
    ElementTree.parse(run.run_dir / "android/mipmap-anydpi-v26/ic_launcher.xml")
    ElementTree.parse(run.run_dir / "windows/manifest-snippet.xml")

    with Image.open(run.run_dir / "web/favicon.ico") as icon:
        assert icon.size in {(16, 16), (32, 32), (48, 48)}


def test_default_platforms_are_ios_android_web(tmp_path: Path) -> None:
    pack = load_pack_module()
    master = tmp_path / "master.png"
    _write_master(master)

    run = pack.pack_icons(
        master=master,
        app_name="Default",
        output_dir=tmp_path,
        create_zip=False,
        timestamp=datetime(2026, 5, 1, 0, 0, 0, tzinfo=UTC),
    )

    assert (run.run_dir / "ios").exists()
    assert (run.run_dir / "android").exists()
    assert (run.run_dir / "web").exists()
    assert not (run.run_dir / "macos").exists()
    assert run.zip_path is None


def _write_master(path: Path) -> None:
    image = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0))
    for x in range(220, 804):
        for y in range(220, 804):
            image.putpixel((x, y), (255, 100, 20, 255))
    image.save(path)


def _assert_png(path: Path, size: tuple[int, int]) -> None:
    assert path.exists(), path
    with Image.open(path) as image:
        assert image.size == size
        assert image.format == "PNG"


def _assert_contents(path: Path, expected_idiom: str) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["info"]["author"] == "icon-creator-skills"
    assert any(image["idiom"] == expected_idiom for image in data["images"])
