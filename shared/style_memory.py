"""User-local style memory store."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path

from shared.errors import InputError

STYLE_ROOT = Path("~/.icon-skills/styles").expanduser()


@dataclass(frozen=True)
class SavedStyle:
    name: str
    path: Path
    metadata: dict[str, object]


def save_style(*, run_dir: str | Path, name: str, root: Path = STYLE_ROOT) -> SavedStyle:
    source = Path(run_dir)
    if not source.exists():
        raise InputError(f"Run directory not found: {source}")
    style_name = _safe_name(name)
    target = root / style_name
    target.mkdir(parents=True, exist_ok=True)

    anchor = _first_existing(
        source / "style-anchor.png",
        source / "master.png",
        source / "preview.png",
    )
    if not anchor:
        raise InputError("Could not find style-anchor.png, master.png, or preview.png in run dir")
    shutil.copy2(anchor, target / "style-anchor.png")

    guide = source / "style-guide.md"
    if guide.exists():
        shutil.copy2(guide, target / "style-guide.md")

    metadata_path = source / "metadata.json"
    metadata = (
        json.loads(metadata_path.read_text(encoding="utf-8"))
        if metadata_path.exists()
        else {}
    )
    style_metadata = {
        "name": style_name,
        "source_run": str(source),
        "source_skill": metadata.get("skill"),
        "source_inputs": metadata.get("inputs") or metadata.get("subjects"),
        "anchor": str(target / "style-anchor.png"),
    }
    (target / "metadata.json").write_text(json.dumps(style_metadata, indent=2), encoding="utf-8")
    return SavedStyle(style_name, target, style_metadata)


def list_styles(root: Path = STYLE_ROOT) -> list[SavedStyle]:
    if not root.exists():
        return []
    styles: list[SavedStyle] = []
    for item in sorted(root.iterdir()):
        metadata = item / "metadata.json"
        if item.is_dir() and metadata.exists():
            styles.append(
                SavedStyle(
                    name=item.name,
                    path=item,
                    metadata=json.loads(metadata.read_text(encoding="utf-8")),
                )
            )
    return styles


def load_style(name: str, root: Path = STYLE_ROOT) -> SavedStyle:
    style_name = _safe_name(name)
    path = root / style_name
    metadata_path = path / "metadata.json"
    if not metadata_path.exists():
        raise InputError(f"Saved style not found: {style_name}")
    return SavedStyle(
        name=style_name,
        path=path,
        metadata=json.loads(metadata_path.read_text(encoding="utf-8")),
    )


def remove_style(name: str, root: Path = STYLE_ROOT) -> None:
    style = load_style(name, root=root)
    shutil.rmtree(style.path)


def _first_existing(*paths: Path) -> Path | None:
    for path in paths:
        if path.exists():
            return path
    return None


def _safe_name(name: str) -> str:
    import re

    value = re.sub(r"[^a-zA-Z0-9._-]+", "-", name.strip()).strip("-")
    if not value:
        raise InputError("Style name cannot be empty")
    return value
