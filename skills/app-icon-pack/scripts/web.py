"""Web favicon/PWA asset writer."""

from __future__ import annotations

import json
from pathlib import Path

from common import PackContext, resize_icon, save_resized

from shared.image_utils import composite_on_bg, save_png, write_ico_multires


def write(ctx: PackContext) -> Path:
    root = ctx.out_dir / "web"
    root.mkdir(parents=True, exist_ok=True)

    icons = [(size, resize_icon(ctx.master, size)) for size in (16, 32, 48)]
    write_ico_multires(root / "favicon.ico", icons)
    save_resized(ctx.master, root / "favicon-16x16.png", 16)
    save_resized(ctx.master, root / "favicon-32x32.png", 32)
    save_resized(ctx.master, root / "apple-touch-icon.png", 180, opaque=True, bg_color=ctx.bg_color)
    save_resized(ctx.master, root / "android-chrome-192x192.png", 192)
    save_resized(ctx.master, root / "android-chrome-512x512.png", 512)
    save_resized(ctx.master, root / "mstile-150x150.png", 150, opaque=True, bg_color=ctx.bg_color)
    save_png(_og_image(ctx), root / "og-image.png")
    _write_pinned_tab(root / "safari-pinned-tab.svg")
    _write_manifest(root / "manifest.json", ctx)
    _write_browserconfig(root / "browserconfig.xml", ctx)
    return root


def _write_manifest(path: Path, ctx: PackContext) -> None:
    path.write_text(
        json.dumps(
            {
                "name": ctx.app_name,
                "short_name": ctx.app_name,
                "icons": [
                    {
                        "src": "/android-chrome-192x192.png",
                        "sizes": "192x192",
                        "type": "image/png",
                    },
                    {
                        "src": "/android-chrome-512x512.png",
                        "sizes": "512x512",
                        "type": "image/png",
                        "purpose": "any",
                    },
                    {
                        "src": "/android-chrome-512x512.png",
                        "sizes": "512x512",
                        "type": "image/png",
                        "purpose": "maskable",
                    },
                ],
                "theme_color": ctx.bg_color,
                "background_color": ctx.bg_color,
                "display": "standalone",
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def _write_browserconfig(path: Path, ctx: PackContext) -> None:
    path.write_text(
        f"""<?xml version="1.0" encoding="utf-8"?>
<browserconfig>
    <msapplication>
        <tile>
            <square150x150logo src="/mstile-150x150.png"/>
            <TileColor>{ctx.bg_color}</TileColor>
        </tile>
    </msapplication>
</browserconfig>
""",
        encoding="utf-8",
    )


def _write_pinned_tab(path: Path) -> None:
    path.write_text(
        """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16">
  <rect width="16" height="16" rx="3" fill="#000000"/>
</svg>
""",
        encoding="utf-8",
    )


def _og_image(ctx: PackContext):
    canvas = composite_on_bg(ctx.master, bg_color=ctx.bg_color, size=(512, 512))
    canvas.thumbnail((420, 420))
    from PIL import Image

    output = Image.new("RGBA", (1200, 630), ctx.bg_color)
    output.alpha_composite(canvas, ((1200 - canvas.width) // 2, (630 - canvas.height) // 2))
    return output
