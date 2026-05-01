from __future__ import annotations

import pytest

from shared.errors import InputError
from shared.image_clients import (
    fallback_models_for_provider,
    normalize_provider,
    resolve_model_for_provider,
    resolve_provider,
)


def test_provider_aliases_and_config_provider() -> None:
    assert normalize_provider("gemini") == "google"
    assert normalize_provider("google-gemini") == "google"
    assert normalize_provider("chatgpt") == "openai"
    assert resolve_provider(config={"image_generation": {"provider": "gemini"}}) == "google"


def test_unknown_provider_fails() -> None:
    with pytest.raises(InputError, match="Unsupported image provider"):
        resolve_provider("unknown", config={})


def test_model_resolution_prefers_cli_then_config_then_prompt() -> None:
    config = {
        "openrouter": {"model": "google/gemini-2.5-flash-image"},
        "openai": {"model": "gpt-image-1"},
        "google": {"model": "gemini-2.5-flash-image"},
    }

    assert (
        resolve_model_for_provider(
            provider="openrouter",
            requested_model="sourceful/riverflow-v2-fast-preview",
            prompt_model="black-forest-labs/flux.2-pro",
            config=config,
        )
        == "sourceful/riverflow-v2-fast-preview"
    )
    assert (
        resolve_model_for_provider(
            provider="openrouter",
            requested_model=None,
            prompt_model="black-forest-labs/flux.2-pro",
            config=config,
        )
        == "google/gemini-2.5-flash-image"
    )
    assert (
        resolve_model_for_provider(
            provider="openrouter",
            requested_model=None,
            prompt_model="black-forest-labs/flux.2-pro",
            config={},
        )
        == "black-forest-labs/flux.2-pro"
    )
    assert (
        resolve_model_for_provider(
            provider="openai",
            requested_model=None,
            prompt_model="sourceful/riverflow-v2-fast-preview",
            config={},
        )
        == "gpt-image-1"
    )


def test_fallback_models_only_apply_to_openrouter() -> None:
    assert fallback_models_for_provider(
        provider="openrouter",
        requested_model=None,
        prompt_fallbacks=["model-a"],
        config={},
    ) == ["model-a"]
    assert fallback_models_for_provider(
        provider="openrouter",
        requested_model="manual-model",
        prompt_fallbacks=["model-a"],
        config={},
    ) == []
    assert fallback_models_for_provider(
        provider="google",
        requested_model=None,
        prompt_fallbacks=["model-a"],
        config={},
    ) == []
    assert fallback_models_for_provider(
        provider="openrouter",
        requested_model=None,
        prompt_fallbacks=["model-a"],
        config={"openrouter": {"fallback_models": ["configured-a", "configured-b"]}},
    ) == ["configured-a", "configured-b"]
