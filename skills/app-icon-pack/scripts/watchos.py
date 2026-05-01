"""watchOS app icon pack writer."""

from __future__ import annotations

from pathlib import Path

from common import PackContext, contents_json, has_edge_content, save_resized, write_json

WATCH_IMAGES = [
    {
        "size": "24x24",
        "scale": "2x",
        "role": "notificationCenter",
        "subtype": "38mm",
        "filename": "icon-watch-24.png",
        "pixels": 48,
    },
    {
        "size": "27.5x27.5",
        "scale": "2x",
        "role": "notificationCenter",
        "subtype": "42mm",
        "filename": "icon-watch-27.5.png",
        "pixels": 55,
    },
    {
        "size": "29x29",
        "scale": "2x",
        "role": "companionSettings",
        "filename": "icon-watch-29@2x.png",
        "pixels": 58,
    },
    {
        "size": "29x29",
        "scale": "3x",
        "role": "companionSettings",
        "filename": "icon-watch-29@3x.png",
        "pixels": 87,
    },
    {
        "size": "40x40",
        "scale": "2x",
        "role": "appLauncher",
        "subtype": "38mm",
        "filename": "icon-watch-40@2x.png",
        "pixels": 80,
    },
    {
        "size": "44x44",
        "scale": "2x",
        "role": "appLauncher",
        "subtype": "40mm",
        "filename": "icon-watch-44@2x.png",
        "pixels": 88,
    },
    {
        "size": "86x86",
        "scale": "2x",
        "role": "quickLook",
        "subtype": "38mm",
        "filename": "icon-watch-86@2x.png",
        "pixels": 172,
    },
    {
        "size": "98x98",
        "scale": "2x",
        "role": "quickLook",
        "subtype": "42mm",
        "filename": "icon-watch-98@2x.png",
        "pixels": 196,
    },
    {
        "size": "50x50",
        "scale": "2x",
        "role": "quickLook",
        "subtype": "44mm",
        "filename": "icon-watch-50@2x.png",
        "pixels": 100,
    },
    {
        "size": "1024x1024",
        "scale": "1x",
        "idiom": "watch-marketing",
        "filename": "icon-watch-1024.png",
        "pixels": 1024,
    },
]


def write(ctx: PackContext) -> Path:
    iconset = ctx.out_dir / "watchos" / "AppIcon.appiconset"
    images = []
    for entry in WATCH_IMAGES:
        filename = str(entry["filename"])
        idiom = str(entry.get("idiom", "watch"))
        save_resized(
            ctx.master,
            iconset / filename,
            int(entry["pixels"]),
            opaque=idiom == "watch-marketing",
            bg_color=ctx.bg_color,
        )
        content = {
            "size": entry["size"],
            "idiom": idiom,
            "filename": filename,
            "scale": entry["scale"],
        }
        if "role" in entry:
            content["role"] = entry["role"]
        if "subtype" in entry:
            content["subtype"] = entry["subtype"]
        images.append(content)
    write_json(iconset / "Contents.json", contents_json(images))
    if has_edge_content(ctx.master):
        ctx.warnings.append("watchOS masks icons to a circle; master has content near edges.")
    return ctx.out_dir / "watchos"
