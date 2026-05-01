from __future__ import annotations

from pathlib import Path

from shared.cli import _api_key_status


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
