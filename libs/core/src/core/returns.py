def compound_growth_rate(start: float, end: float, periods: float) -> float:
    if start <= 0:
        raise ValueError("start must be positive")
    if end < 0:
        raise ValueError("end must be non-negative")
    if periods <= 0:
        raise ValueError("periods must be positive")
    return (end / start) ** (1 / periods) - 1


def annualized_return(total_return: float, years: float) -> float:
    if years <= 0:
        raise ValueError("years must be positive")
    return (1 + total_return) ** (1 / years) - 1
