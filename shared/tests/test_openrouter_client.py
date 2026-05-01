from __future__ import annotations

import base64
from io import BytesIO
from pathlib import Path
from typing import Any

import pytest
from PIL import Image

from shared.errors import OpenRouterError
from shared.openrouter_client import OpenRouterClient


class FakeResponse:
    def __init__(
        self,
        status_code: int,
        data: dict[str, Any] | None = None,
        text: str = "",
    ) -> None:
        self.status_code = status_code
        self._data = data or {}
        self.text = text
        self.content = b""

    def json(self) -> dict[str, Any]:
        return self._data


class FakeSession:
    def __init__(self, responses: list[FakeResponse]) -> None:
        self.responses = responses
        self.posts: list[dict[str, Any]] = []

    def post(self, url: str, **kwargs: Any) -> FakeResponse:
        self.posts.append({"url": url, **kwargs})
        return self.responses.pop(0)


def test_generate_parses_openrouter_image_response(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("shared.openrouter_client.COST_LOG_PATH", tmp_path / "cost-log.json")
    session = FakeSession([FakeResponse(200, _image_response())])
    client = OpenRouterClient(api_key="test-key", session=session)

    result = client.generate(
        model="google/gemini-3.1-flash-image-preview",
        prompt="fox",
        n=1,
        skill="test",
    )

    assert len(result.images) == 1
    assert result.images[0].size == (2, 2)
    assert result.model_used == "google/gemini-3.1-flash-image-preview"
    assert result.cost_usd is None
    payload = session.posts[0]["json"]
    assert payload["modalities"] == ["image", "text"]
    assert payload["messages"][0]["content"] == "fox"


def test_retired_model_falls_back(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("shared.openrouter_client.COST_LOG_PATH", tmp_path / "cost-log.json")
    session = FakeSession([FakeResponse(200, _image_response())])
    client = OpenRouterClient(api_key="test-key", session=session)

    result = client.generate(
        model="openai/dall-e-3",
        fallback_models=["google/gemini-3.1-flash-image-preview"],
        prompt="fox",
    )

    assert result.fallback_used is True
    assert result.model_used == "google/gemini-3.1-flash-image-preview"


def test_missing_images_raises(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("shared.openrouter_client.COST_LOG_PATH", tmp_path / "cost-log.json")
    session = FakeSession([FakeResponse(200, {"choices": [{"message": {}}]})])
    client = OpenRouterClient(api_key="test-key", session=session)

    with pytest.raises(OpenRouterError, match="did not include any images"):
        client.generate(model="google/gemini-3.1-flash-image-preview", prompt="fox")


def _image_response() -> dict[str, Any]:
    image = Image.new("RGBA", (2, 2), (255, 0, 0, 255))
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    data_url = "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode("ascii")
    return {"choices": [{"message": {"images": [{"image_url": {"url": data_url}}]}}]}
