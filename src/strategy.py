"""Strategy interface. All strategies implement this — stateless, no instance
attributes persisting across ticks. Implemented in Phase 2.
"""

from typing import Protocol
from events import Signal, TickEvent


class Strategy(Protocol):
    name: str

    def on_tick(
        self, tick: TickEvent, price_history: list[float], volume_history: list[float]
    ) -> Signal: ...