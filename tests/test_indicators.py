from indicators import moving_average, ema, returns

def test_moving_average_basic():
    assert moving_average([10, 11, 12, 11, 13], period=3) == 12.0

def test_moving_average_not_enough_data():
    assert moving_average([10, 11], period=3) is None

def test_returns_basic():
    result = returns([10, 11, 12])
    assert result[0] == 0.1
    assert round(result[1], 4) == 0.0909

def test_ema_basic():
    assert ema([10, 11, 12, 11, 13], period=3) == 12.0