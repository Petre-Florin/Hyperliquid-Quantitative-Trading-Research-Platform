"""Pure functions on raw values. No state, no API calls, no side effects.
Implemented in Phase 1. Loop version first, vectorize second (see Phase 1 pitfall).
"""


def moving_average(prices: list[float], period: int) -> float | None:
    if len(prices) < period:
        return None
    return sum(prices[-period:])/period


def ema(prices: list[float], period: int) -> float | None:
    if len(prices) < period:
        return None

    alpha = 2 / (period + 1)
    ema_value = sum(prices[:period]) / period

    for price in prices[period:]:
        ema_value = (price * alpha) + (ema_value * (1 - alpha))
        
    return ema_value


def rsi(prices: list[float], period: int) -> float | None:
    if len(prices) < period + 1:
        return None

    changes = [prices[i] - prices[i - 1] for i in range(1, len(prices))]
    gains = [c if c > 0 else 0.0 for c in changes]
    losses = [-c if c < 0 else 0.0 for c in changes]

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    for gain, loss in zip(gains[period:], losses[period:]):
        avg_gain = (avg_gain * (period - 1) + gain) / period
        avg_loss = (avg_loss * (period - 1) + loss) / period

    if avg_loss == 0:
        return 100.0

    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def volatility(prices: list[float], period: int) -> float:
    raise NotImplementedError


def returns(prices: list[float]) -> list[float]:
    return [((prices[i]-prices[i-1])/prices[i-1]) for i in range(1,len(prices))]

def volume_spike(volumes: list[float], period: int, threshold: float) -> bool:
    if len(volumes) < period + 1:
        return False
    baseline = sum(volumes[-period - 1:-1]) / period
    if baseline == 0:
        return False
    return volumes[-1] > baseline * threshold


def orderbook_imbalance(orderbook: dict[str, object]) -> float:
    raise NotImplementedError
