"""Replays historical candles as TickEvents into the SAME engine used live.
No duplicated strategy/risk/execution logic. Implemented in Phase 7.
"""

import csv
from collections.abc import Iterator

from events import TickEvent


class HistoricalClient:
    def __init__(self, prices: list[float]) -> None:
        self._prices = prices
        self._index = 0

    async def get_price(self, symbol: str) -> float:
        price = self._prices[self._index]
        self._index += 1
        return price


def load_prices_from_csv(path: str) -> list[float]:
    prices = []
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            prices.append(float(row["close"]))
    return prices


def load_candles_from_csv(path: str) -> tuple[list[float], list[float]]:
    """Returns (closes, volumes) — used for strategies that need real volume data."""
    closes: list[float] = []
    volumes: list[float] = []
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            closes.append(float(row["close"]))
            volumes.append(float(row["volume"]))
    return closes, volumes