from dataclasses import dataclass

from valuation.discounting import discount


@dataclass(frozen=True)
class DcfInputs:
    free_cash_flow: float
    growth_rate: float
    discount_rate: float
    terminal_growth_rate: float
    years: int = 5


@dataclass(frozen=True)
class DcfResult:
    forecast_value: float
    terminal_value: float
    enterprise_value: float


def discounted_cash_flow(inputs: DcfInputs) -> DcfResult:
    if inputs.years <= 0:
        raise ValueError("years must be positive")
    if inputs.discount_rate <= inputs.terminal_growth_rate:
        raise ValueError("discount_rate must exceed terminal_growth_rate")

    forecast_value = 0.0
    current_fcf = inputs.free_cash_flow
    for year in range(1, inputs.years + 1):
        current_fcf *= 1 + inputs.growth_rate
        forecast_value += discount(current_fcf, inputs.discount_rate, year)

    terminal_cash_flow = current_fcf * (1 + inputs.terminal_growth_rate)
    terminal = terminal_cash_flow / (inputs.discount_rate - inputs.terminal_growth_rate)
    terminal_value = discount(terminal, inputs.discount_rate, inputs.years)
    return DcfResult(
        forecast_value=forecast_value,
        terminal_value=terminal_value,
        enterprise_value=forecast_value + terminal_value,
    )
