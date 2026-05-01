from PIL import Image

from shared.image_utils import crop_square, detect_alpha, ensure_alpha, pad_square, resize


def test_ensure_alpha_and_detect_alpha() -> None:
    image = Image.new("RGB", (10, 10), "red")
    rgba = ensure_alpha(image)

    assert rgba.mode == "RGBA"
    assert detect_alpha(rgba) is False

    rgba.putpixel((0, 0), (255, 0, 0, 0))
    assert detect_alpha(rgba) is True


def test_crop_square_center() -> None:
    image = Image.new("RGBA", (20, 10), (255, 0, 0, 255))

    cropped = crop_square(image)

    assert cropped.size == (10, 10)


def test_pad_square() -> None:
    image = Image.new("RGBA", (20, 10), (255, 0, 0, 255))

    padded = pad_square(image)

    assert padded.size == (20, 20)
    assert padded.getpixel((0, 0))[3] == 0


def test_resize() -> None:
    image = Image.new("RGBA", (20, 20), (255, 0, 0, 255))

    resized = resize(image, (5, 5))

    assert resized.size == (5, 5)

