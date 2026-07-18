"""Template for a new strategy.

Copy this file, rename it (e.g. breakout_volume.py), and rename the class inside.
It will be auto-discovered by strategy_registry.py the next time the backtest UI
or CLI scripts run — no other file needs to change.

Requirements (see strategy_registry.py for the full convention):
- `name: str` class attribute — must be unique across all strategies.
- `on_tick(tick, price_history) -> Signal` method — always return a Signal,
  never None (use action="HOLD", confidence=0.0 when there isn't enough data).
- Every constructor parameter MUST have a default value (zero-arg construction
  is required so the registry/UI can instantiate it generically).
"""

from events import Signal, TickEvent
from strategy import Strategy


class TemplateStrategy:
    name = "template"  # rename this — must be unique across strategies/

    def __init__(self, example_period: int = 10) -> None:
        self.example_period = example_period

    def on_tick(self, tick: TickEvent, price_history: list[float]) -> Signal:
        if len(price_history) < self.example_period:
            return Signal(strategy_name=self.name, symbol=tick.symbol, action="HOLD", confidence=0.0)

        # Replace this with real logic.
        return Signal(strategy_name=self.name, symbol=tick.symbol, action="HOLD", confidence=0.0)


_: Strategy = TemplateStrategy()