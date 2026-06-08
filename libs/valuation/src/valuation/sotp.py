from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class SegmentValuation:
    name: str
    enterprise_value: float
    method: str
    notes: str = ""


@dataclass(frozen=True)
class SotpInputs:
    segments: Sequence[SegmentValuation]
    cash: float = 0.0
    debt: float = 0.0
    dilution: float = 0.0
    fully_diluted_shares: float | None = None


@dataclass(frozen=True)
class SotpResult:
    segment_value: float
    net_cash: float
    dilution: float
    equity_value: float
    value_per_share: float | None


@dataclass(frozen=True)
class MarketPremiumInputs:
    musk_premium: float = 0.0
    ai_scarcity_premium: float = 0.0
    ipo_scarcity_premium: float = 0.0
    strategic_asset_premium: float = 0.0
    governance_discount: float = 0.0
    execution_haircut: float = 0.0


@dataclass(frozen=True)
class MarketPremiumResult:
    net_premium: float
    market_value: float


@dataclass(frozen=True)
class OptionScenario:
    name: str
    probability: float
    value: float


def sotp_equity_value(inputs: SotpInputs) -> SotpResult:
    if inputs.fully_diluted_shares is not None and inputs.fully_diluted_shares <= 0:
        raise ValueError("fully_diluted_shares must be positive when provided")

    segment_value = sum(segment.enterprise_value for segment in inputs.segments)
    net_cash = inputs.cash - inputs.debt
    equity_value = segment_value + net_cash - inputs.dilution
    value_per_share = (
        equity_value / inputs.fully_diluted_shares
        if inputs.fully_diluted_shares is not None
        else None
    )
    return SotpResult(
        segment_value=segment_value,
        net_cash=net_cash,
        dilution=inputs.dilution,
        equity_value=equity_value,
        value_per_share=value_per_share,
    )


def market_premium_value(base_value: float, inputs: MarketPremiumInputs) -> MarketPremiumResult:
    net_premium = (
        inputs.musk_premium
        + inputs.ai_scarcity_premium
        + inputs.ipo_scarcity_premium
        + inputs.strategic_asset_premium
        + inputs.governance_discount
        + inputs.execution_haircut
    )
    return MarketPremiumResult(
        net_premium=net_premium,
        market_value=base_value * (1 + net_premium),
    )


def probability_weighted_option_value(scenarios: Iterable[OptionScenario]) -> float:
    scenario_list = list(scenarios)
    probability_sum = sum(scenario.probability for scenario in scenario_list)
    if round(probability_sum, 10) != 1:
        raise ValueError("scenario probabilities must sum to 1.0")
    return sum(scenario.probability * scenario.value for scenario in scenario_list)


def build_sensitivity_grid(
    row_values: Sequence[float],
    column_values: Sequence[float],
    formula: Callable[[float, float], float],
    row_name: str,
    column_name: str,
) -> pd.DataFrame:
    data = [
        [formula(row_value, column_value) for column_value in column_values]
        for row_value in row_values
    ]
    grid = pd.DataFrame(data, index=list(row_values), columns=list(column_values))
    grid.index.name = row_name
    grid.columns.name = column_name
    return grid
