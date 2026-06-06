def discount(value: float, rate: float, period: int) -> float:
    if rate <= -1:
        raise ValueError("rate must be greater than -100%")
    if period < 0:
        raise ValueError("period must be non-negative")
    return value / ((1 + rate) ** period)
