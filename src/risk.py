from dataclasses import dataclass, field

from config import Settings
from events import OrderRequest, Signal


@dataclass
class Portfolio:
    cash: float
    positions: dict[str, float] = field(default_factory=dict)


def evaluate_signal(
    signal: Signal,
    portfolio: Portfolio,
    current_price: float,
    settings: Settings,
) -> OrderRequest | None:
    if signal.action == "HOLD" or signal.confidence < settings.min_signal_confidence:
        return None

    margin_required = settings.trade_dollar_amount
    notional = margin_required * settings.leverage
    size = notional / current_price

    current_notional = sum(portfolio.positions.values()) * current_price
    current_margin_used = current_notional / settings.leverage
    max_allowed_margin = portfolio.cash * settings.max_exposure_pct

    if current_margin_used + margin_required > max_allowed_margin:
        return None

    current_position = portfolio.positions.get(signal.symbol, 0.0)

    if signal.action == "SELL" and current_position <= 0:
        return None

    if signal.action == "BUY" and current_position > 0:
        return None 

    return OrderRequest(symbol=signal.symbol, side=signal.action, size=size, order_type="MARKET")