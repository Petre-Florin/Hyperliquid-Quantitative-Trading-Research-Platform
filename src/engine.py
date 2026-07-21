"""Async orchestrator. Owns event queues and asyncio.gather loops.
No business logic here — this file wires together strategy_runner, risk,
and execution, but never implements their logic itself.
"""

import asyncio
import logging

from config import Settings
from events import Signal, TickEvent
from execution import execute_order
from hyperliquid_client import HyperliquidClient
from retry import retry_with_backoff
from risk import Portfolio, evaluate_signal
from strategies.ma_crossover import MACrossoverStrategy
from strategies.rsi_reversion import RSIReversionStrategy
from strategies.breakout_volume import BreakoutVolumeStrategy
from strategy import Strategy
from strategy_runner import run_strategies
from state_store import init_db, record_equity_snapshot, record_trade

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s | %(message)s",
)
logger = logging.getLogger("engine")


class Engine:
    async def start(self) -> None: ...
    async def stop(self) -> None: ...


async def market_loop(
    queue: asyncio.Queue[TickEvent | None], client: HyperliquidClient, symbol: str
) -> None:
    while True:
        price = await retry_with_backoff(lambda: client.get_price(symbol))
        tick = TickEvent(symbol=symbol, price=price, volume=1.0, orderbook={})
        await queue.put(tick)
        await asyncio.sleep(5)


async def strategy_loop(
    tick_queue: asyncio.Queue[TickEvent | None],
    signal_queue: asyncio.Queue[tuple[Signal, TickEvent] | None],
    strategies: list[Strategy],
) -> None:
    price_history: list[float] = []
    volume_history: list[float] = []
    while True:
        tick = await tick_queue.get()
        if tick is None:
            await signal_queue.put(None)
            break
        price_history.append(tick.price)
        volume_history.append(tick.volume)  # live volume is currently a placeholder (1.0)
        signals = await run_strategies(tick, strategies, price_history, volume_history)
        for signal in signals:
            await signal_queue.put((signal, tick))

async def risk_execution_loop(
    signal_queue: asyncio.Queue[tuple[Signal, TickEvent] | None],
    portfolios: dict[str, Portfolio],
    settings: Settings,
) -> None:
    while True:
        item = await signal_queue.get()
        if item is None:
            break
        signal, tick = item
        portfolio = portfolios[signal.strategy_name]

        order = evaluate_signal(signal, portfolio, current_price=tick.price, settings=settings)
        if order is None:
            logger.info(
                "tick=%s symbol=%s strategy=%s action=%s metadata=%s -> REJECTED by risk",
                tick.event_id, signal.symbol, signal.strategy_name, signal.action, signal.metadata,
            )
        else:
            report = await execute_order(order, portfolio, current_price=tick.price, settings=settings)
            logger.info(
                "tick=%s symbol=%s strategy=%s action=%s metadata=%s -> %s %.5f@%.2f (cash=%.2f)",
                tick.event_id, report.symbol, signal.strategy_name, signal.action, signal.metadata,
                report.status, report.filled_size, report.avg_price, portfolio.cash,
            )
            record_trade(
                strategy_name=signal.strategy_name, symbol=report.symbol, side=order.side,
                size=report.filled_size, avg_price=report.avg_price, status=report.status,
                cash_after=portfolio.cash,
            )

        equity = portfolio.cash + portfolio.positions.get(tick.symbol, 0.0) * tick.price
        record_equity_snapshot(signal.strategy_name, portfolio.cash, equity)


async def main() -> None:
    tick_queue: asyncio.Queue[TickEvent | None] = asyncio.Queue()
    signal_queue: asyncio.Queue[tuple[Signal, TickEvent] | None] = asyncio.Queue()

    settings = Settings()
    init_db()
    client = HyperliquidClient(settings)
    strategies: list[Strategy] = [
    MACrossoverStrategy(short_period=3, long_period=5),
    RSIReversionStrategy(),
    BreakoutVolumeStrategy(),
    ]

    starting_cash_total = 10000.0
    per_strategy_cash = starting_cash_total / len(strategies)
    portfolios: dict[str, Portfolio] = {s.name: Portfolio(cash=per_strategy_cash) for s in strategies}

    await asyncio.gather(
        market_loop(tick_queue, client, "BTC"),
        strategy_loop(tick_queue, signal_queue, strategies),
        risk_execution_loop(signal_queue, portfolios, settings),
    )

    for name, p in portfolios.items():
        print(f"{name}: {p}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutdown requested — stopping.")
