"""OpenAI Image API client."""

from __future__ import annotations

import base64
import json
import os
from io import BytesIO
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests
from PIL import Image

from shared.config import load_config, load_dotenv_if_present
from shared.errors import OpenRouterError
from shared.image_utils import ensure_alpha, load_image
from shared.logging_setup import JsonlLogger
from shared.openrouter_client import COST_LOG_PATH, GenerateResult


class OpenAIImageClient:
    """Small request-based client for OpenAI image generation."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        config: dict[str, Any] | None = None,
        session: requests.Session | None = None,
    ) -> None:
        load_dotenv_if_present()
        self.config = config or load_config()
        self.api_key = api_key or os.getenv("OPENAI_API_KEY") or _read_api_key_file(self.config)
        if not self.api_key:
            raise OpenRouterError(
                "OpenAI API key is not configured. Set OPENAI_API_KEY or configure "
                "openai.api_key_file in ~/.icon-skills/config.yaml.",
                code="auth",
            )
        self.session = session or requests.Session()

    def generate(
        self,
        *,
        model: str,
        prompt: str,
        negative_prompt: str | None = None,
        size: tuple[int, int] = (1024, 1024),
        n: int = 1,
        seed: int | None = None,
        fallback_models: list[str] | None = None,
        reference_image: str | Path | Image.Image | None = None,
        strength: float | None = None,
        run_logger: JsonlLogger | None = None,
        skill: str | None = None,
    ) -> GenerateResult:
        del seed, fallback_models, strength
        text = prompt if not negative_prompt else f"{prompt}\n\nAvoid: {negative_prompt}"
        response = (
            self._edit(model=model, prompt=text, size=size, n=n, reference_image=reference_image)
            if reference_image is not None
            else self._generate(model=model, prompt=text, size=size, n=n)
        )
        images = _parse_images(response, self.session)
        self._append_cost_log(model=model, prompt=prompt, n=n, skill=skill)
        if run_logger:
            run_logger.event("response", provider="openai", model_used=model)
        return GenerateResult(
            images=images,
            cost_usd=None,
            model_used=model,
            fallback_used=False,
            raw_response=response,
        )

    def _generate(
        self,
        *,
        model: str,
        prompt: str,
        size: tuple[int, int],
        n: int,
    ) -> dict[str, Any]:
        url = f"{_base_url(self.config).rstrip('/')}/images/generations"
        payload = {"model": model, "prompt": prompt, "n": n, "size": f"{size[0]}x{size[1]}"}
        response = self.session.post(url, headers=_headers(self.api_key), json=payload, timeout=120)
        return _json_or_raise(response, model)

    def _edit(
        self,
        *,
        model: str,
        prompt: str,
        size: tuple[int, int],
        n: int,
        reference_image: str | Path | Image.Image | None,
    ) -> dict[str, Any]:
        url = f"{_base_url(self.config).rstrip('/')}/images/edits"
        image_bytes = _image_bytes(reference_image)
        files = {"image": ("reference.png", image_bytes, "image/png")}
        data = {"model": model, "prompt": prompt, "n": str(n), "size": f"{size[0]}x{size[1]}"}
        response = self.session.post(
            url,
            headers=_auth_header(self.api_key),
            data=data,
            files=files,
            timeout=120,
        )
        return _json_or_raise(response, model)

    def _append_cost_log(self, *, model: str, prompt: str, n: int, skill: str | None) -> None:
        COST_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        if COST_LOG_PATH.exists():
            current = json.loads(COST_LOG_PATH.read_text(encoding="utf-8"))
        else:
            current = []
        current.append(
            {
                "model": model,
                "provider": "openai",
                "prompt_chars": len(prompt),
                "n": n,
                "cost_usd": None,
                "skill": skill,
            }
        )
        COST_LOG_PATH.write_text(json.dumps(current, indent=2), encoding="utf-8")


def _parse_images(data: dict[str, Any], session: requests.Session) -> list[Image.Image]:
    images: list[Image.Image] = []
    for item in data.get("data", []):
        if item.get("b64_json"):
            raw = base64.b64decode(item["b64_json"])
            images.append(_open_image(raw))
        elif item.get("url"):
            images.append(_load_url(item["url"], session))
    if not images:
        raise OpenRouterError("OpenAI response did not include any images", code="invalid-response")
    return images


def _json_or_raise(response, model: str) -> dict[str, Any]:
    if response.status_code >= 400:
        raise OpenRouterError(
            f"OpenAI API error {response.status_code}: {response.text[:500]}",
            code="invalid-input",
            model_attempted=model,
        )
    return response.json()


def _headers(api_key: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}


def _auth_header(api_key: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {api_key}"}


def _base_url(config: dict[str, Any]) -> str:
    return config.get("openai", {}).get("base_url", "https://api.openai.com/v1")


def _read_api_key_file(config: dict[str, Any]) -> str | None:
    path_value = config.get("openai", {}).get("api_key_file")
    if not path_value:
        return None
    path = Path(str(path_value)).expanduser()
    return path.read_text(encoding="utf-8").strip() if path.exists() else None


def _image_bytes(image: str | Path | Image.Image | None) -> bytes:
    if image is None:
        raise OpenRouterError("reference_image is required for OpenAI edits", code="invalid-input")
    source = load_image(image) if isinstance(image, str | Path) else image
    buffer = BytesIO()
    ensure_alpha(source).save(buffer, format="PNG")
    return buffer.getvalue()


def _load_url(url: str, session: requests.Session) -> Image.Image:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise OpenRouterError(f"Unsupported OpenAI image URL: {url}", code="invalid-response")
    response = session.get(url, timeout=120)
    response.raise_for_status()
    return _open_image(response.content)


def _open_image(raw: bytes) -> Image.Image:
    with Image.open(BytesIO(raw)) as image:
        return ensure_alpha(image)
