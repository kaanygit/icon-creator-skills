"""Project-wide exception hierarchy."""


class IconSkillsError(Exception):
    """Base class for all expected project errors."""


class OpenRouterError(IconSkillsError):
    """OpenRouter API, model, authentication, or response parsing failure."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "unknown",
        model_attempted: str | None = None,
        fallback_chain_exhausted: bool = False,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.model_attempted = model_attempted
        self.fallback_chain_exhausted = fallback_chain_exhausted


class DependencyMissingError(IconSkillsError):
    """A required optional/native dependency is missing."""


class ValidationError(IconSkillsError):
    """Validation failed for user input or generated output."""


class InputError(IconSkillsError):
    """The user supplied invalid or incomplete input."""


class CostThresholdError(IconSkillsError):
    """A generation call would exceed a configured cost threshold."""

