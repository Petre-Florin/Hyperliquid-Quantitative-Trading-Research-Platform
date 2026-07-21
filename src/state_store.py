"""Lightweight SQLite store for live engine state — trades and equity snapshots.
No external service, no credentials, just a local file. Written by engine.py as
it runs; read by the dashboard's Live tab.
"""

import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "data" / "state.db"


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def init_db() -> None:
    conn = _connect()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            strategy_name TEXT NOT NULL,
            symbol TEXT NOT NULL,
            side TEXT NOT NULL,
            size REAL NOT NULL,
            avg_price REAL NOT NULL,
            status TEXT NOT NULL,
            cash_after REAL NOT NULL,
            executed_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS equity_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            strategy_name TEXT NOT NULL,
            cash REAL NOT NULL,
            equity REAL NOT NULL,
            recorded_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    conn.close()


def record_trade(
    strategy_name: str, symbol: str, side: str, size: float, avg_price: float,
    status: str, cash_after: float,
) -> None:
    conn = _connect()
    conn.execute(
        "INSERT INTO trades (strategy_name, symbol, side, size, avg_price, status, cash_after) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (strategy_name, symbol, side, size, avg_price, status, cash_after),
    )
    conn.commit()
    conn.close()


def record_equity_snapshot(strategy_name: str, cash: float, equity: float) -> None:
    conn = _connect()
    conn.execute(
        "INSERT INTO equity_snapshots (strategy_name, cash, equity) VALUES (?, ?, ?)",
        (strategy_name, cash, equity),
    )
    conn.commit()
    conn.close()


def get_recent_trades(limit: int = 50) -> list[dict[str, object]]:
    conn = _connect()
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM trades ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_equity_history(strategy_name: str | None = None) -> list[dict[str, object]]:
    conn = _connect()
    conn.row_factory = sqlite3.Row
    if strategy_name:
        rows = conn.execute(
            "SELECT * FROM equity_snapshots WHERE strategy_name = ? ORDER BY id ASC",
            (strategy_name,),
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM equity_snapshots ORDER BY id ASC").fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_strategy_names() -> list[str]:
    conn = _connect()
    rows = conn.execute("SELECT DISTINCT strategy_name FROM equity_snapshots").fetchall()
    conn.close()
    return [r[0] for r in rows]