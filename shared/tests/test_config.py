from pathlib import Path

import pytest

from shared.config import deep_merge, find_project_config, load_config
from shared.errors import InputError


def test_deep_merge_nested_override() -> None:
    base = {"openrouter": {"timeout_seconds": 60, "max_retries": 5}}
    override = {"openrouter": {"timeout_seconds": 10}}

    assert deep_merge(base, override) == {
        "openrouter": {"timeout_seconds": 10, "max_retries": 5}
    }


def test_load_config_merges_defaults_project_and_overrides(tmp_path: Path) -> None:
    defaults = tmp_path / "defaults.yaml"
    project = tmp_path / ".iconrc.yaml"
    defaults.write_text(
        "openrouter:\n  timeout_seconds: 60\n  max_retries: 5\nimage:\n  size: 1024\n",
        encoding="utf-8",
    )
    project.write_text("openrouter:\n  timeout_seconds: 30\n", encoding="utf-8")

    config = load_config(
        defaults_path=defaults,
        user_config_path=None,
        project_config_path=project,
        overrides={"image": {"size": 512}},
    )

    assert config["openrouter"]["timeout_seconds"] == 30
    assert config["openrouter"]["max_retries"] == 5
    assert config["image"]["size"] == 512


def test_load_config_discovers_iconrc_json_from_nested_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    defaults = tmp_path / "defaults.yaml"
    defaults.write_text("openrouter:\n  timeout_seconds: 60\n", encoding="utf-8")
    project = tmp_path / ".iconrc.json"
    project.write_text('{"brand": {"colors": ["#111111"]}, "openrouter": {"timeout_seconds": 20}}')
    nested = tmp_path / "apps" / "web"
    nested.mkdir(parents=True)
    monkeypatch.chdir(nested)

    config = load_config(defaults_path=defaults, user_config_path=None)

    assert find_project_config(nested) == project
    assert config["brand"]["colors"] == ["#111111"]
    assert config["openrouter"]["timeout_seconds"] == 20


def test_iconrc_json_rejects_unknown_sections(tmp_path: Path) -> None:
    defaults = tmp_path / "defaults.yaml"
    defaults.write_text("openrouter:\n  timeout_seconds: 60\n", encoding="utf-8")
    project = tmp_path / ".iconrc.json"
    project.write_text('{"secrets": {"api_key": "nope"}}')

    with pytest.raises(InputError, match="Unsupported"):
        load_config(defaults_path=defaults, user_config_path=None, project_config_path=project)
