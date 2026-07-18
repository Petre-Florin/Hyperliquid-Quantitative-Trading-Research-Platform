# Hyperliquid Quant

A modular, async, multi-strategy research and paper-trading framework for
Hyperliquid perpetuals — built phase-by-phase as a learning project, with
strict architectural rules: typed event contracts, pure-function indicators,
stateless strategies, and **backtest/live sharing the exact same pipeline**
(proven by an automated parity test).

**Paper trading only.** `TRADING_MODE=live` order placement is deliberately
unimplemented (`hyperliquid_client.py` raises `NotImplementedError`) until real
wallet signing and a full soak-test period are complete. Nothing here places
real orders.

## Architecture
