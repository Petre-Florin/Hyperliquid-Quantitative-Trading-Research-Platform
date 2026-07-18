from events import Signal, TickEvent
from indicators import moving_average
from strategy import Strategy


class MACrossoverStrategy:
    name = "ma_crossover"

    def __init__(self, short_period: int = 3, long_period: int = 5) -> None:
        self.short_period = short_period
        self.long_period = long_period

    def on_tick(
        self, tick: TickEvent, price_history: list[float], volume_history: list[float]
    ) -> Signal:
        if len(price_history) < self.short_period or len(price_history) < self.long_period:
            return Signal(strategy_name=self.name, symbol=tick.symbol, action="HOLD", confidence=0.0)

        short_ma = moving_average(price_history, self.short_period)
        long_ma = moving_average(price_history, self.long_period)

        assert short_ma is not None
        assert long_ma is not None

        if short_ma > long_ma:
            return Signal(strategy_name=self.name, symbol=tick.symbol, action="BUY", confidence=1.0)
        if short_ma < long_ma:
            return Signal(strategy_name=self.name, symbol=tick.symbol, action="SELL", confidence=1.0)
        return Signal(strategy_name=self.name, symbol=tick.symbol, action="HOLD", confidence=1.0)


_: Strategy = MACrossoverStrategy()