from pathlib import Path

from PIL import Image

from shared.vision_analyzer import VisionAnalyzer


def test_extract_palette_returns_hex_colors(tmp_path: Path) -> None:
    image_path = tmp_path / "palette.png"
    image = Image.new("RGBA", (20, 10), (255, 0, 0, 255))
    for x in range(10, 20):
        for y in range(10):
            image.putpixel((x, y), (0, 0, 255, 255))
    image.save(image_path)

    palette = VisionAnalyzer().extract_palette(image_path, n_colors=2)

    assert len(palette) == 2
    assert all(color.hex.startswith("#") for color in palette)


def test_analyze_style_returns_descriptor(tmp_path: Path) -> None:
    image_path = tmp_path / "reference.png"
    Image.new("RGBA", (32, 32), (0, 128, 255, 255)).save(image_path)

    hints = VisionAnalyzer().analyze_style(image_path)

    assert hints.palette
    assert hints.descriptor
    assert 0 <= hints.edge_density <= 1
    assert 0 <= hints.gradient_prevalence <= 1

