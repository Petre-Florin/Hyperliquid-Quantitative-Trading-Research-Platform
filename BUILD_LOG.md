# Build Log

## Phase 0 — Scaffolding (COMPLETE)
- Folder structure created (src-layout).
- `pyproject.toml`: pytest, mypy (strict), ruff (line-length 100) configured.
- `.env.example` documents mode + risk + Hyperliquid vars (unpopulated until Phase 8/9).
- `events.py` written in full per spec Section 3 — this is a locked contract, not a stub.
- All other `src/` modules are **signature-only stubs** (bodies are `...`), matching the
  Module Contracts table in Section 4. No logic exists yet.
- Git initialized.

**Locked decisions:**
- None yet beyond the contracts already fixed in the spec itself.

**Deferred:**
- Everything past scaffolding. Phase 1 is next: MockClient, MarketData, indicators.

**Verify:**
```
cd hyperliquid_quant
pip install -e ".[dev]"
pytest            # should collect 0 tests, exit clean
mypy src/          # should pass against stub signatures
```

---

## Phases 1–8 — Foundation through hardening (COMPLETE)

### Phase 1 — Foundation
- `indicators.py`: `returns`, `moving_average`, `ema` implemented as pure loop-based functions.
- `client.py`: `MockClient` — random-walk price generator using `random.Random(seed)` (isolated
  instance RNG, not the global `random` module, for reproducibility).
- `market_data.py`: `MarketData` — dict-of-`TickEvent` store, keyed by symbol.

### Phase 2 — First strategy
- `strategy.py`: `Strategy` Protocol (interface only — no implementations live here).
- `strategies/ma_crossover.py`: `MACrossoverStrategy`. Always returns a real `Signal` (never
  `None`) — insufficient data returns `HOLD` with `confidence=0.0`, per the Protocol contract.
- Every strategy file ends with a throwaway type-check line (`_: Strategy = SomeStrategy()`) so
  mypy actually verifies Protocol compliance instead of just implying it via import.

### Phase 3 — Async engine skeleton
- `engine.py`: `market_loop` (producer) → `strategy_loop` (consumer) over `asyncio.Queue`.
- Deliberately reproduced the `time.sleep()` vs `await asyncio.sleep()` blocking bug — confirmed
  `time.sleep()` freezes the whole event loop, not just the coroutine that calls it.
- Clean shutdown via `None` sentinel on the queue; no "Task was destroyed" warnings.

### Phase 4 — Multi-strategy fan-out
- Added `RSIReversionStrategy` (placeholder — always `HOLD`, real RSI logic deferred).
- `strategy_runner.py`: `run_strategies()` fans a tick out to a list of strategies.
- **Exception isolation**: `try/except` sits *inside* the per-strategy loop, not wrapped around
  the whole loop — confirmed by deliberately making a strategy raise and verifying the other
  strategy's signals still came through every tick.

### Phase 5 — Risk engine
- `risk.py`: `Portfolio` dataclass (`cash`, `positions: dict[str, float]`).
- `evaluate_signal()` layers three rejection rules in order: HOLD/low-confidence → exposure cap
  → position-limit (no shorting).
- **Bug caught & fixed**: exposure check originally compared a dollar amount against a raw
  percentage (`current_exposure > max_exposure_pct`) instead of against `max_allowed` — always
  true, rejected everything silently.
- **Bug caught & fixed**: SELL guard originally checked key *existence* in `positions`
  (`if symbol in portfolio.positions`) instead of the *value* — let an already-shorted position
  sell further into the negative. Fixed to `portfolio.positions.get(symbol, 0.0) <= 0 → reject`.

### Phase 6 — Execution engine (simulated)
- `execution.py`: `execute_order()` — single `if/else` on `order.side` (not two independent
  ifs, which double-applied and force-set `status="REJECTED"` regardless of outcome). Updates
  `Portfolio.positions`/`cash`, returns `ExecutionReport` with `str(uuid.uuid4())` order id and
  `avg_price=current_price` (not `order.price`, which is `None` for market orders).
- Full 3-stage async pipeline wired in `engine.py`: `tick_queue` → `strategy_loop` →
  `signal_queue` (carries `(Signal, TickEvent)` tuples so execution has price without touching
  shared mutable state) → `risk_execution_loop`. Shutdown sentinel (`None`) is forwarded stage
  to stage, not just checked locally.

### Phase 7 — Backtester (parity-first)
- `backtester.py`: `HistoricalClient` — implements the same `get_price(symbol) -> float` shape
  as `MockClient`, replaying a fixed price list instead of random-walking.
- **Parity test written and verified both ways**: two `HistoricalClient` instances fed an
  identical fixed price list produce byte-for-byte identical signal/order sequences through the
  real strategy+risk pipeline (`PARITY OK`). Confirmed the test actually catches divergence by
  deliberately injecting randomness into a strategy and seeing `PARITY FAILED` with the exact
  tick flagged.

### Phase 8 — Testing, logging, config
- `config.py`: `Settings(BaseSettings)` via `pydantic-settings`, reads `.env`
  (`TRADING_MODE`, `MAX_EXPOSURE_PCT`, `MAX_POSITION_PCT_PER_SYMBOL`, `MIN_SIGNAL_CONFIDENCE`).
- Structured logging in `engine.py` via stdlib `logging` — every risk/execution outcome logged
  with `tick=<event_id>` for correlation, using `%s`-style lazy formatting (not f-strings, so the
  string isn't built when the log level wouldn't emit it).
- `tests/test_risk.py` added — 7 cases covering every rule and every bug found above, so each
  is now a permanent regression guard.
- Full suite: **13/13 tests passing**, `mypy --strict src/` clean across 15 files.

**Locked decisions:**
- Position/exposure checks always compare like units (dollars vs dollars, not dollars vs %).
- SELL-side risk checks use `.get(symbol, 0.0)` and check the *value*, never just key presence.
- No shorting allowed in v1 — `evaluate_signal` rejects any SELL that would take a position
  negative. Revisit only if/when short-selling becomes an explicit, deliberate feature.
- `execute_order` always fills at the tick's `current_price` param, never `order.price`
  (which is `None` for MARKET orders in the current `OrderRequest` contract).
- Logging uses lazy `%s` formatting, not f-strings, project-wide.
- `asyncio.Queue` types are always explicitly parameterized (`asyncio.Queue[TickEvent | None]`),
  and `list[Strategy]` is always annotated explicitly at the point of construction — mypy does
  not reliably infer either on its own.

**Deferred / known gaps (deliberate, not oversights):**
- `RSIReversionStrategy` and `BreakoutVolumeStrategy` are placeholders — real indicator logic
  (RSI, volume-spike detection) not yet implemented. `rsi`, `volatility`, `volume_spike`,
  `orderbook_imbalance` in `indicators.py` are still stubs.
- No slippage/fee modeling in `execute_order` — fills instantly at tick price.
- No `Decimal` vs `float` decision made yet for money math — currently `float` throughout.
- Position sizing is hardcoded to `1.0` per order — no real sizing logic yet.

**Not yet done from v1 MVP DoD (Section 9):**
- One full week of paper-live signals logged with zero unhandled exceptions — not yet run
  continuously; everything so far has been short manual test runs.

**Next up:** Phase 9 — real Hyperliquid connection (`HyperliquidClient` implementing the
existing `ExchangeClient` Protocol), paper mode before any real capital flag is touched.

**Verify:**
```
cd hyperliquid_quant
pytest -v          # expect 13 passed
mypy --strict src/ # expect: Success, no issues found in 15 source files
python -m src.engine  # or however your entrypoint runs — watch structured log output
```