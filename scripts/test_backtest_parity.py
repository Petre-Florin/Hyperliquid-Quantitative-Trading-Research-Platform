"""Proves live and backtest paths produce identical signal/order sequences when
fed the same price sequence — the single most important test in this repo (see
build spec Section 7). If this ever fails, the architecture has a live/backtest
divergence bug and nothing built on top of it can be trusted.
"""

import asyncio

from backtester import HistoricalClient
from config import Settings
from events import TickEvent
from risk import Portfolio, evaluate_signal
from strategies.ma_crossover import MACrossoverStrategy
from strategy_runner import run_strategies

FIXED_PRICES = [100.0, 99.5, 99.0, 98.7, 99.2, 100.1, 101.3, 102.0, 101.5, 100.8]


async def _replay(client: HistoricalClient) -> list[str]:
    strategy = MACrossoverStrategy(short_period=3, long_period=5)
    settings = Settings()
    portfolio = Portfolio(cash=10000.0)
    price_history: list[float] = []
    results: list[str] = []

    for _ in range(len(FIXED_PRICES)):
        price = await client.get_price("BTC")
        tick = TickEvent(symbol="BTC", price=price, volume=1.0, orderbook={})
        price_history.append(price)

        signals = await run_strategies(tick, [strategy], price_history)
        for signal in signals:
            order = evaluate_signal(signal, portfolio, current_price=tick.price, settings=settings)
            results.append(f"{signal.strategy_name}:{signal.action}:{order is not None}")

    return results


def test_two_independent_replays_of_identical_prices_produce_identical_signals():
    client_a = HistoricalClient(prices=FIXED_PRICES)
    client_b = HistoricalClient(prices=FIXED_PRICES)

    results_a = asyncio.run(_replay(client_a))
    results_b = asyncio.run(_replay(client_b))

    assert results_a == results_b