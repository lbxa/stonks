import math

import pandas as pd
from valuation import (
    MarketPremiumInputs,
    OptionScenario,
    SegmentValuation,
    SotpInputs,
    build_sensitivity_grid,
    market_premium_value,
    probability_weighted_option_value,
    sotp_equity_value,
)


def test_sotp_equity_value_bridges_segments_to_per_share_value() -> None:
    result = sotp_equity_value(
        SotpInputs(
            segments=[
                SegmentValuation("Starlink", 800.0, "DCF"),
                SegmentValuation("Launch", 150.0, "EV/EBITDA"),
            ],
            cash=75.0,
            debt=20.0,
            dilution=5.0,
            fully_diluted_shares=10.0,
        )
    )

    assert result.segment_value == 950.0
    assert result.equity_value == 1_000.0
    assert result.value_per_share == 100.0


def test_market_premium_value_applies_explicit_premiums_and_discounts() -> None:
    result = market_premium_value(
        1_000.0,
        MarketPremiumInputs(
            musk_premium=0.15,
            ai_scarcity_premium=0.10,
            ipo_scarcity_premium=0.15,
            strategic_asset_premium=0.15,
            governance_discount=-0.10,
            execution_haircut=-0.15,
        ),
    )

    assert math.isclose(result.net_premium, 0.30)
    assert math.isclose(result.market_value, 1_300.0)


def test_probability_weighted_option_value_requires_probabilities_to_sum_to_one() -> None:
    scenarios = [
        OptionScenario("Bear", 0.25, 10.0),
        OptionScenario("Base", 0.50, 40.0),
        OptionScenario("Bull", 0.25, 100.0),
    ]

    assert probability_weighted_option_value(scenarios) == 47.5


def test_sensitivity_grid_returns_expected_labeled_values() -> None:
    grid = build_sensitivity_grid(
        row_values=[100.0, 200.0],
        column_values=[0.20, 0.30],
        formula=lambda revenue, margin: revenue * margin,
        row_name="Revenue",
        column_name="Margin",
    )

    assert isinstance(grid, pd.DataFrame)
    assert list(grid.index) == [100.0, 200.0]
    assert list(grid.columns) == [0.20, 0.30]
    assert math.isclose(grid.loc[200.0, 0.30], 60.0)
