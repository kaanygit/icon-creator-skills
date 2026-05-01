"""Prompt rendering from skill presets and Jinja templates."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from shared.errors import IconSkillsError

PRESETS_DIR = Path(__file__).parent / "presets"
TEMPLATES_DIR = PRESETS_DIR / "prompt_templates"


class PromptBuilderError(IconSkillsError):
    """Prompt template or preset resolution failed."""

    def __init__(self, message: str, *, code: str = "unknown") -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class PromptResult:
    positive: str
    negative: str
    prompt_hash: str
    model_recommendation: str
    model_fallbacks: list[str]
    preset: str
    template: str


class PromptBuilder:
    """Build prompts for skill entrypoints."""

    def __init__(
        self,
        *,
        presets_dir: str | Path = PRESETS_DIR,
        templates_dir: str | Path = TEMPLATES_DIR,
    ) -> None:
        self.presets_dir = Path(presets_dir)
        self.templates_dir = Path(templates_dir)
        self.environment = Environment(
            loader=FileSystemLoader(self.templates_dir),
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def build(
        self,
        *,
        skill: str,
        preset: str,
        description: str,
        type: str = "app-icon",
        colors: list[str] | None = None,
        reference_hints: Any | None = None,
        user_extras: str | None = None,
        extra_negatives: str | None = None,
        model_override: str | None = None,
        **extra_context: Any,
    ) -> PromptResult:
        preset_config = self._load_preset(skill, preset)
        template_name = preset_config.get("template", f"{preset}.j2")
        template_path = f"{skill}/{template_name}"
        template = self._load_template(template_path, skill=skill)
        context = {
            "description": description.strip(),
            "type": type,
            "colors": colors or [],
            "reference_hints": reference_hints,
            "user_extras": user_extras,
            "extra_negatives": extra_negatives,
            "preset": preset,
            "style_phrase": preset_config.get("style_phrase", ""),
            "negative_extras": preset_config.get("negative_extras", ""),
            **extra_context,
        }

        try:
            render_context = template.new_context(context)
            positive = _normalize_prompt(_render_block(template, "positive", render_context))
            if "negative" in template.blocks:
                negative = _normalize_prompt(_render_block(template, "negative", render_context))
            else:
                default_template = self.environment.get_template(f"{skill}/_default.j2")
                default_context = default_template.new_context(context)
                negative = _normalize_prompt(
                    _render_block(default_template, "negative", default_context)
                )
        except Exception as exc:
            raise PromptBuilderError(
                f"Failed to render prompt template {template_path}: {exc}",
                code="render-failed",
            ) from exc

        if extra_negatives:
            negative = _normalize_prompt(f"{negative}, {extra_negatives}")

        model = model_override or preset_config["primary_model"]
        fallback_models = list(preset_config.get("fallback_models", []))
        if model_override:
            fallback_models = []

        prompt_hash = hashlib.sha256(f"{positive}||{negative}".encode()).hexdigest()[:16]
        return PromptResult(
            positive=positive,
            negative=negative,
            prompt_hash=prompt_hash,
            model_recommendation=model,
            model_fallbacks=fallback_models,
            preset=preset,
            template=template_path,
        )

    def _load_preset(self, skill: str, preset: str) -> dict[str, Any]:
        path = self.presets_dir / f"{skill}_styles.yaml"
        if not path.exists():
            raise PromptBuilderError(f"Preset file not found for {skill}", code="preset-unknown")

        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}

        presets = data.get(skill, {})
        if preset not in presets:
            raise PromptBuilderError(
                f"Unknown preset '{preset}' for {skill}",
                code="preset-unknown",
            )
        return presets[preset]

    def _load_template(self, template_path: str, *, skill: str):
        try:
            return self.environment.get_template(template_path)
        except TemplateNotFound:
            fallback = f"{skill}/_default.j2"
            try:
                return self.environment.get_template(fallback)
            except TemplateNotFound as exc:
                raise PromptBuilderError(
                    f"No template found for {template_path} or {fallback}",
                    code="template-not-found",
                ) from exc


def _normalize_prompt(value: str) -> str:
    return " ".join(value.replace("\n", " ").split()).strip(" ,")


def _render_block(template, block_name: str, context) -> str:
    return "".join(template.blocks[block_name](context))
