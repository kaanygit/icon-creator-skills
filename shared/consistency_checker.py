"""Lightweight image consistency scoring for mascot and icon variants."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

from PIL import Image, ImageChops, ImageFilter, ImageStat

from shared.errors import IconSkillsError
from shared.image_utils import composite_on_bg, ensure_alpha, load_image


class ConsistencyCheckerError(IconSkillsError):
    """Consistency scoring failed."""

    def __init__(self, message: str, *, code: str = "unknown") -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class ConsistencyScore:
    combined: float
    palette_similarity: float
    edge_density_similarity: float
    perceptual_hash_similarity: float
    subject_overlap: float
    face_similarity: float | None
    passed: bool
    threshold_used: float

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class ConsistencyChecker:
    """Compare candidate artwork against an anchor image."""

    def __init__(self, *, default_threshold: float = 0.80) -> None:
        self.default_threshold = default_threshold

    def score(
        self,
        candidate: Image.Image | str | Path,
        anchor: Image.Image | str | Path,
        *,
        threshold: float | None = None,
    ) -> ConsistencyScore:
        candidate_image = _normalize(candidate)
        anchor_image = _normalize(anchor)
        used_threshold = self.default_threshold if threshold is None else threshold

        palette = _palette_similarity(candidate_image, anchor_image)
        edge = _edge_density_similarity(candidate_image, anchor_image)
        phash = _hash_similarity(candidate_image, anchor_image)
        overlap = _subject_overlap(candidate_image, anchor_image)
        combined = round((palette * 0.34) + (edge * 0.22) + (phash * 0.28) + (overlap * 0.16), 4)

        return ConsistencyScore(
            combined=combined,
            palette_similarity=palette,
            edge_density_similarity=edge,
            perceptual_hash_similarity=phash,
            subject_overlap=overlap,
            face_similarity=None,
            passed=combined >= used_threshold,
            threshold_used=used_threshold,
        )

    def score_batch(
        self,
        *,
        candidates: list[Image.Image | str | Path],
        anchor: Image.Image | str | Path,
        threshold: float | None = None,
    ) -> list[ConsistencyScore]:
        return [self.score(candidate, anchor, threshold=threshold) for candidate in candidates]


def _normalize(image_or_path: Image.Image | str | Path, *, size: int = 256) -> Image.Image:
    image = load_image(image_or_path) if isinstance(image_or_path, str | Path) else image_or_path
    return composite_on_bg(ensure_alpha(image), bg_color="#FFFFFF").resize(
        (size, size),
        Image.Resampling.LANCZOS,
    )


def _palette_similarity(a: Image.Image, b: Image.Image) -> float:
    hist_a = _color_histogram(a)
    hist_b = _color_histogram(b)
    intersection = sum(min(hist_a.get(key, 0.0), hist_b.get(key, 0.0)) for key in hist_a | hist_b)
    return round(max(0.0, min(1.0, intersection)), 4)


def _color_histogram(image: Image.Image, *, bins: int = 4) -> dict[tuple[int, int, int], float]:
    rgb = image.convert("RGB").resize((96, 96), Image.Resampling.LANCZOS)
    histogram: dict[tuple[int, int, int], int] = {}
    step = 256 // bins
    for red, green, blue in _pixel_data(rgb):
        key = (red // step, green // step, blue // step)
        histogram[key] = histogram.get(key, 0) + 1
    total = rgb.width * rgb.height
    return {key: count / total for key, count in histogram.items()}


def _edge_density_similarity(a: Image.Image, b: Image.Image) -> float:
    density_a = _edge_density(a)
    density_b = _edge_density(b)
    if density_a == density_b == 0:
        return 1.0
    score = 1 - abs(density_a - density_b) / max(density_a, density_b, 0.0001)
    return round(max(0.0, min(1.0, score)), 4)


def _edge_density(image: Image.Image) -> float:
    edges = image.convert("L").filter(ImageFilter.FIND_EDGES)
    stat = ImageStat.Stat(edges)
    return round(min(1.0, (stat.mean[0] or 0) / 80), 4)


def _hash_similarity(a: Image.Image, b: Image.Image) -> float:
    hash_a = _average_hash(a)
    hash_b = _average_hash(b)
    distance = sum(left != right for left, right in zip(hash_a, hash_b, strict=True))
    return round(1 - distance / len(hash_a), 4)


def _average_hash(image: Image.Image, *, size: int = 8) -> tuple[int, ...]:
    small = image.convert("L").resize((size, size), Image.Resampling.LANCZOS)
    pixels = list(_pixel_data(small))
    average = sum(pixels) / len(pixels)
    return tuple(1 if value >= average else 0 for value in pixels)


def _subject_overlap(a: Image.Image, b: Image.Image) -> float:
    mask_a = _subject_mask(a)
    mask_b = _subject_mask(b)
    intersection = ImageChops.logical_and(mask_a, mask_b)
    union = ImageChops.logical_or(mask_a, mask_b)
    union_count = _mask_count(union)
    if union_count == 0:
        return 1.0
    return round(_mask_count(intersection) / union_count, 4)


def _subject_mask(image: Image.Image) -> Image.Image:
    gray = image.convert("L")
    background = gray.getpixel((0, 0))
    diff = gray.point(lambda value: 255 if abs(value - background) > 18 else 0)
    return diff.convert("1")


def _mask_count(mask: Image.Image) -> int:
    return sum(1 for value in _pixel_data(mask) if value)


def _pixel_data(image: Image.Image):
    if hasattr(image, "get_flattened_data"):
        return image.get_flattened_data()
    return image.getdata()
