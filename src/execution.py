"""The only side-effecting module. Consumes OrderRequest, places/simulates fills,
updates Portfolio, returns ExecutionReport. Implemented in Phase 6.
"""

import uuid

from config import Settings
from events import ExecutionReport, OrderRequest
from risk import Portfolio


async def execute_order(
    order: OrderRequest, portfolio: Portfolio, current_price: float, settings: Settings
) -> ExecutionReport:
    notional = order.size * current_price
    fee = notional * settings.taker_fee_pct

    if order.side == "BUY":
        portfolio.positions[order.symbol] = portfolio.positions.get(order.symbol, 0.0) + order.size
        portfolio.cash -= notional + fee
    else:
        portfolio.positions[order.symbol] = portfolio.positions.get(order.symbol, 0.0) - order.size
        portfolio.cash += notional - fee

    return ExecutionReport(
        order_id=str(uuid.uuid4()),
        symbol=order.symbol,
        status="FILLED",
        filled_size=order.size,
        avg_price=current_price,
    )