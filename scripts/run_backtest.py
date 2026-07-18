"""CLI entrypoint: runs every discovered strategy against one symbol/interval."""

import asyncio
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from backtest_core import run_backtest
from strategy_registry import discover_strategies

if __name__ == "__main__":
    symbol = sys.argv[1] if len(sys.argv) > 1 else "BTC"
    interval = sys.argv[2] if len(sys.argv) > 2 else "1m"

    for name, cls in discover_strategies().items():
        print(f"\n=== {name} on {symbol} {interval} ===")
        result = asyncio.run(run_backtest(symbol, interval, [cls()]))
        print(
            f"Trades: {result['trade_count']} | Net P&L: {result['net_pnl']:.2f} | "
            f"Fees: {result['total_fees']:.2f} | Max DD: {result['max_drawdown_pct']:.2f}%"
        )
