from events import TickEvent
from strategies.ma_crossover import MACrossoverStrategy

def test_crossover_flips_to_sell_on_downtrend():
    strategy = MACrossoverStrategy(short_period=2, long_period=4)
    prices = [10, 11, 12, 13, 14, 13, 12, 11]

    last_action = None
    for i in range(len(prices)):
        tick = TickEvent(symbol="BTC", price=prices[i], volume=1.0, orderbook={})
        signal = strategy.on_tick(tick, prices[:i+1])
        last_action = signal.action

    assert last_action == "SELL"

def test_crossover_holds_with_insufficient_data():
    strategy = MACrossoverStrategy(short_period=2, long_period=4)
    tick = TickEvent(symbol="BTC", price=10, volume=1.0, orderbook={})
    signal = strategy.on_tick(tick, [10])
    assert signal.action == "HOLD"
    assert signal.confidence == 0.0