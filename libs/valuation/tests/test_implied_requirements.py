import math

import pytest
from valuation import implied_margin_for_enterprise_value, implied_revenue_for_enterprise_value


def test_implied_revenue_for_enterprise_value() -> None:
    assert (
        implied_revenue_for_enterprise_value(
            enterprise_value=1_500.0,
            margin=0.30,
            exit_multiple=25.0,
        )
        == 200.0
    )


def test_implied_margin_for_enterprise_value() -> None:
    assert math.isclose(
        implied_margin_for_enterprise_value(
            enterprise_value=1_500.0,
            revenue=250.0,
            exit_multiple=25.0,
        ),
        0.24,
    )


@pytest.mark.parametrize(
    ("enterprise_value", "margin", "exit_multiple"),
    [
        (1_500.0, 0.0, 25.0),
        (1_500.0, -0.10, 25.0),
        (1_500.0, 0.30, 0.0),
        (1_500.0, 0.30, -10.0),
    ],
)
def test_implied_revenue_rejects_invalid_denominators(
    enterprise_value: float, margin: float, exit_multiple: float
) -> None:
    with pytest.raises(ValueError):
        implied_revenue_for_enterprise_value(enterprise_value, margin, exit_multiple)


@pytest.mark.parametrize(
    ("enterprise_value", "revenue", "exit_multiple"),
    [
        (1_500.0, 0.0, 25.0),
        (1_500.0, -100.0, 25.0),
        (1_500.0, 250.0, 0.0),
        (1_500.0, 250.0, -10.0),
    ],
)
def test_implied_margin_rejects_invalid_denominators(
    enterprise_value: float, revenue: float, exit_multiple: float
) -> None:
    with pytest.raises(ValueError):
        implied_margin_for_enterprise_value(enterprise_value, revenue, exit_multiple)
