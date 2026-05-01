from __future__ import annotations

import base64
from io import BytesIO
from pathlib import Path
from typing import Any

from PIL import Image

from shared.google_client import GoogleImageClient


class FakeResponse:
    status_code = 200
    text = "{}"

    def __init__(self, payload: dict[str, Any]) -> None:
        self._payload = payload

    def json(self) -> dict[str, Any]:
        return self._payload


class FakeSession:
    def __init__(self, payload: dict[str, Any]) -> None:
        self.payload = payload
        self.posts: list[dict[str, Any]] = []

    def post(self, url: str, **kwargs: Any) -> FakeResponse:
        self.posts.append({"url": url, **kwargs})
        return FakeResponse(self.payload)


def test_google_generation_posts_generate_content_and_parses_image(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr("shared.google_client.COST_LOG_PATH", tmp_path / "cost-log.json")
    session = FakeSession(_payload("inlineData"))
    client = GoogleImageClient(api_key="test-key", config={"google": {}}, session=session)

    result = client.generate(model="gemini-2.5-flash-image", prompt="fox icon", n=1)

    assert result.images[0].size == (2, 2)
    assert session.posts[0]["url"].endswith("/models/gemini-2.5-flash-image:generateContent")
    assert session.posts[0]["headers"]["x-goog-api-key"] == "test-key"
    assert session.posts[0]["json"]["contents"][0]["parts"][0]["text"] == "fox icon"


def test_google_generation_includes_reference_image(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("shared.google_client.COST_LOG_PATH", tmp_path / "cost-log.json")
    session = FakeSession(_payload("inline_data"))
    reference = Image.new("RGBA", (2, 2), (255, 0, 0, 255))
    client = GoogleImageClient(api_key="test-key", config={"google": {}}, session=session)

    result = client.generate(
        model="gemini-2.5-flash-image",
        prompt="fox icon",
        reference_image=reference,
    )

    assert result.images[0].size == (2, 2)
    parts = session.posts[0]["json"]["contents"][0]["parts"]
    assert parts[1]["inline_data"]["mime_type"] == "image/png"
    assert parts[1]["inline_data"]["data"]


def _payload(key: str) -> dict[str, Any]:
    return {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            key: {
                                "mimeType": "image/png",
                                "data": base64.b64encode(_png_bytes()).decode("ascii"),
                            }
                        }
                    ]
                }
            }
        ]
    }


def _png_bytes() -> bytes:
    buffer = BytesIO()
    Image.new("RGBA", (2, 2), (10, 20, 30, 255)).save(buffer, format="PNG")
    return buffer.getvalue()
