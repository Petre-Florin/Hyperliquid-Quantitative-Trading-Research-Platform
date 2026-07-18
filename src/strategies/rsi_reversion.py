from events import Signal, TickEvent
from indicators import rsi
from strategy import Strategy


class RSIReversionStrategy:
    name = "rsi_reversion"

    def __init__(self, period: int = 14, oversold: float = 30.0, overbought: float = 70.0) -> None:
        self.period = period
        self.oversold = oversold
        self.overbought = overbought

    def on_tick(
        self, tick: TickEvent, price_history: list[float], volume_history: list[float]
    ) -> Signal:
        current_rsi = rsi(price_history, self.period)
        price_change = price_history[-1] - price_history[-2] if len(price_history) >= 2 else 0.0

        metadata: dict[str, object] = {"rsi": current_rsi, "price_change": price_change}

        if current_rsi is None:
            return Signal(strategy_name=self.name, symbol=tick.symbol, action="HOLD", confidence=0.0, metadata=metadata)
        if current_rsi < self.oversold:
            return Signal(strategy_name=self.name, symbol=tick.symbol, action="BUY", confidence=1.0, metadata=metadata)
        if current_rsi > self.overbought:
            return Signal(strategy_name=self.name, symbol=tick.symbol, action="SELL", confidence=1.0, metadata=metadata)
        return Signal(strategy_name=self.name, symbol=tick.symbol, action="HOLD", confidence=0.0, metadata=metadata)


_: Strategy = RSIReversionStrategy()