"""Basic generated-icon quality checks."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

from PIL import Image, ImageChops, ImageFilter, ImageStat

from shared.errors import IconSkillsError
from shared.image_utils import ensure_alpha, load_image


class QualityValidatorError(IconSkillsError):
    """Quality validation failed to run."""

    def __init__(self, message: str, *, code: str = "unknown") -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class Check:
    passed: bool
    score: float
    message: str = ""


@dataclass(frozen=True)
class QualityResult:
    passed: bool
    checks: dict[str, Check]
    combined_score: float

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class QualityValidator:
    """Validate icon-like images and pick the best candidate."""

    PROFILES = {
        "app-icon": {
            "required": [
                "square_aspect",
                "centered",
                "readable_at_16px",
                "contrast",
                "non_empty",
            ],
            "optional": ["transparent_bg", "no_text_artifacts"],
        },
        "ui-icon": {
            "required": [
                "transparent_bg",
                "square_aspect",
                "centered",
                "readable_at_16px",
                "non_empty",
            ],
            "optional": ["contrast", "no_text_artifacts"],
        },
        "favicon": {
            "required": [
                "transparent_bg",
                "square_aspect",
                "readable_at_16px",
                "contrast",
                "non_empty",
            ],
            "optional": [],
        },
        "logo-mark": {
            "required": ["non_empty", "no_text_artifacts"],
            "optional": ["transparent_bg", "square_aspect"],
        },
        "mascot-master": {
            "required": ["non_empty"],
            "optional": ["transparent_bg"],
        },
    }

    def validate(
        self,
        image_or_path: Image.Image | str | Path,
        *,
        profile: str = "app-icon",
    ) -> QualityResult:
        if profile not in self.PROFILES:
            raise QualityValidatorError(f"Unknown profile: {profile}", code="profile-unknown")

        image = (
            load_image(image_or_path)
            if isinstance(image_or_path, str | Path)
            else image_or_path.copy()
        )
        rgba = ensure_alpha(image)
        bbox = _subject_bbox(rgba)
        checks = {
            "transparent_bg": _check_transparent_bg(rgba),
            "square_aspect": _check_square_aspect(rgba),
            "centered": _check_centered(rgba, bbox),
            "readable_at_16px": _check_readable_at_16px(rgba),
            "contrast": _check_contrast(rgba, bbox),
            "non_empty": _check_non_empty(rgba, bbox),
            "no_text_artifacts": _check_no_text_artifacts(rgba, bbox),
        }

        required = self.PROFILES[profile]["required"]
        passed = all(checks[name].passed for name in required)
        combined_score = round(sum(check.score for check in checks.values()) / len(checks), 4)
        return QualityResult(passed=passed, checks=checks, combined_score=combined_score)

    def pick_best(
        self,
        candidates: list[Image.Image | str | Path],
        *,
        profile: str = "app-icon",
    ) -> tuple[int, QualityResult, list[QualityResult]]:
        if not candidates:
            raise QualityValidatorError("No candidates to validate", code="invalid-input")

        results = [self.validate(candidate, profile=profile) for candidate in candidates]
        passing = [(index, result) for index, result in enumerate(results) if result.passed]
        pool = passing or list(enumerate(results))
        best_index, best_result = max(pool, key=lambda item: item[1].combined_score)
        return best_index, best_result, results


def _check_transparent_bg(image: Image.Image) -> Check:
    alpha = image.getchannel("A")
    width, height = image.size
    corners = [
        alpha.getpixel((0, 0)),
        alpha.getpixel((width - 1, 0)),
        alpha.getpixel((0, height - 1)),
        alpha.getpixel((width - 1, height - 1)),
    ]
    transparent = sum(1 for value in corners if value < 32)
    if transparent == 4:
        return Check(True, 1.0, "all corners transparent")
    if transparent >= 2:
        return Check(False, 0.5, "partially transparent corners")
    return Check(False, 0.0, "corners are opaque")


def _check_square_aspect(image: Image.Image) -> Check:
    passed = image.width == image.height
    return Check(passed, 1.0 if passed else 0.0, f"{image.width}x{image.height}")


def _check_centered(image: Image.Image, bbox: tuple[int, int, int, int] | None) -> Check:
    if bbox is None:
        return Check(False, 0.0, "no subject detected")

    left, top, right, bottom = bbox
    bbox_center_x = (left + right) / 2
    bbox_center_y = (top + bottom) / 2
    center_x = image.width / 2
    center_y = image.height / 2
    distance = (((bbox_center_x - center_x) ** 2 + (bbox_center_y - center_y) ** 2) ** 0.5) / max(
        image.size
    )
    score = round(max(0.0, 1 - 4 * distance), 4)
    return Check(score >= 0.6, score, f"center distance {distance:.3f}")


def _check_readable_at_16px(image: Image.Image) -> Check:
    small = image.resize((16, 16), Image.Resampling.LANCZOS).convert("L")
    large = small.resize((256, 256), Image.Resampling.NEAREST)
    edges = large.filter(ImageFilter.FIND_EDGES)
    edge_mean = ImageStat.Stat(edges).mean[0]
    score = round(min(1.0, edge_mean / 18), 4)
    return Check(score >= 0.25, score, f"edge mean {edge_mean:.2f}")


def _check_contrast(image: Image.Image, bbox: tuple[int, int, int, int] | None) -> Check:
    background = Image.new("RGBA", image.size, (255, 255, 255, 255))
    background.alpha_composite(image)
    region = background.crop(bbox) if bbox else background
    gray = region.convert("L")
    stddev = ImageStat.Stat(gray).stddev[0]
    if stddev < 1 and bbox:
        sample = background.getpixel((bbox[0], bbox[1]))[:3]
        bg = background.getpixel((0, 0))[:3]
        delta = sum(abs(sample[index] - bg[index]) for index in range(3)) / 3
        score = round(min(1.0, delta / 80), 4)
        return Check(score >= 0.2, score, f"foreground/background delta {delta:.2f}")
    score = round(min(1.0, stddev / 45), 4)
    return Check(score >= 0.2, score, f"luminance stddev {stddev:.2f}")


def _check_non_empty(image: Image.Image, bbox: tuple[int, int, int, int] | None) -> Check:
    if bbox is None:
        return Check(False, 0.0, "no subject detected")
    left, top, right, bottom = bbox
    area = (right - left) * (bottom - top)
    ratio = area / (image.width * image.height)
    score = round(min(1.0, ratio / 0.15), 4)
    return Check(ratio >= 0.02, score, f"subject area {ratio:.3f}")


def _check_no_text_artifacts(
    image: Image.Image,
    bbox: tuple[int, int, int, int] | None,
) -> Check:
    if bbox is None:
        return Check(True, 1.0, "no subject to scan for text")

    left, top, right, bottom = bbox
    width = right - left
    height = bottom - top
    aspect = width / max(1, height)
    height_ratio = height / image.height

    if aspect < 1.8 or height_ratio > 0.35:
        return Check(True, 1.0, "subject shape is not text-like")

    crop = image.crop(bbox).getchannel("A")
    sample_size = (min(96, max(1, width)), min(96, max(1, height)))
    mask = crop.resize(sample_size, Image.Resampling.LANCZOS)
    mask = mask.point(lambda value: 255 if value > 96 else 0)
    components = _count_components(mask)

    if components >= 3:
        score = round(max(0.0, 1 - (components - 2) * 0.25), 4)
        return Check(False, score, f"{components} glyph-like components detected")
    return Check(True, 1.0, f"{components} glyph-like components detected")


def _count_components(mask: Image.Image) -> int:
    pixels = mask.load()
    width, height = mask.size
    visited: set[tuple[int, int]] = set()
    components = 0

    for start_y in range(height):
        for start_x in range(width):
            if (start_x, start_y) in visited or pixels[start_x, start_y] == 0:
                continue

            stack = [(start_x, start_y)]
            visited.add((start_x, start_y))
            area = 0
            while stack:
                x, y = stack.pop()
                area += 1
                for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                    if (
                        0 <= nx < width
                        and 0 <= ny < height
                        and (nx, ny) not in visited
                        and pixels[nx, ny] > 0
                    ):
                        visited.add((nx, ny))
                        stack.append((nx, ny))

            if area >= 3:
                components += 1

    return components


def _subject_bbox(image: Image.Image) -> tuple[int, int, int, int] | None:
    alpha = image.getchannel("A")
    if alpha.getextrema()[0] < 250:
        return alpha.point(lambda value: 255 if value > 16 else 0).getbbox()

    background = Image.new("RGBA", image.size, image.getpixel((0, 0)))
    diff = ImageChops.difference(image, background).convert("L")
    return diff.point(lambda value: 255 if value > 12 else 0).getbbox()
