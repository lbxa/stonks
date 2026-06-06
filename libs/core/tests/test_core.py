from core import Ticker, compound_growth_rate


def test_ticker_normalizes_symbol_and_exchange() -> None:
    assert Ticker(" aapl ", " nasdaq ").normalized() == "NASDAQ:AAPL"


def test_compound_growth_rate() -> None:
    assert round(compound_growth_rate(100, 121, 2), 4) == 0.1
