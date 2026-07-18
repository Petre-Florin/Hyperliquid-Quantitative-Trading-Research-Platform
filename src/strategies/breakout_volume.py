"""Breakout confirmed by volume: buys when price breaks above its recent high
AND volume spikes above its recent baseline (real conviction, not noise); sells
symmetrically on a breakdown below the recent low with a volume spike.

Note: live ticks currently carry a placeholder volume (1.0) since no live volume
feed is wired up yet (get_orderbook/get_candles in hyperliquid_client.py are still
stubs) — this strategy is only meaningful in backtests until that's built.
"""

from events import Signal, TickEvent
from indicators import volume_spike
from strategy import Strategy


class BreakoutVolumeStrategy:
    name = "breakout_volume"

    def __init__(
        self, lookback: int = 20, volume_period: int = 20, volume_threshold: float = 2.0
    ) -> None:
        self.lookback = lookback
        self.volume_period = volume_period
        self.volume_threshold = volume_threshold

    def on_tick(
        self, tick: TickEvent, price_history: list[float], volume_history: list[float]
    ) -> Signal:
        min_needed = max(self.lookback, self.volume_period) + 1
        if len(price_history) < min_needed or len(volume_history) < min_needed:
            return Signal(strategy_name=self.name, symbol=tick.symbol, action="HOLD", confidence=0.0)

        recent_high = max(price_history[-self.lookback - 1:-1])
        recent_low = min(price_history[-self.lookback - 1:-1])
        current_price = price_history[-1]
        has_spike = volume_spike(volume_history, self.volume_period, self.volume_threshold)

        metadata: dict[str, object] = {
            "recent_high": recent_high, "recent_low": recent_low, "volume_spike": has_spike,
        }

        if current_price > recent_high and has_spike:
            return Signal(strategy_name=self.name, symbol=tick.symbol, action="BUY", confidence=1.0, metadata=metadata)
        if current_price < recent_low and has_spike:
            return Signal(strategy_name=self.name, symbol=tick.symbol, action="SELL", confidence=1.0, metadata=metadata)
        return Signal(strategy_name=self.name, symbol=tick.symbol, action="HOLD", confidence=0.0, metadata=metadata)


_: Strategy = BreakoutVolumeStrategy()