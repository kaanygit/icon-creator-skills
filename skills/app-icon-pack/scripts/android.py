"""Android app icon pack writer."""

from __future__ import annotations

from pathlib import Path

from common import PackContext, centered_foreground, save_resized, solid_image, white_silhouette

from shared.image_utils import save_png

ANDROID_DENSITIES = [
    ("mipmap-mdpi", 48),
    ("mipmap-hdpi", 72),
    ("mipmap-xhdpi", 96),
    ("mipmap-xxhdpi", 144),
    ("mipmap-xxxhdpi", 192),
]


def write(ctx: PackContext) -> Path:
    root = ctx.out_dir / "android"
    for directory, pixels in ANDROID_DENSITIES:
        save_resized(ctx.master, root / directory / "ic_launcher.png", pixels)

    save_png(
        centered_foreground(ctx.master, canvas=432, content_max=288),
        root / "drawable" / "ic_launcher_foreground.png",
    )
    save_png(solid_image(432, ctx.bg_color), root / "drawable" / "ic_launcher_background.png")
    save_png(white_silhouette(ctx.master, 24), root / "notification" / "ic_stat_24.png")
    save_resized(
        ctx.master,
        root / "play-store" / "ic_launcher_512.png",
        512,
        opaque=True,
        bg_color=ctx.bg_color,
    )

    adaptive = root / "mipmap-anydpi-v26" / "ic_launcher.xml"
    adaptive.parent.mkdir(parents=True, exist_ok=True)
    adaptive.write_text(
        """<?xml version="1.0" encoding="utf-8"?>
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@drawable/ic_launcher_background"/>
    <foreground android:drawable="@drawable/ic_launcher_foreground"/>
</adaptive-icon>
""",
        encoding="utf-8",
    )
    return root
