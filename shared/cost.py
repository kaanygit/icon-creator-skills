"""Cost estimation and confirmation helpers."""

from __future__ import annotations

from dataclasses import dataclass

from shared.errors import CostThresholdError


@dataclass(frozen=True)
class CostDecision:
    estimated_usd: float
    requires_confirmation: bool
    hard_cap_exceeded: bool


def evaluate_cost(
    *,
    estimated_usd: float,
    threshold_usd: float = 1.0,
    hard_cap_usd: float = 10.0,
    yes: bool = False,
    allow_large_cost: bool = False,
) -> CostDecision:
    hard_cap_exceeded = estimated_usd > hard_cap_usd and not allow_large_cost
    if hard_cap_exceeded:
        raise CostThresholdError(
            f"Estimated cost ${estimated_usd:.2f} exceeds hard cap ${hard_cap_usd:.2f}. "
            "Pass --allow-large-cost if you intentionally want to proceed."
        )
    requires = estimated_usd > threshold_usd and not yes
    return CostDecision(
        estimated_usd=estimated_usd,
        requires_confirmation=requires,
        hard_cap_exceeded=False,
    )
