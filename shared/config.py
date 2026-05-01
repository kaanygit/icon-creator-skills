"""Configuration loading and merge helpers."""

from __future__ import annotations

import copy
import json
import os
from pathlib import Path
from typing import Any

import yaml

from shared.errors import InputError

PROJECT_CONFIG = ".iconrc.yaml"
PROJECT_JSON_CONFIG = ".iconrc.json"
USER_CONFIG = "~/.icon-skills/config.yaml"
DEFAULTS_PATH = Path(__file__).parent / "presets" / "defaults.yaml"
ICONRC_SCHEMA_PATH = Path(__file__).parent / "presets" / "iconrc.schema.json"


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Return a recursive merge where override wins."""

    merged = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = copy.deepcopy(value)
    return merged


def load_yaml(path: str | Path, *, required: bool = False) -> dict[str, Any]:
    """Load a YAML mapping. Missing optional files return an empty mapping."""

    resolved = Path(path).expanduser()
    if not resolved.exists():
        if required:
            raise InputError(f"Config file not found: {resolved}")
        return {}

    with resolved.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}

    if not isinstance(data, dict):
        raise InputError(f"Config file must contain a mapping: {resolved}")
    return data


def load_mapping(path: str | Path, *, required: bool = False) -> dict[str, Any]:
    """Load a YAML or JSON mapping."""

    resolved = Path(path).expanduser()
    if not resolved.exists():
        if required:
            raise InputError(f"Config file not found: {resolved}")
        return {}
    if resolved.suffix.lower() == ".json":
        with resolved.open("r", encoding="utf-8") as handle:
            data = json.load(handle) or {}
    else:
        data = load_yaml(resolved, required=required)
    if not isinstance(data, dict):
        raise InputError(f"Config file must contain a mapping: {resolved}")
    if resolved.name == PROJECT_JSON_CONFIG:
        validate_iconrc(data)
    return data


def find_project_config(start: str | Path | None = None) -> Path | None:
    """Find `.iconrc.json` or `.iconrc.yaml` by walking up to the filesystem root."""

    current = Path(start or os.getcwd()).resolve()
    if current.is_file():
        current = current.parent

    for directory in [current, *current.parents]:
        for filename in (PROJECT_JSON_CONFIG, PROJECT_CONFIG):
            candidate = directory / filename
            if candidate.exists():
                return candidate
    return None


def load_config(
    *,
    defaults_path: str | Path = DEFAULTS_PATH,
    user_config_path: str | Path | None = USER_CONFIG,
    project_config_path: str | Path | None = None,
    overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Load defaults, user config, project config, and per-call overrides."""

    config = load_mapping(defaults_path, required=True)

    if user_config_path:
        config = deep_merge(config, load_mapping(user_config_path))

    if project_config_path is None:
        project_path = find_project_config()
    else:
        project_path = Path(project_config_path).expanduser()

    if project_path:
        config = deep_merge(config, load_mapping(project_path))

    if overrides:
        config = deep_merge(config, overrides)

    return config


def validate_iconrc(data: dict[str, Any]) -> None:
    """Validate the supported subset of `.iconrc.json` without extra dependencies."""

    allowed_top = {
        "brand",
        "defaults",
        "openrouter",
        "openai",
        "google",
        "image_generation",
        "cost",
        "image",
        "logging",
    }
    unknown = sorted(set(data) - allowed_top)
    if unknown:
        raise InputError(f"Unsupported .iconrc.json section(s): {', '.join(unknown)}")
    brand = data.get("brand")
    if brand is not None and not isinstance(brand, dict):
        raise InputError(".iconrc.json brand must be an object")
    defaults = data.get("defaults")
    if defaults is not None and not isinstance(defaults, dict):
        raise InputError(".iconrc.json defaults must be an object")


def load_dotenv_if_present(path: str | Path = ".env") -> None:
    """Load a local .env when python-dotenv is installed."""

    try:
        from dotenv import load_dotenv
    except ImportError:
        return

    load_dotenv(Path(path))
