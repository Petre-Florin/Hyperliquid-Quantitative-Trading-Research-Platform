import asyncio
import csv

from events import Signal, TickEvent


class AlwaysBuyStrategy:
    name = "always_buy"

    def on_tick(self, tick: TickEvent, price_history: list[float]) -> Signal:
        return Signal(strategy_name=self.name, symbol=tick.symbol, action="BUY", confidence=1.0)


class AlwaysSellStrategy:
    name = "always_sell"

    def on_tick(self, tick: TickEvent, price_history: list[float]) -> Signal:
        return Signal(strategy_name=self.name, symbol=tick.symbol, action="SELL", confidence=1.0)


def _write_fake_csv(path, prices: list[float]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "open", "high", "low", "close", "volume"])
        for i, p in enumerate(prices):
            writer.writerow([i, p, p, p, p, 1.0])


def test_strategies_have_isolated_portfolios(tmp_path, monkeypatch):
    import backtest_core

    monkeypatch.setattr(backtest_core, "PROJECT_ROOT", tmp_path)
    _write_fake_csv(tmp_path / "data" / "historical" / "TEST_1m.csv", [100.0] * 10)

    result = asyncio.run(
        backtest_core.run_backtest("TEST", "1m", [AlwaysBuyStrategy(), AlwaysSellStrategy()])
    )

    portfolios = result["portfolios"]

    # AlwaysSellStrategy can never sell (no position, no shorting allowed) —
    # its portfolio should be completely untouched.
    assert portfolios["always_sell"]["positions"].get("TEST", 0.0) == 0.0
    assert portfolios["always_sell"]["cash"] == 5000.0  # untouched half of starting_cash

    # AlwaysBuyStrategy should have bought (once — the no-pyramiding guard blocks
    # further buys once it holds a position), independent of the other strategy.
    assert portfolios["always_buy"]["positions"].get("TEST", 0.0) > 0.0
    assert portfolios["always_buy"]["cash"] < 5000.0
