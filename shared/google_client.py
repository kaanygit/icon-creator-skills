"""Google Gemini image generation client."""

from __future__ import annotations

import base64
import json
import os
from io import BytesIO
from pathlib import Path
from typing import Any

import requests
from PIL import Image

from shared.config import load_config, load_dotenv_if_present
from shared.errors import OpenRouterError
from shared.image_utils import ensure_alpha, load_image
from shared.logging_setup import JsonlLogger
from shared.openrouter_client import COST_LOG_PATH, GenerateResult


class GoogleImageClient:
    """Request-based Gemini generateContent image client."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        config: dict[str, Any] | None = None,
        session: requests.Session | None = None,
    ) -> None:
        load_dotenv_if_present()
        self.config = config or load_config()
        self.api_key = (
            api_key
            or os.getenv("GEMINI_API_KEY")
            or os.getenv("GOOGLE_API_KEY")
            or _read_api_key_file(self.config)
        )
        if not self.api_key:
            raise OpenRouterError(
                "Google Gemini API key is not configured. Set GEMINI_API_KEY, GOOGLE_API_KEY, "
                "or configure google.api_key_file in ~/.icon-skills/config.yaml.",
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
        del size, seed, fallback_models, strength
        text = prompt if not negative_prompt else f"{prompt}\n\nAvoid: {negative_prompt}"
        images: list[Image.Image] = []
        raw_response: dict[str, Any] = {}
        for _ in range(n):
            raw_response = self._generate_one(
                model=model,
                prompt=text,
                reference_image=reference_image,
            )
            images.extend(_parse_images(raw_response))
        self._append_cost_log(model=model, prompt=prompt, n=n, skill=skill)
        if run_logger:
            run_logger.event("response", provider="google", model_used=model)
        return GenerateResult(
            images=images,
            cost_usd=None,
            model_used=model,
            fallback_used=False,
            raw_response=raw_response,
        )

    def _generate_one(
        self,
        *,
        model: str,
        prompt: str,
        reference_image: str | Path | Image.Image | None,
    ) -> dict[str, Any]:
        base_url = self.config.get("google", {}).get(
            "base_url",
            "https://generativelanguage.googleapis.com/v1beta",
        )
        url = f"{base_url.rstrip('/')}/models/{model}:generateContent"
        payload = {
            "contents": [{"parts": _parts(prompt=prompt, reference_image=reference_image)}],
            "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]},
        }
        response = self.session.post(
            url,
            headers={"x-goog-api-key": self.api_key, "Content-Type": "application/json"},
            json=payload,
            timeout=120,
        )
        if response.status_code >= 400:
            raise OpenRouterError(
                f"Google Gemini API error {response.status_code}: {response.text[:500]}",
                code="invalid-input",
                model_attempted=model,
            )
        return response.json()

    def _append_cost_log(self, *, model: str, prompt: str, n: int, skill: str | None) -> None:
        COST_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        if COST_LOG_PATH.exists():
            current = json.loads(COST_LOG_PATH.read_text(encoding="utf-8"))
        else:
            current = []
        current.append(
            {
                "model": model,
                "provider": "google",
                "prompt_chars": len(prompt),
                "n": n,
                "cost_usd": None,
                "skill": skill,
            }
        )
        COST_LOG_PATH.write_text(json.dumps(current, indent=2), encoding="utf-8")


def _parts(
    *,
    prompt: str,
    reference_image: str | Path | Image.Image | None,
) -> list[dict[str, Any]]:
    parts: list[dict[str, Any]] = [{"text": prompt}]
    if reference_image is not None:
        parts.append(
            {
                "inline_data": {
                    "mime_type": "image/png",
                    "data": _image_base64(reference_image),
                }
            }
        )
    return parts


def _parse_images(data: dict[str, Any]) -> list[Image.Image]:
    images: list[Image.Image] = []
    for candidate in data.get("candidates", []):
        for part in candidate.get("content", {}).get("parts", []):
            inline = part.get("inlineData") or part.get("inline_data")
            if inline and inline.get("data"):
                raw = base64.b64decode(inline["data"])
                with Image.open(BytesIO(raw)) as image:
                    images.append(ensure_alpha(image))
    if not images:
        raise OpenRouterError(
            "Google Gemini response did not include any images",
            code="invalid-response",
        )
    return images


def _image_base64(image: str | Path | Image.Image) -> str:
    source = load_image(image) if isinstance(image, str | Path) else image
    buffer = BytesIO()
    ensure_alpha(source).save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("ascii")


def _read_api_key_file(config: dict[str, Any]) -> str | None:
    path_value = config.get("google", {}).get("api_key_file")
    if not path_value:
        return None
    path = Path(str(path_value)).expanduser()
    return path.read_text(encoding="utf-8").strip() if path.exists() else None
