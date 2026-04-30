# Shared module: `image_utils`

Image processing primitives. Resize, crop, pad, background removal, format conversion, alpha cleanup. Every skill uses some subset.

## Responsibilities

- Resize with high-quality filters (lanczos for downscale, lanczos/bicubic for upscale)
- Crop to square (center-crop default)
- Pad to square (preserve content with alpha padding)
- Background removal (rembg + heuristic alpha-edge cleanup)
- Format conversion (PNG ↔ WebP ↔ ICO ↔ AVIF)
- ICO multi-resolution writing
- SVG rasterization (cairosvg primary, resvg fallback)
- Composite operations (place mascot on a colored canvas, add stroke)
- Alpha channel utilities (detect, fix anti-alias halos, threshold)

Pure stateless functions. No skill-specific logic.

## Public API

```python
from shared.image_utils import (
    resize, crop_square, pad_square,
    remove_background, clean_alpha_edges,
    to_webp, to_ico, write_ico_multires,
    rasterize_svg,
    composite_on_bg, add_stroke,
    detect_alpha, ensure_alpha,
    color_palette_match,
)

# resize
img = resize(input_path, (512, 512), filter="lanczos")
# → PIL.Image (does not write to disk)

# square handling
img = crop_square(img)             # center-crop
img = pad_square(img, fill=(0,0,0,0))  # transparent pad

# background removal (rembg)
img = remove_background(img)       # PIL alpha-channel image
img = clean_alpha_edges(img)       # de-halo from rembg

# format
to_webp(img, "out.webp", quality=85)
write_ico_multires("favicon.ico", [(16,img), (32,img), (48,img)])

# SVG to PNG raster
img = rasterize_svg("master.svg", size=(1024, 1024))

# composite on background
img = composite_on_bg(mascot_img, bg_color="#FFFFFF")  # for white-bg variant
img = composite_on_bg(mascot_img, bg_image="gradient.png", anchor="center")

# Telegram-style sticker outline
img = add_stroke(mascot_img, color="#FFFFFF", width=8)
```

## Notable functions

### `remove_background(image, model="u2net")`

Wraps `rembg`. Three model choices for different content:
- `u2net` (default) — generic
- `u2net_human_seg` — for human/character mascots
- `silueta` — for stylized illustrations

Returns RGBA image with model-predicted mask as alpha. Auto-runs `clean_alpha_edges` after removal unless `clean_edges=False`.

### `clean_alpha_edges(image)`

`rembg` and similar tools leave anti-alias halos and stray semi-transparent pixels at the edge. This function:
- Erodes alpha by 1px (eliminates 1-pixel ghost outlines)
- Reblurs the alpha mask slightly to keep softness
- Premultiplies alpha to avoid white halos in composited renders

Idempotent on already-clean images.

### `crop_square` vs `pad_square`

- `crop_square(img, anchor="center")` — center-crop (or "top", "bottom", etc.) to make the longest side equal to the shortest.
- `pad_square(img, fill=(0,0,0,0))` — pad with a fill color (default transparent) to make the shortest side equal to the longest.

Skills choose based on input. `app-icon-pack` defaults to `crop_square` with a warning when the master is non-square; users can override.

### `rasterize_svg(path, size)`

Two-backend strategy:
1. Try `cairosvg` (most robust, requires libcairo native dep)
2. Fall back to `resvg-py` (Rust-based, simpler install on Windows)

Both return PIL.Image. Used by `app-icon-pack` for any SVG master.

### `write_ico_multires(path, [(size, image), ...])`

Pillow's ICO writer is finicky. This wrapper:
- Sorts entries by size ascending
- Verifies each image is square and PNG-encoded internally
- Handles the BMP-vs-PNG storage decision per size (PNG for ≥256, BMP otherwise)

### `color_palette_match(image, palette, tolerance=0.05)`

Checks whether the image uses (approximately) only colors from a target palette. Used by `consistency_checker` and as a quality check.

## Native dependencies

| Dep | Purpose | Install hint |
|---|---|---|
| `Pillow` | Core image ops | `pip` (always present) |
| `rembg` | Background removal | `pip install rembg[cpu]` (downloads model on first use) |
| `cairosvg` | SVG → PNG | needs `libcairo`: `brew install cairo` / `apt install libcairo2-dev` |
| `resvg-py` | SVG → PNG fallback | `pip` (statically linked) |
| `pillow-avif-plugin` | AVIF support | optional |
| `pillow-heif` | HEIF support | optional |

Each function checks its required dep at first call and raises `DependencyMissingError` with the install command if missing.

## Error model

```python
class ImageUtilsError(IconSkillsError):
    code: str   # 'unsupported-format', 'corrupt-image', 'native-dep-missing', 'rasterize-failed'
```

## Testing

- Synthetic fixtures (programmatically generated test images of known properties)
- Property-based tests for resize / pad / crop dimensions invariants
- `rembg` calls mocked in unit tests; live tests under `RUN_LIVE_TESTS=1`
- ICO output validated by reading back with multiple ICO readers

## Performance

- Operations on a 1024×1024 image complete in <100ms on commodity hardware (excluding ML-based bg removal which is ~500ms-1500ms depending on model and CPU/GPU)
- Batch operations (resizing one master into 17 sizes for iOS) parallelized via thread pool
