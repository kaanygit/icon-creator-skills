"""Web responsive exports for mascot-pack."""

from __future__ import annotations

from common import MascotPackContext, load_sizes, save_fit, save_webp
from PIL import Image


def write(ctx: MascotPackContext, *, webp: bool = True) -> None:
    sizes = load_sizes()["web"]
    out = ctx.out_dir / "web"
    written = []
    for width in sizes["hero"]:
        path = save_fit(
            ctx.master,
            out / f"hero-{width}w.png",
            (int(width), int(width * 0.5625)),
            bg_color=ctx.bg_color,
        )
        written.append(path)
    for size in sizes["avatar"]:
        path = save_fit(
            ctx.master,
            out / f"avatar-{size}.png",
            (int(size), int(size)),
            max_ratio=0.9,
        )
        written.append(path)
    if webp:
        for path in written:
            with Image.open(path) as image:
                save_webp(image.convert("RGBA"), out / "webp" / f"{path.stem}.webp")
