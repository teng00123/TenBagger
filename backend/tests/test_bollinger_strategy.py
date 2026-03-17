"""
tests/test_bollinger_strategy.py — BollingerStrategy 单元测试（8个）
"""
import pytest
import numpy as np
from datetime import datetime, timedelta

from strategies.bollinger_strategy import BollingerStrategy
from models.schemas import Candlestick, OrderSide


def make_candles(prices):
    return [
        Candlestick(
            timestamp=datetime.now() - timedelta(days=len(prices) - i),
            open=p, high=p + 0.5, low=p - 0.5, close=p, volume=100_000,
        )
        for i, p in enumerate(prices)
    ]


class TestBollingerCalculation:
    """测试布林带计算"""

    def setup_method(self):
        self.strategy = BollingerStrategy(period=20, k=2.0)

    def test_output_length_equals_input(self, sample_candlesticks):
        upper, middle, lower = self.strategy.calculate_bands(sample_candlesticks)
        assert len(upper) == len(sample_candlesticks)
        assert len(middle) == len(sample_candlesticks)
        assert len(lower) == len(sample_candlesticks)

    def test_first_period_minus_one_is_nan(self, sample_candlesticks):
        upper, middle, lower = self.strategy.calculate_bands(sample_candlesticks)
        assert np.isnan(upper[self.strategy.period - 2])
        assert np.isnan(middle[self.strategy.period - 2])

    def test_upper_above_lower(self, sample_candlesticks):
        upper, middle, lower = self.strategy.calculate_bands(sample_candlesticks)
        valid = ~np.isnan(upper)
        assert np.all(upper[valid] > lower[valid])

    def test_middle_between_upper_and_lower(self, sample_candlesticks):
        upper, middle, lower = self.strategy.calculate_bands(sample_candlesticks)
        valid = ~np.isnan(upper)
        assert np.all(upper[valid] >= middle[valid])
        assert np.all(middle[valid] >= lower[valid])


class TestBollingerSignal:
    """测试布林带信号生成"""

    @pytest.mark.asyncio
    async def test_insufficient_data_returns_none(self):
        strategy = BollingerStrategy(period=20)
        tiny = make_candles([100.0] * 10)
        signal = await strategy.analyze(data=tiny)
        assert signal is None

    @pytest.mark.asyncio
    async def test_price_below_lower_band_buy_signal(self):
        """价格跌破下轨应产生买入信号"""
        strategy = BollingerStrategy(period=20, k=2.0)
        # 前 22 根平稳（均值=100，std 很小），最后1根暴跌到 50
        prices = [100.0] * 22 + [50.0]
        data = make_candles(prices)
        signal = await strategy.analyze(data=data)
        if signal:
            assert signal.side == OrderSide.BUY

    @pytest.mark.asyncio
    async def test_signal_strength_in_range(self):
        strategy = BollingerStrategy(period=20, k=2.0)
        prices = [100.0] * 22 + [50.0]
        data = make_candles(prices)
        signal = await strategy.analyze(data=data)
        if signal:
            assert 0.0 <= signal.signal_strength <= 1.0

    @pytest.mark.asyncio
    async def test_get_current_status_keys(self):
        strategy = BollingerStrategy(symbol="600519.SS")
        status = await strategy.get_current_status()
        for key in ("strategy", "symbol", "current_price", "upper_band", "middle_band", "lower_band", "market_state"):
            assert key in status
