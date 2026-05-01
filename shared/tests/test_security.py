from __future__ import annotations

from shared.logging_setup import JsonlLogger
from shared.security import scrub_text


def test_scrub_text_redacts_openrouter_keys() -> None:
    assert "sk-or-v1" not in scrub_text("key sk-or-v1-abc123")


def test_jsonl_logger_scrubs_secrets(tmp_path) -> None:
    path = tmp_path / "log.jsonl"
    logger = JsonlLogger(path)

    logger.event("request", authorization="Bearer secret-token", api_key="sk-or-v1-abc123")

    text = path.read_text(encoding="utf-8")
    assert "secret-token" not in text
    assert "sk-or-v1" not in text
