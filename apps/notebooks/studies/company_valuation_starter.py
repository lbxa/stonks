from benchmarks import default_benchmarks
from core import Ticker
from valuation import DcfInputs, discounted_cash_flow


def starter_study() -> dict[str, object]:
    ticker = Ticker("AAPL", "NASDAQ")
    dcf = discounted_cash_flow(
        DcfInputs(
            free_cash_flow=100_000_000_000,
            growth_rate=0.04,
            discount_rate=0.09,
            terminal_growth_rate=0.025,
        )
    )
    return {
        "ticker": ticker.normalized(),
        "enterprise_value": dcf.enterprise_value,
        "benchmarks": [benchmark.name for benchmark in default_benchmarks()],
    }


if __name__ == "__main__":
    print(starter_study())
