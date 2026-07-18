"""Fans out TickEvent to all strategies concurrently, collects Signals.
No risk or execution logic here. Implemented in Phase 4 (async fan-out).
"""

from events import Signal, TickEvent
from strategy import Strategy


async def run_strategies(
    tick: TickEvent, strategies: list[Strategy], price_history: list[float], volume_history: list[float]
) -> list[Signal]:
    signals = []
    for s in strategies:
        try:
            signals.append(s.on_tick(tick, price_history, volume_history))
        except Exception as e:
            print(f"Strategy {s.name} raised an error: {e}")
    return signals