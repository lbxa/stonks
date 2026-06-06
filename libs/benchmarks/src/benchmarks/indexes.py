from dataclasses import dataclass

from core import Ticker


@dataclass(frozen=True)
class Benchmark:
    name: str
    ticker: Ticker
    description: str


def default_benchmarks() -> tuple[Benchmark, ...]:
    return (
        Benchmark("S&P 500", Ticker("SPY", "NYSEARCA"), "Large-cap US equity baseline"),
        Benchmark("Nasdaq 100", Ticker("QQQ", "NASDAQ"), "Growth-heavy US equity baseline"),
        Benchmark("US Treasury Bills", Ticker("BIL", "NYSEARCA"), "Cash-like return baseline"),
    )
