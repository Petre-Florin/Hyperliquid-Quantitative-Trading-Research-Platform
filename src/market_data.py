"""In-memory state store. Emits TickEvent on update. No API calls, no decisions.
Implemented in Phase 1.
"""

from events import TickEvent


class MarketData:
    def __init__(self) -> None:
        self._store: dict[str,TickEvent] = {}

    def update(self, symbol: str, price: float, volume: float, orderbook: dict[str, object]) -> TickEvent:
        tick = TickEvent(symbol=symbol,price=price,volume=volume,orderbook=orderbook)
        self._store[symbol] = tick
        return tick

    def latest(self, symbol: str) -> TickEvent | None:
        return self._store.get(symbol)
