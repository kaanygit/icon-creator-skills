"""Social media exports for mascot-pack."""

from __future__ import annotations

from common import MascotPackContext, load_sizes, save_fit


def write(ctx: MascotPackContext) -> None:
    sizes = load_sizes()["social"]
    out = ctx.out_dir / "social"
    for name, size in sizes.items():
        width, height = size
        save_fit(
            ctx.master,
            out / f"{name}-{width}x{height}.png",
            (width, height),
            bg_color=ctx.bg_color,
        )
