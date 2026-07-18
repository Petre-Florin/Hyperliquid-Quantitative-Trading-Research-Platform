from config import Settings
from events import Signal
from risk import Portfolio, evaluate_signal


def make_settings(**overrides: object) -> Settings:
    return Settings(**overrides)


def test_hold_signal_rejected():
    portfolio = Portfolio(cash=10000.0)
    settings = make_settings()
    signal = Signal(strategy_name="test", symbol="BTC", action="HOLD", confidence=1.0)
    assert evaluate_signal(signal, portfolio, current_price=100.0, settings=settings) is None


def test_low_confidence_rejected():
    portfolio = Portfolio(cash=10000.0)
    settings = make_settings()
    signal = Signal(strategy_name="test", symbol="BTC", action="BUY", confidence=0.3)
    assert evaluate_signal(signal, portfolio, current_price=100.0, settings=settings) is None


def test_high_confidence_buy_approved_with_correct_size():
    portfolio = Portfolio(cash=10000.0)
    settings = make_settings()
    signal = Signal(strategy_name="test", symbol="BTC", action="BUY", confidence=0.9)

    order = evaluate_signal(signal, portfolio, current_price=100.0, settings=settings)

    assert order is not None
    assert order.side == "BUY"
    assert order.size == 5.0


def test_size_scales_inversely_with_price():
    portfolio = Portfolio(cash=10000.0)
    settings = make_settings()
    signal = Signal(strategy_name="test", symbol="BTC", action="BUY", confidence=0.9)

    order = evaluate_signal(signal, portfolio, current_price=63597.0, settings=settings)

    assert order is not None
    expected_size = 500.0 / 63597.0
    assert abs(order.size - expected_size) < 1e-9


def test_exposure_cap_rejects_when_margin_used_would_exceed_limit():
    # Existing position is in a DIFFERENT symbol (ETH) than the one being traded
    # (BTC), so the "already holding this symbol" no-pyramiding guard doesn't
    # interfere — this isolates the exposure/margin cap logic specifically.
    # price=1.0 for both is a deliberate simplification so the notional math is
    # easy to verify by hand; it doesn't need to be realistic to test the logic.
    portfolio = Portfolio(cash=10000.0, positions={"ETH": 9500.0})
    settings = make_settings()  # max_exposure_pct=0.2 -> max_allowed_margin = 2000
    signal = Signal(strategy_name="test", symbol="BTC", action="BUY", confidence=0.9)

    # current_margin_used = 9500 / leverage(5) = 1900; + margin_required(100) = 2000
    # 2000 > 2000 is False -> should still be approved (right at the boundary)
    order = evaluate_signal(signal, portfolio, current_price=1.0, settings=settings)
    assert order is not None

    # push existing exposure just over the cap
    portfolio_over = Portfolio(cash=10000.0, positions={"ETH": 9600.0})
    order_over = evaluate_signal(signal, portfolio_over, current_price=1.0, settings=settings)
    assert order_over is None


def test_sell_rejected_with_no_position():
    portfolio = Portfolio(cash=10000.0)
    settings = make_settings()
    signal = Signal(strategy_name="test", symbol="BTC", action="SELL", confidence=0.9)
    assert evaluate_signal(signal, portfolio, current_price=100.0, settings=settings) is None


def test_sell_rejected_when_already_short():
    portfolio = Portfolio(cash=10000.0, positions={"BTC": -3.0})
    settings = make_settings()
    signal = Signal(strategy_name="test", symbol="BTC", action="SELL", confidence=0.9)
    assert evaluate_signal(signal, portfolio, current_price=100.0, settings=settings) is None


def test_sell_approved_when_holding_position():
    portfolio = Portfolio(cash=10000.0, positions={"BTC": 2.0})
    settings = make_settings()
    signal = Signal(strategy_name="test", symbol="BTC", action="SELL", confidence=0.9)
    order = evaluate_signal(signal, portfolio, current_price=100.0, settings=settings)
    assert order is not None
    assert order.side == "SELL"


def test_buy_rejected_when_already_holding_position():
    portfolio = Portfolio(cash=10000.0, positions={"BTC": 5.0})
    settings = make_settings()
    signal = Signal(strategy_name="test", symbol="BTC", action="BUY", confidence=0.9)
    assert evaluate_signal(signal, portfolio, current_price=100.0, settings=settings) is None