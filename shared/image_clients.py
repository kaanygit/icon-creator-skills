"""Provider factory for image generation clients."""

from __future__ import annotations

from typing import Any

import requests

from shared.config import load_config
from shared.errors import InputError
from shared.google_client import GoogleImageClient
from shared.openai_client import OpenAIImageClient
from shared.openrouter_client import OpenRouterClient

DEFAULT_PROVIDER = "openrouter"
DEFAULT_PROVIDER_MODELS = {
    "openrouter": "sourceful/riverflow-v2-fast-preview",
    "openai": "gpt-image-1",
    "google": "gemini-2.5-flash-image",
}


def create_image_client(
    provider: str | None = None,
    *,
    config: dict[str, Any] | None = None,
    session: requests.Session | None = None,
):
    resolved_config = config or load_config()
    normalized = resolve_provider(provider, config=resolved_config)
    if normalized == "openrouter":
        return OpenRouterClient(config=resolved_config, session=session)
    if normalized == "openai":
        return OpenAIImageClient(config=resolved_config, session=session)
    if normalized == "google":
        return GoogleImageClient(config=resolved_config, session=session)
    raise InputError(f"Unsupported image provider: {provider}")


def normalize_provider(provider: str | None) -> str:
    normalized = (provider or DEFAULT_PROVIDER).strip().lower()
    aliases = {
        "gemini": "google",
        "google-gemini": "google",
        "chatgpt": "openai",
    }
    return aliases.get(normalized, normalized)


def resolve_provider(provider: str | None = None, *, config: dict[str, Any] | None = None) -> str:
    resolved_config = config or load_config()
    configured = (resolved_config.get("image_generation") or {}).get("provider")
    normalized = normalize_provider(provider or configured or DEFAULT_PROVIDER)
    if normalized not in DEFAULT_PROVIDER_MODELS:
        raise InputError(f"Unsupported image provider: {provider or configured}")
    return normalized


def resolve_model_for_provider(
    *,
    provider: str,
    requested_model: str | None,
    prompt_model: str,
    config: dict[str, Any] | None = None,
) -> str:
    normalized = normalize_provider(provider)
    if requested_model:
        return requested_model
    configured_model = _configured_model(normalized, config or load_config())
    if configured_model:
        return configured_model
    if normalized == "openrouter" and prompt_model:
        return prompt_model
    return DEFAULT_PROVIDER_MODELS[normalized]


def fallback_models_for_provider(
    *,
    provider: str,
    prompt_fallbacks: list[str],
    requested_model: str | None,
    config: dict[str, Any] | None = None,
) -> list[str]:
    if requested_model:
        return []
    if normalize_provider(provider) == "openrouter":
        configured = _configured_fallback_models(config or load_config())
        if configured is not None:
            return configured
        return prompt_fallbacks
    return []


def _configured_model(provider: str, config: dict[str, Any]) -> str | None:
    image_generation = config.get("image_generation") or {}
    provider_models = image_generation.get("models") or {}
    model = provider_models.get(provider) or (config.get(provider) or {}).get("model")
    return str(model).strip() if model else None


def _configured_fallback_models(config: dict[str, Any]) -> list[str] | None:
    image_generation = config.get("image_generation") or {}
    values = (
        image_generation.get("openrouter_fallback_models")
        or (config.get("openrouter") or {}).get("fallback_models")
    )
    if values is None:
        return None
    if isinstance(values, str):
        return [values]
    if isinstance(values, list):
        return [str(value) for value in values if str(value).strip()]
    raise InputError("openrouter fallback model config must be a string or list")
