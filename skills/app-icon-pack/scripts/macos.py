"""macOS app icon pack writer."""

from __future__ import annotations

from pathlib import Path

from common import PackContext, contents_json, save_resized, write_json

MACOS_IMAGES = [
    ("16x16", "1x", "icon-16.png", 16),
    ("16x16", "2x", "icon-16@2x.png", 32),
    ("32x32", "1x", "icon-32.png", 32),
    ("32x32", "2x", "icon-32@2x.png", 64),
    ("128x128", "1x", "icon-128.png", 128),
    ("128x128", "2x", "icon-128@2x.png", 256),
    ("256x256", "1x", "icon-256.png", 256),
    ("256x256", "2x", "icon-256@2x.png", 512),
    ("512x512", "1x", "icon-512.png", 512),
    ("512x512", "2x", "icon-512@2x.png", 1024),
]


def write(ctx: PackContext) -> Path:
    iconset = ctx.out_dir / "macos" / "AppIcon.appiconset"
    images = []
    for size, scale, filename, pixels in MACOS_IMAGES:
        save_resized(ctx.master, iconset / filename, pixels)
        images.append({"size": size, "idiom": "mac", "filename": filename, "scale": scale})
    write_json(iconset / "Contents.json", contents_json(images))
    ctx.warnings.append(
        "macOS icons are not auto-shaped; use a master that already has the desired "
        "rounded-square look."
    )
    return ctx.out_dir / "macos"
