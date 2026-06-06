from benchmarks import default_benchmarks


def test_default_benchmarks_include_equity_and_cash_baselines() -> None:
    names = {benchmark.name for benchmark in default_benchmarks()}
    assert {"S&P 500", "Nasdaq 100", "US Treasury Bills"} <= names
