from PIL import Image, ImageDraw

from shared.quality_validator import QualityValidator


def test_validator_passes_centered_transparent_icon() -> None:
    image = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
    for x in range(32, 96):
        for y in range(32, 96):
            image.putpixel((x, y), (255, 80, 0, 255))

    result = QualityValidator().validate(image)

    assert result.passed
    assert result.checks["transparent_bg"].passed
    assert result.checks["square_aspect"].passed
    assert result.checks["non_empty"].passed


def test_validator_flags_blank_image() -> None:
    image = Image.new("RGBA", (128, 128), (0, 0, 0, 0))

    result = QualityValidator().validate(image)

    assert not result.passed
    assert not result.checks["non_empty"].passed


def test_validator_flags_required_transparency_for_ui_icon() -> None:
    image = Image.new("RGBA", (128, 128), (255, 255, 255, 255))
    for x in range(32, 96):
        for y in range(32, 96):
            image.putpixel((x, y), (30, 30, 30, 255))

    result = QualityValidator().validate(image, profile="ui-icon")

    assert not result.passed
    assert not result.checks["transparent_bg"].passed


def test_validator_flags_non_square_image() -> None:
    image = Image.new("RGBA", (128, 96), (0, 0, 0, 0))
    for x in range(40, 88):
        for y in range(24, 72):
            image.putpixel((x, y), (255, 80, 0, 255))

    result = QualityValidator().validate(image)

    assert not result.passed
    assert not result.checks["square_aspect"].passed


def test_validator_flags_off_center_subject() -> None:
    image = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
    for x in range(4, 44):
        for y in range(4, 44):
            image.putpixel((x, y), (255, 80, 0, 255))

    result = QualityValidator().validate(image)

    assert not result.passed
    assert not result.checks["centered"].passed


def test_validator_flags_low_contrast_subject() -> None:
    image = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
    for x in range(32, 96):
        for y in range(32, 96):
            image.putpixel((x, y), (252, 252, 252, 255))

    result = QualityValidator().validate(image)

    assert not result.passed
    assert not result.checks["contrast"].passed


def test_validator_flags_text_like_artifacts() -> None:
    image = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.text((48, 60), "FOX", fill=(0, 0, 0, 255))

    result = QualityValidator().validate(image)

    assert not result.checks["no_text_artifacts"].passed


def test_pick_best_prefers_passing_candidate() -> None:
    blank = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
    good = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
    for x in range(32, 96):
        for y in range(32, 96):
            good.putpixel((x, y), (255, 80, 0, 255))

    index, best, results = QualityValidator().pick_best([blank, good])

    assert index == 1
    assert best.passed
    assert len(results) == 2
