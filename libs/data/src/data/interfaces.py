from dataclasses import dataclass
from datetime import date
from typing import Protocol

import pandas as pd
from core import Ticker


@dataclass(frozen=True)
class PriceRequest:
    ticker: Ticker
    start: date
    end: date
    interval: str = "1d"


class PriceProvider(Protocol):
    def prices(self, request: PriceRequest) -> pd.DataFrame:
        """Return prices indexed by date with adjusted close when available."""


class FundamentalsProvider(Protocol):
    def fundamentals(self, ticker: Ticker) -> pd.DataFrame:
        """Return normalized company fundamentals by fiscal period."""
