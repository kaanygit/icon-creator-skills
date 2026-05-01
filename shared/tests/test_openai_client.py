from __future__ import annotations

import base64
from io import BytesIO
from pathlib import Path
from typing import Any

from PIL import Image

from shared.openai_client import OpenAIImageClient


class FakeResponse:
    status_code = 200
    text = "{}"

    def __init__(self, payload: dict[str, Any] | None = None, content: bytes = b"") -> None:
        self._payload = payload or {}
        self.content = content

    def json(self) -> dict[str, Any]:
        return self._payload

    def raise_for_status(self) -> None:
        return None


class FakeSession:
    def __init__(self, payload: dict[str, Any]) -> None:
        self.payload = payload
        self.posts: list[dict[str, Any]] = []

    def post(self, url: str, **kwargs: Any) -> FakeResponse:
        self.posts.append({"url": url, **kwargs})
        return FakeResponse(self.payload)

    def get(self, url: str, **kwargs: Any) -> FakeResponse:
        return FakeResponse(content=_png_bytes())


def test_openai_generation_posts_json_and_parses_base64(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("shared.openai_client.COST_LOG_PATH", tmp_path / "cost-log.json")
    session = FakeSession({"data": [{"b64_json": _png_base64()}]})
    client = OpenAIImageClient(api_key="test-key", config={"openai": {}}, session=session)

    result = client.generate(model="gpt-image-1", prompt="fox icon", n=1)

    assert result.images[0].size == (2, 2)
    assert session.posts[0]["url"].endswith("/images/generations")
    assert session.posts[0]["headers"]["Authorization"] == "Bearer test-key"
    assert session.posts[0]["json"]["model"] == "gpt-image-1"
    assert session.posts[0]["json"]["prompt"] == "fox icon"


def test_openai_edit_posts_multipart_reference(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("shared.openai_client.COST_LOG_PATH", tmp_path / "cost-log.json")
    session = FakeSession({"data": [{"b64_json": _png_base64()}]})
    reference = Image.new("RGBA", (2, 2), (255, 0, 0, 255))
    client = OpenAIImageClient(api_key="test-key", config={"openai": {}}, session=session)

    result = client.generate(model="gpt-image-1", prompt="fox icon", reference_image=reference)

    assert result.images[0].size == (2, 2)
    assert session.posts[0]["url"].endswith("/images/edits")
    assert "files" in session.posts[0]
    assert session.posts[0]["files"]["image"][0] == "reference.png"
    assert session.posts[0]["data"]["model"] == "gpt-image-1"


def _png_base64() -> str:
    return base64.b64encode(_png_bytes()).decode("ascii")


def _png_bytes() -> bytes:
    buffer = BytesIO()
    Image.new("RGBA", (2, 2), (10, 20, 30, 255)).save(buffer, format="PNG")
    return buffer.getvalue()
