def implied_enterprise_value(metric: float, multiple: float) -> float:
    if metric < 0:
        raise ValueError("metric must be non-negative")
    if multiple < 0:
        raise ValueError("multiple must be non-negative")
    return metric * multiple


def implied_revenue_for_enterprise_value(
    enterprise_value: float, margin: float, exit_multiple: float
) -> float:
    if enterprise_value < 0:
        raise ValueError("enterprise_value must be non-negative")
    if margin <= 0:
        raise ValueError("margin must be positive")
    if exit_multiple <= 0:
        raise ValueError("exit_multiple must be positive")
    return enterprise_value / (margin * exit_multiple)


def implied_margin_for_enterprise_value(
    enterprise_value: float, revenue: float, exit_multiple: float
) -> float:
    if enterprise_value < 0:
        raise ValueError("enterprise_value must be non-negative")
    if revenue <= 0:
        raise ValueError("revenue must be positive")
    if exit_multiple <= 0:
        raise ValueError("exit_multiple must be positive")
    return enterprise_value / (revenue * exit_multiple)
