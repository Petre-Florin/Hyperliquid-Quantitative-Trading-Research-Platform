"""Core backtest engine — single source of truth, used by CLI scripts and the UI.

Also home to lightweight discovery helpers: which historical data is available on
disk, so nothing (UI or CLI) ever needs a hardcoded symbol/interval list.
"""

import statistics
from pathlib import Path
from typing import TypedDict

from backtester import HistoricalClient, load_candles_from_csv
from config import Settings
from events import TickEvent
from execution import execute_order
from risk import Portfolio, evaluate_signal
from strategy import Strategy
from strategy_runner import run_strategies

PROJECT_ROOT = Path(__file__).parent.parent

_INTERVAL_ORDER = ["1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "8h", "12h", "1d", "3d", "1w", "1M"]


class EquityRow(TypedDict):
    step: int
    price: float
    equity: float
    trade: str


def _interval_sort_key(interval: str) -> int:
    try:
        return _INTERVAL_ORDER.index(interval)
    except ValueError:
        return len(_INTERVAL_ORDER)


def discover_available_data() -> dict[str, list[str]]:
    historical_dir = PROJECT_ROOT / "data" / "historical"
    if not historical_dir.exists():
        return {}

    found: dict[str, list[str]] = {}
    for csv_file in historical_dir.glob("*.csv"):
        stem = csv_file.stem
        if "_" not in stem:
            continue
        symbol, interval = stem.rsplit("_", 1)
        found.setdefault(symbol, []).append(interval)

    for symbol in found:
        found[symbol].sort(key=_interval_sort_key)

    return found


def make_strategy(name: str) -> Strategy:
    from strategy_registry import discover_strategies

    registry = discover_strategies()
    if name not in registry:
        available = ", ".join(registry.keys()) or "(none found)"
        raise ValueError(f"Unknown strategy '{name}'. Available: {available}")
    return registry[name]()


def _compute_metrics(equity_curve: list[EquityRow]) -> dict[str, float]:
    equities = [row["equity"] for row in equity_curve]

    peak = equities[0]
    max_drawdown_pct = 0.0
    for e in equities:
        if e > peak:
            peak = e
        drawdown_pct = (e - peak) / peak * 100 if peak else 0.0
        if drawdown_pct < max_drawdown_pct:
            max_drawdown_pct = drawdown_pct

    tick_returns = [
        (equities[i] - equities[i - 1]) / equities[i - 1]
        for i in range(1, len(equities))
        if equities[i - 1] != 0
    ]
    if len(tick_returns) >= 2 and statistics.pstdev(tick_returns) != 0:
        risk_ratio = statistics.mean(tick_returns) / statistics.pstdev(tick_returns)
    else:
        risk_ratio = 0.0

    return {"max_drawdown_pct": max_drawdown_pct, "risk_ratio": risk_ratio}


async def run_backtest(
    symbol: str, interval: str, strategies: list[Strategy], starting_cash: float = 10000.0
) -> dict[str, object]:
    csv_path = PROJECT_ROOT / "data" / "historical" / f"{symbol}_{interval}.csv"
    prices, volumes = load_candles_from_csv(str(csv_path))

    client = HistoricalClient(prices)
    settings = Settings()

    per_strategy_cash = starting_cash / len(strategies)
    portfolios: dict[str, Portfolio] = {s.name: Portfolio(cash=per_strategy_cash) for s in strategies}

    price_history: list[float] = []
    volume_history: list[float] = []
    trade_count = 0
    total_fees = 0.0
    equity_curve: list[EquityRow] = []

    for i in range(len(prices)):
        price = await client.get_price(symbol)
        volume = volumes[i]
        tick = TickEvent(symbol=symbol, price=price, volume=volume, orderbook={})
        price_history.append(price)
        volume_history.append(volume)

        signals = await run_strategies(tick, strategies, price_history, volume_history)
        trade_marker = ""
        for signal in signals:
            portfolio = portfolios[signal.strategy_name]
            order = evaluate_signal(signal, portfolio, current_price=tick.price, settings=settings)
            if order is None:
                continue

            notional = order.size * tick.price
            total_fees += notional * settings.taker_fee_pct

            await execute_order(order, portfolio, current_price=tick.price, settings=settings)
            trade_count += 1
            trade_marker = order.side

        total_equity = sum(
            p.cash + p.positions.get(symbol, 0.0) * price for p in portfolios.values()
        )
        equity_curve.append({"step": i, "price": price, "equity": total_equity, "trade": trade_marker})

    final_value = equity_curve[-1]["equity"]
    net_pnl = final_value - starting_cash
    metrics = _compute_metrics(equity_curve)

    return {
        "strategy_tag": "+".join(s.name for s in strategies),
        "symbol": symbol,
        "interval": interval,
        "equity_curve": equity_curve,
        "trade_count": trade_count,
        "total_fees": total_fees,
        "final_value": final_value,
        "net_pnl": net_pnl,
        "num_ticks": len(prices),
        "portfolios": {name: {"cash": p.cash, "positions": dict(p.positions)} for name, p in portfolios.items()},
        **metrics,
    }