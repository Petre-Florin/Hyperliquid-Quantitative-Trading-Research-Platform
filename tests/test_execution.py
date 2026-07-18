import asyncio

from config import Settings
from events import OrderRequest
from execution import execute_order
from risk import Portfolio


def run(coro):
    return asyncio.run(coro)


def test_buy_deducts_notional_plus_fee():
    portfolio = Portfolio(cash=10000.0)
    settings = Settings()
    order = OrderRequest(symbol="BTC", side="BUY", size=5.0, order_type="MARKET")

    report = run(execute_order(order, portfolio, current_price=100.0, settings=settings))

    # notional = 5 * 100 = 500; fee = 500 * 0.00045 = 0.225
    assert report.status == "FILLED"
    assert abs(portfolio.cash - (10000.0 - 500.0 - 0.225)) < 1e-9
    assert portfolio.positions["BTC"] == 5.0


def test_sell_adds_notional_minus_fee():
    portfolio = Portfolio(cash=10000.0, positions={"BTC": 5.0})
    settings = Settings()
    order = OrderRequest(symbol="BTC", side="SELL", size=5.0, order_type="MARKET")

    report = run(execute_order(order, portfolio, current_price=100.0, settings=settings))

    assert report.status == "FILLED"
    assert abs(portfolio.cash - (10000.0 + 500.0 - 0.225)) < 1e-9
    assert portfolio.positions["BTC"] == 0.0