def implied_enterprise_value(metric: float, multiple: float) -> float:
    if metric < 0:
        raise ValueError("metric must be non-negative")
    if multiple < 0:
        raise ValueError("multiple must be non-negative")
    return metric * multiple
