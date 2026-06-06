from valuation import DcfInputs, discounted_cash_flow, implied_enterprise_value


def test_implied_enterprise_value() -> None:
    assert implied_enterprise_value(100, 12) == 1200


def test_discounted_cash_flow_returns_positive_enterprise_value() -> None:
    result = discounted_cash_flow(
        DcfInputs(
            free_cash_flow=100,
            growth_rate=0.05,
            discount_rate=0.10,
            terminal_growth_rate=0.025,
        )
    )
    assert result.enterprise_value > result.forecast_value > 0
