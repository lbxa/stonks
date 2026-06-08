"""Valuation models and scenario calculations."""

from valuation.dcf import DcfInputs, DcfResult, discounted_cash_flow
from valuation.multiples import (
    implied_enterprise_value,
    implied_margin_for_enterprise_value,
    implied_revenue_for_enterprise_value,
)
from valuation.sotp import (
    MarketPremiumInputs,
    MarketPremiumResult,
    OptionScenario,
    SegmentValuation,
    SotpInputs,
    SotpResult,
    build_sensitivity_grid,
    market_premium_value,
    probability_weighted_option_value,
    sotp_equity_value,
)

__all__ = [
    "DcfInputs",
    "DcfResult",
    "MarketPremiumInputs",
    "MarketPremiumResult",
    "OptionScenario",
    "SegmentValuation",
    "SotpInputs",
    "SotpResult",
    "build_sensitivity_grid",
    "discounted_cash_flow",
    "implied_enterprise_value",
    "implied_margin_for_enterprise_value",
    "implied_revenue_for_enterprise_value",
    "market_premium_value",
    "probability_weighted_option_value",
    "sotp_equity_value",
]
