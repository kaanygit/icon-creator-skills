"""Sticker exports for mascot-pack."""

from __future__ import annotations

from pathlib import Path

from common import (
    MascotPackContext,
    add_white_outline,
    discover_variants,
    load_sizes,
    save_fit,
)
from PIL import Image

from shared.image_utils import save_png


def write(ctx: MascotPackContext) -> None:
    sizes = load_sizes()["stickers"]
    out = ctx.out_dir / "stickers"
    for size in sizes["imessage"]:
        save_fit(ctx.master, out / "imessage" / f"sticker-{size}.png", (size, size), max_ratio=0.9)

    telegram = int(sizes["telegram"])
    telegram_base = save_fit(
        ctx.master,
        out / "telegram" / f"sticker-{telegram}.png",
        (telegram, telegram),
        max_ratio=0.9,
    )
    with Image.open(telegram_base) as image:
        save_png(
            add_white_outline(image),
            out / "telegram" / f"sticker-with-outline-{telegram}.png",
        )

    whatsapp = int(sizes["whatsapp"])
    tray = int(sizes["whatsapp-tray"])
    save_fit(
        ctx.master,
        out / "whatsapp" / f"sticker-{whatsapp}.png",
        (whatsapp, whatsapp),
        max_ratio=0.9,
    )
    save_fit(ctx.master, out / "whatsapp" / f"tray-{tray}.png", (tray, tray), max_ratio=0.9)

    emoji = int(sizes["emoji"])
    save_fit(
        ctx.master,
        out / "discord-emoji" / f"emoji-{emoji}.png",
        (emoji, emoji),
        max_ratio=0.9,
    )
    save_fit(ctx.master, out / "slack-emoji" / f"emoji-{emoji}.png", (emoji, emoji), max_ratio=0.9)

    variants = discover_variants(ctx.variants_dir)
    for source in [*variants["poses"], *variants["expressions"]]:
        _write_variant(source, out, telegram, whatsapp, emoji)


def _write_variant(source: Path, out: Path, telegram: int, whatsapp: int, emoji: int) -> None:
    image = Image.open(source).convert("RGBA")
    stem = source.stem
    save_fit(image, out / "imessage" / "per-pose" / f"{stem}-408.png", (408, 408), max_ratio=0.9)
    base = save_fit(
        image,
        out / "telegram" / "per-pose" / f"{stem}-{telegram}.png",
        (telegram, telegram),
        max_ratio=0.9,
    )
    with Image.open(base) as opened:
        save_png(
            add_white_outline(opened),
            out / "telegram" / "per-pose" / f"{stem}-outline-{telegram}.png",
        )
    save_fit(
        image,
        out / "whatsapp" / "per-pose" / f"{stem}-{whatsapp}.png",
        (whatsapp, whatsapp),
        max_ratio=0.9,
    )
    save_fit(
        image,
        out / "discord-emoji" / "per-pose" / f"{stem}-{emoji}.png",
        (emoji, emoji),
        max_ratio=0.9,
    )
    save_fit(
        image,
        out / "slack-emoji" / "per-pose" / f"{stem}-{emoji}.png",
        (emoji, emoji),
        max_ratio=0.9,
    )
