"""Typed, immutable event contracts. Every module imports from here.

No other module defines its own shape for these concepts. See build spec
Section 3 — these are locked; changing them is an architectural decision,
not a per-phase one.
"""

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Literal


def _now() -> datetime:
    return datetime.now(UTC)


@dataclass(frozen=True)
class TickEvent:
    symbol: str
    price: float
    volume: float
    orderbook: dict[str, object]
    timestamp: datetime = field(default_factory=_now)
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass(frozen=True)
class Signal:
    strategy_name: str
    symbol: str
    action: Literal["BUY", "SELL", "HOLD"]
    confidence: float
    metadata: dict[str, object] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=_now)


@dataclass(frozen=True)
class OrderRequest:
    symbol: str
    side: Literal["BUY", "SELL"]
    size: float
    order_type: Literal["MARKET", "LIMIT"]
    price: float | None = None
    signal_ref: str | None = None  # traceability back to the originating signal


@dataclass(frozen=True)
class ExecutionReport:
    order_id: str
    symbol: str
    status: Literal["FILLED", "PARTIAL", "REJECTED", "CANCELLED"]
    filled_size: float
    avg_price: float
    timestamp: datetime = field(default_factory=_now)
