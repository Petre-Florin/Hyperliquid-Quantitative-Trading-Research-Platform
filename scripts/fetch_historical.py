"""One-off script: fetch historical candles from Hyperliquid and save to CSV."""

import csv
import time
from pathlib import Path

from hyperliquid.info import Info
from hyperliquid.utils import constants

PROJECT_ROOT = Path(__file__).parent.parent

# How far back is actually available depends on interval, since the API caps at
# 5,000 candles total regardless of resolution. Pick a safe days_back per interval.
INTERVALS_TO_FETCH = {
    "1m": 3,      # 5000 min ≈ 3.5 days available; ask for 3 to stay safely inside it
    "3m": 10,     # 5000 * 3min ≈ 10.4 days
    "5m": 17,     # 5000 * 5min ≈ 17.4 days
    "15m": 52,    # 5000 * 15min ≈ 52 days
    "1h": 208,    # 5000 hours ≈ 208 days
}


def fetch_candles(symbol: str, interval: str, start_ms: int, end_ms: int) -> list[dict]:
    info = Info(constants.MAINNET_API_URL, skip_ws=True)
    all_candles = []
    current_start = start_ms

    while current_start < end_ms:
        batch = info.candles_snapshot(symbol, interval, current_start, end_ms)
        if not batch:
            break
        all_candles.extend(batch)
        last_time = batch[-1]["t"]
        if last_time <= current_start:
            break
        current_start = last_time + 1
        print(f"  fetched {len(all_candles)} candles so far...")
        time.sleep(0.5)

    return all_candles


def save_to_csv(candles: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "open", "high", "low", "close", "volume"])
        for c in candles:
            writer.writerow([c["t"], c["o"], c["h"], c["l"], c["c"], c["v"]])


def fetch_all_intervals(symbol: str) -> None:
    for interval, days_back in INTERVALS_TO_FETCH.items():
        print(f"\n=== Fetching {symbol} {interval} ({days_back} days back) ===")
        end_ms = int(time.time() * 1000)
        start_ms = end_ms - (days_back * 24 * 60 * 60 * 1000)

        candles = fetch_candles(symbol, interval, start_ms, end_ms)
        print(f"Total candles fetched: {len(candles)}")

        out_path = PROJECT_ROOT / "data" / "historical" / f"{symbol}_{interval}.csv"
        save_to_csv(candles, out_path)
        print(f"Saved to {out_path}")


if __name__ == "__main__":
    import sys
    symbol = sys.argv[1] if len(sys.argv) > 1 else "BTC"
    fetch_all_intervals(symbol)