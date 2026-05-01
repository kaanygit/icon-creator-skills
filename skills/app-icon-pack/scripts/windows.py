"""Windows app icon pack writer."""

from __future__ import annotations

from pathlib import Path

from common import PackContext, centered_foreground, save_resized
from PIL import Image

from shared.image_utils import save_png

WINDOWS_IMAGES = [
    ("Square44x44Logo.png", 44),
    ("Square71x71Logo.png", 71),
    ("Square150x150Logo.png", 150),
    ("Square310x310Logo.png", 310),
    ("StoreLogo.png", 50),
]


def write(ctx: PackContext) -> Path:
    root = ctx.out_dir / "windows"
    for filename, pixels in WINDOWS_IMAGES:
        save_resized(ctx.master, root / filename, pixels)
    save_png(_wide_tile(ctx), root / "Wide310x150Logo.png")
    _write_manifest(root / "manifest-snippet.xml", ctx)
    return root


def _wide_tile(ctx: PackContext) -> Image.Image:
    subject = centered_foreground(ctx.master, canvas=150, content_max=120)
    output = Image.new("RGBA", (310, 150), (0, 0, 0, 0))
    output.alpha_composite(subject, ((310 - subject.width) // 2, 0))
    return output


def _write_manifest(path: Path, ctx: PackContext) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"""<Applications xmlns:uap="http://schemas.microsoft.com/appx/manifest/uap/windows10">
  <Application Id="App">
    <uap:VisualElements
        DisplayName="{ctx.app_name}"
        Square150x150Logo="Assets\\Square150x150Logo.png"
        Square44x44Logo="Assets\\Square44x44Logo.png"
        BackgroundColor="{ctx.bg_color}">
      <uap:DefaultTile
          Square71x71Logo="Assets\\Square71x71Logo.png"
          Square310x310Logo="Assets\\Square310x310Logo.png"
          Wide310x150Logo="Assets\\Wide310x150Logo.png" />
      <uap:SplashScreen Image="Assets\\SplashScreen.png" />
    </uap:VisualElements>
  </Application>
</Applications>
""",
        encoding="utf-8",
    )
