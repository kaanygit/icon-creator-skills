"""iOS app icon pack writer."""

from __future__ import annotations

from pathlib import Path

from common import PackContext, contents_json, save_resized, write_json

IOS_IMAGES = [
    ("20x20", "iphone", "2x", "icon-20@2x.png", 40),
    ("20x20", "iphone", "3x", "icon-20@3x.png", 60),
    ("29x29", "iphone", "2x", "icon-29@2x.png", 58),
    ("29x29", "iphone", "3x", "icon-29@3x.png", 87),
    ("40x40", "iphone", "2x", "icon-40@2x.png", 80),
    ("40x40", "iphone", "3x", "icon-40@3x.png", 120),
    ("60x60", "iphone", "2x", "icon-60@2x.png", 120),
    ("60x60", "iphone", "3x", "icon-60@3x.png", 180),
    ("20x20", "ipad", "1x", "icon-20.png", 20),
    ("20x20", "ipad", "2x", "icon-20@2x-ipad.png", 40),
    ("29x29", "ipad", "1x", "icon-29.png", 29),
    ("29x29", "ipad", "2x", "icon-29@2x-ipad.png", 58),
    ("40x40", "ipad", "1x", "icon-40.png", 40),
    ("40x40", "ipad", "2x", "icon-40@2x-ipad.png", 80),
    ("76x76", "ipad", "1x", "icon-76.png", 76),
    ("76x76", "ipad", "2x", "icon-76@2x.png", 152),
    ("83.5x83.5", "ipad", "2x", "icon-83.5@2x.png", 167),
    ("1024x1024", "ios-marketing", "1x", "icon-1024.png", 1024),
]


def write(ctx: PackContext) -> Path:
    iconset = ctx.out_dir / "ios" / "AppIcon.appiconset"
    images = []
    for size, idiom, scale, filename, pixels in IOS_IMAGES:
        opaque = idiom == "ios-marketing"
        save_resized(ctx.master, iconset / filename, pixels, opaque=opaque, bg_color=ctx.bg_color)
        images.append({"size": size, "idiom": idiom, "filename": filename, "scale": scale})
    write_json(iconset / "Contents.json", contents_json(images))
    return ctx.out_dir / "ios"
