from pathlib import Path

from shared.config import deep_merge, load_config


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

