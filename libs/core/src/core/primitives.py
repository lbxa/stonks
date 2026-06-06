from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Ticker:
    symbol: str
    exchange: str | None = None

    def normalized(self) -> str:
        symbol = self.symbol.strip().upper()
        return f"{self.exchange.strip().upper()}:{symbol}" if self.exchange else symbol


@dataclass(frozen=True)
class FiscalPeriod:
    year: int
    quarter: int | None = None

    def label(self) -> str:
        return f"{self.year}Q{self.quarter}" if self.quarter else str(self.year)


@dataclass(frozen=True)
class CurrencyAmount:
    value: Decimal
    currency: str = "USD"

    @classmethod
    def from_float(cls, value: float, currency: str = "USD") -> "CurrencyAmount":
        return cls(Decimal(str(value)), currency.upper())
