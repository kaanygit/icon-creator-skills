import pytest

from shared.prompt_builder import PromptBuilder, PromptBuilderError


def test_build_icon_prompt_for_all_presets() -> None:
    builder = PromptBuilder()
    presets = [
        "flat",
        "gradient",
        "glass-morphism",
        "outline",
        "3d-isometric",
        "skeuomorphic",
        "neumorphic",
        "material",
        "ios-style",
    ]

    for preset in presets:
        result = builder.build(
            skill="icon-creator",
            preset=preset,
            description="minimalist mountain",
            colors=["#123456", "#ABCDEF"],
        )
        assert "minimalist mountain" in result.positive
        assert "#123456" in result.positive
        assert result.negative
        assert len(result.prompt_hash) == 16
        assert result.model_recommendation


def test_unknown_preset_raises() -> None:
    builder = PromptBuilder()

    with pytest.raises(PromptBuilderError):
        builder.build(skill="icon-creator", preset="unknown", description="fox")

