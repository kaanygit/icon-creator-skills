"""OpenRouter image generation client."""

from __future__ import annotations

import base64
import hashlib
import json
import os
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests
import yaml
from PIL import Image

from shared.config import load_config, load_dotenv_if_present
from shared.errors import OpenRouterError
from shared.image_utils import ensure_alpha, load_image
from shared.logging_setup import JsonlLogger

PRESETS_DIR = Path(__file__).parent / "presets"
MODELS_PATH = PRESETS_DIR / "openrouter_models.yaml"
PRICING_PATH = PRESETS_DIR / "openrouter_pricing.yaml"
COST_LOG_PATH = Path("~/.icon-skills/cost-log.json").expanduser()


@dataclass(frozen=True)
class GenerateResult:
    images: list[Image.Image]
    cost_usd: float | None
    model_used: str
    fallback_used: bool
    raw_response: dict[str, Any]


class OpenRouterClient:
    """Small OpenRouter client focused on image outputs."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        config: dict[str, Any] | None = None,
        session: requests.Session | None = None,
        model_config_path: str | Path = MODELS_PATH,
        pricing_path: str | Path = PRICING_PATH,
    ) -> None:
        load_dotenv_if_present()
        self.config = config or load_config()
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY") or _read_api_key_file(self.config)
        if not self.api_key:
            raise OpenRouterError(
                "OpenRouter API key is not configured. Set OPENROUTER_API_KEY or configure "
                "openrouter.api_key_file in ~/.icon-skills/config.yaml.",
                code="auth",
            )

        self.session = session or requests.Session()
        self.models = _load_yaml(model_config_path).get("models", {})
        self.pricing = _load_yaml(pricing_path).get("models", {})
        self.session_cost_usd = 0.0

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
        """Generate one or more images."""

        if n < 1:
            raise OpenRouterError("n must be >= 1", code="invalid-input", model_attempted=model)

        fallback_chain = [model, *(fallback_models or [])]
        last_error: OpenRouterError | None = None

        for index, candidate in enumerate(fallback_chain):
            try:
                images: list[Image.Image] = []
                raw_response: dict[str, Any] = {}
                for image_index in range(n):
                    call_seed = None if seed is None else seed + image_index
                    response = self._generate_one(
                        model=candidate,
                        prompt=prompt,
                        negative_prompt=negative_prompt,
                        size=size,
                        seed=call_seed,
                        reference_image=reference_image,
                        strength=strength,
                        run_logger=run_logger,
                    )
                    raw_response = response
                    images.extend(_parse_images(response, self.session))

                cost = self._estimate_cost(candidate, n, raw_response)
                if cost is not None:
                    self.session_cost_usd += cost
                self._append_cost_log(
                    model=candidate,
                    prompt=prompt,
                    n=n,
                    cost_usd=cost,
                    skill=skill,
                )
                return GenerateResult(
                    images=images,
                    cost_usd=cost,
                    model_used=candidate,
                    fallback_used=index > 0,
                    raw_response=raw_response,
                )
            except OpenRouterError as exc:
                last_error = exc
                if exc.code not in {"model-not-found", "model-unavailable"}:
                    raise
                if run_logger:
                    next_model = (
                        fallback_chain[index + 1] if index + 1 < len(fallback_chain) else None
                    )
                    run_logger.event(
                        "fallback",
                        failed_model=candidate,
                        next_model=next_model,
                    )

        raise OpenRouterError(
            str(last_error) if last_error else "Fallback chain exhausted",
            code=last_error.code if last_error else "unknown",
            model_attempted=model,
            fallback_chain_exhausted=True,
        )

    def _generate_one(
        self,
        *,
        model: str,
        prompt: str,
        negative_prompt: str | None,
        size: tuple[int, int],
        seed: int | None,
        reference_image: str | Path | Image.Image | None,
        strength: float | None,
        run_logger: JsonlLogger | None,
    ) -> dict[str, Any]:
        self._ensure_model_usable(model, reference_image=reference_image)

        openrouter = self.config["openrouter"]
        url = f"{openrouter['base_url'].rstrip('/')}/chat/completions"
        timeout = int(openrouter["timeout_seconds"])
        max_retries = int(openrouter["max_retries"])
        payload = self._build_payload(
            model=model,
            prompt=prompt,
            negative_prompt=negative_prompt,
            size=size,
            seed=seed,
            reference_image=reference_image,
            strength=strength,
        )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": openrouter.get("http_referer", ""),
            "X-Title": openrouter.get("app_name", "icon-creator-skills"),
        }
        headers = {key: value for key, value in headers.items() if value}

        if run_logger:
            run_logger.event(
                "request",
                model=model,
                prompt_hash=_hash(prompt),
                seed=seed,
                size=f"{size[0]}x{size[1]}",
            )

        start = time.monotonic()
        for attempt in range(max_retries):
            try:
                response = self.session.post(url, headers=headers, json=payload, timeout=timeout)
            except requests.Timeout as exc:
                if attempt == max_retries - 1:
                    raise OpenRouterError("OpenRouter request timed out", code="timeout") from exc
                _sleep(attempt)
                continue
            except requests.RequestException as exc:
                if attempt == max_retries - 1:
                    raise OpenRouterError(
                        f"OpenRouter request failed: {exc}",
                        code="network",
                    ) from exc
                _sleep(attempt)
                continue

            if response.status_code in {429, 500, 502, 503, 504}:
                if attempt == max_retries - 1:
                    raise OpenRouterError(
                        f"OpenRouter transient error: {response.status_code}",
                        code="rate-limit" if response.status_code == 429 else "server",
                        model_attempted=model,
                    )
                _sleep(attempt)
                continue

            if response.status_code in {404, 410}:
                raise OpenRouterError(
                    f"OpenRouter model unavailable: {model}",
                    code="model-not-found",
                    model_attempted=model,
                )

            if response.status_code >= 400:
                raise OpenRouterError(
                    f"OpenRouter API error {response.status_code}: {response.text[:500]}",
                    code="invalid-input",
                    model_attempted=model,
                )

            data = response.json()
            if run_logger:
                run_logger.event(
                    "response",
                    model_used=model,
                    duration_ms=round((time.monotonic() - start) * 1000),
                )
            return data

        raise OpenRouterError("OpenRouter retry loop exited unexpectedly", model_attempted=model)

    def _build_payload(
        self,
        *,
        model: str,
        prompt: str,
        negative_prompt: str | None,
        size: tuple[int, int],
        seed: int | None,
        reference_image: str | Path | Image.Image | None,
        strength: float | None,
    ) -> dict[str, Any]:
        model_info = self.models.get(model, {})
        content: str | list[dict[str, Any]]
        text = prompt if not negative_prompt else f"{prompt}\n\nNegative prompt: {negative_prompt}"

        if reference_image is None:
            content = text
        else:
            content = [
                {"type": "text", "text": text},
                {"type": "image_url", "image_url": {"url": _image_to_data_url(reference_image)}},
            ]

        payload: dict[str, Any] = {
            "model": model,
            "modalities": model_info.get("default_modalities", ["image"]),
            "messages": [{"role": "user", "content": content}],
            "image_config": {"size": f"{size[0]}x{size[1]}"},
        }
        if seed is not None:
            payload["seed"] = seed
        if strength is not None:
            payload["strength"] = strength
        return payload

    def _ensure_model_usable(
        self,
        model: str,
        *,
        reference_image: str | Path | Image.Image | None,
    ) -> None:
        model_info = self.models.get(model)
        if not model_info:
            raise OpenRouterError(
                f"Model is not in openrouter_models.yaml: {model}",
                code="model-not-found",
                model_attempted=model,
            )
        if model_info.get("status") == "retired":
            raise OpenRouterError(
                f"Model is retired in openrouter_models.yaml: {model}",
                code="model-unavailable",
                model_attempted=model,
            )
        if not model_info.get("supports_text_to_image", False):
            raise OpenRouterError(
                f"Model does not support text-to-image: {model}",
                code="model-unavailable",
                model_attempted=model,
            )
        if reference_image is not None and not model_info.get("supports_image_input", False):
            raise OpenRouterError(
                f"Model does not support image input: {model}",
                code="model-unavailable",
                model_attempted=model,
            )

    def _estimate_cost(self, model: str, n: int, response: dict[str, Any]) -> float | None:
        pricing = self.pricing.get(model, {})
        per_image = pricing.get("per_image_usd")
        if per_image is not None:
            return round(float(per_image) * n, 6)

        usage = response.get("usage") or {}
        input_rate = pricing.get("input_per_million_tokens_usd")
        output_rate = pricing.get("output_per_million_tokens_usd")
        if input_rate is None or output_rate is None or not usage:
            return None

        input_tokens = usage.get("prompt_tokens", 0) or 0
        output_tokens = usage.get("completion_tokens", 0) or 0
        cost = (input_tokens / 1_000_000 * float(input_rate)) + (
            output_tokens / 1_000_000 * float(output_rate)
        )
        return round(cost, 6)

    def _append_cost_log(
        self,
        *,
        model: str,
        prompt: str,
        n: int,
        cost_usd: float | None,
        skill: str | None,
    ) -> None:
        COST_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "model": model,
            "prompt_chars": len(prompt),
            "n": n,
            "cost_usd": cost_usd,
            "skill": skill,
        }

        if COST_LOG_PATH.exists():
            with COST_LOG_PATH.open("r", encoding="utf-8") as handle:
                current = json.load(handle)
        else:
            current = []

        current.append(entry)
        with COST_LOG_PATH.open("w", encoding="utf-8") as handle:
            json.dump(current, handle, indent=2)


def _parse_images(data: dict[str, Any], session: requests.Session) -> list[Image.Image]:
    images: list[Image.Image] = []
    for choice in data.get("choices", []):
        for image_item in choice.get("message", {}).get("images", []):
            image_url = image_item.get("image_url", {}).get("url")
            if not image_url:
                continue
            images.append(_load_generated_image(image_url, session))

    if not images:
        raise OpenRouterError(
            "OpenRouter response did not include any images",
            code="invalid-response",
        )
    return images


def _load_generated_image(url: str, session: requests.Session) -> Image.Image:
    if url.startswith("data:image/"):
        _, encoded = url.split(",", 1)
        raw = base64.b64decode(encoded)
    else:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            raise OpenRouterError(
                f"Unsupported image URL scheme: {parsed.scheme}",
                code="invalid-response",
            )
        response = session.get(url, timeout=60)
        response.raise_for_status()
        raw = response.content

    with Image.open(BytesIO(raw)) as image:
        return ensure_alpha(image)


def _image_to_data_url(image: str | Path | Image.Image) -> str:
    source = load_image(image) if isinstance(image, str | Path) else image
    buffer = BytesIO()
    ensure_alpha(source).save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def _load_yaml(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def _read_api_key_file(config: dict[str, Any]) -> str | None:
    path_value = config.get("openrouter", {}).get("api_key_file")
    if not path_value:
        return None
    path = Path(str(path_value)).expanduser()
    if not path.exists():
        raise OpenRouterError(
            f"Configured OpenRouter API key file was not found: {path}",
            code="auth",
        )
    key = path.read_text(encoding="utf-8").strip()
    return key or None


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def _sleep(attempt: int) -> None:
    time.sleep(min(2**attempt, 16))
