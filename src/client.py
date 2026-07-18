"""Exchange client Protocol. MockClient (Phase 1) and HyperliquidClient (Phase 9)
both implement this so downstream code never knows which one it's talking to.
"""

from typing import Protocol
from events import ExecutionReport, OrderRequest

class ExchangeClient(Protocol):
    async def get_price(self, symbol: str) -> float: ...
    async def get_orderbook(self, symbol: str) -> dict[str, object]: ...
    async def get_candles(self, symbol: str, interval: str) -> list[dict[str, object]]: ...
    async def place_order(self, order: OrderRequest) -> ExecutionReport: ...
    async def cancel_order(self, order_id: str) -> None: ...


import random

class MockClient:
    def __init__(self, start_price: float = 100.0, seed: int = 42) -> None:
        self.price = start_price
        self._rng = random.Random(seed)

    async def get_price(self, symbol: str) -> float:
        change_pct = self._rng.uniform(-0.01,0.01)
        self.price = self.price * (1 + change_pct)
        return self.price
