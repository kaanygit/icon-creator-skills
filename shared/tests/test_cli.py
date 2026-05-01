from __future__ import annotations

from pathlib import Path

from shared.cli import (
    _api_key_status,
    _create_command,
    _doctor_fix,
    _estimate,
    _parse_items,
    build_parser,
)


def test_api_key_status_checks_provider_environment(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    assert _api_key_status({}, "openai") == "set in environment (OPENAI_API_KEY)"


def test_api_key_status_checks_provider_key_file(tmp_path: Path) -> None:
    key_file = tmp_path / "google.key"
    key_file.write_text("test-key", encoding="utf-8")

    assert _api_key_status({"google": {"api_key_file": str(key_file)}}, "google") == (
        f"configured via {key_file}"
    )


def test_api_key_status_reports_missing_for_selected_provider() -> None:
    assert _api_key_status({}, "openrouter") == "missing"


def test_estimate_mascot_counts_variant_attempts() -> None:
    parser = build_parser()
    args = parser.parse_args(
        [
            "estimate",
            "mascot",
            "--variants",
            "1",
            "--poses",
            "idle,waving",
            "--expressions",
            "happy,curious",
            "--matrix",
            "--best-of-n",
            "2",
        ]
    )

    estimate = _estimate(args)

    assert estimate["skill"] == "mascot-creator"
    assert estimate["requests"] == 17
    assert estimate["images"] == 17


def test_create_icon_command_wraps_script() -> None:
    parser = build_parser()
    args = parser.parse_args(
        [
            "create-icon",
            "--description",
            "minimal fox",
            "--style-preset",
            "gradient",
            "--provider",
            "openrouter",
            "--model",
            "test/model",
            "--variants",
            "1",
        ]
    )

    command = _create_command(args)

    assert "skills/icon-creator/scripts/generate.py" in command[1]
    assert command[command.index("--description") + 1] == "minimal fox"
    assert command[command.index("--provider") + 1] == "openrouter"
    assert command[command.index("--model") + 1] == "test/model"


def test_parse_items_accepts_json_and_csv() -> None:
    assert _parse_items('["home", "search"]') == ["home", "search"]
    assert _parse_items("home,search") == ["home", "search"]


def test_doctor_fix_creates_user_config(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))

    _doctor_fix()

    assert (tmp_path / ".icon-skills").is_dir()
    assert (tmp_path / ".icon-skills" / "styles").is_dir()
    config = tmp_path / ".icon-skills" / "config.yaml"
    assert config.exists()
    assert "image_generation:" in config.read_text(encoding="utf-8")
