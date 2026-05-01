"""Print exports for mascot-pack."""

from __future__ import annotations

from common import MascotPackContext, load_sizes, save_fit
from PIL import Image


def write(ctx: MascotPackContext) -> None:
    out = ctx.out_dir / "print"
    for name, size in load_sizes()["print"].items():
        width, height = size
        path = save_fit(ctx.master, out / f"{name}.png", (width, height), max_ratio=0.72)
        with Image.open(path) as image:
            image.save(path, dpi=(300, 300))

    preview = ctx.master.convert("RGB").convert("CMYK")
    preview.thumbnail((1200, 1200), Image.Resampling.LANCZOS)
    cmyk_path = out / "cmyk-preview.tif"
    cmyk_path.parent.mkdir(parents=True, exist_ok=True)
    preview.save(cmyk_path)
    ctx.warnings.append("CMYK preview is approximate and not a substitute for print-shop proofing.")
