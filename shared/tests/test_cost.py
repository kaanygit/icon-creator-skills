from __future__ import annotations

import pytest

from shared.cost import evaluate_cost
from shared.errors import CostThresholdError


def test_cost_threshold_requires_confirmation() -> None:
    decision = evaluate_cost(estimated_usd=2.0, threshold_usd=1.0)

    assert decision.requires_confirmation is True


def test_cost_yes_skips_confirmation() -> None:
    decision = evaluate_cost(estimated_usd=2.0, threshold_usd=1.0, yes=True)

    assert decision.requires_confirmation is False


def test_cost_hard_cap_blocks_without_override() -> None:
    with pytest.raises(CostThresholdError):
        evaluate_cost(estimated_usd=11.0, hard_cap_usd=10.0)
