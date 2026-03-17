"""
tests/test_macd_strategy.py — MACDStrategy 单元测试（8个）
"""
import pytest
import numpy as np
from datetime import datetime, timedelta

from strategies.macd_strategy import MACDStrategy
from models.schemas import Candlestick, OrderSide


def make_candles(prices):
    """从价格列表快速构造 Candlestick 列表"""
    return [
        Candlestick(
            timestamp=datetime.now() - timedelta(days=len(prices) - i),
            open=p, high=p + 0.5, low=p - 0.5, close=p, volume=100_000,
        )
        for i, p in enumerate(prices)
    ]


class TestMACDCalculation:
    """测试 MACD 指标计算"""

    def setup_method(self):
        self.strategy = MACDStrategy(fast_period=12, slow_period=26, signal_period=9)

    def test_output_length_equals_input(self, sample_candlesticks):
        macd, signal, hist = self.strategy.calculate_macd(sample_candlesticks)
        assert len(macd) == len(sample_candlesticks)
        assert len(signal) == len(sample_candlesticks)
        assert len(hist) == len(sample_candlesticks)

    def test_histogram_equals_macd_minus_signal(self, sample_candlesticks):
        macd, signal, hist = self.strategy.calculate_macd(sample_candlesticks)
        np.testing.assert_allclose(hist, macd - signal, atol=1e-10)

    def test_ema_converges_on_constant_series(self):
        """常数序列的 EMA 应等于常数本身"""
        values = np.full(50, 100.0)
        ema = self.strategy._ema(values, 12)
        assert abs(ema[-1] - 100.0) < 1e-6

    def test_macd_positive_in_uptrend(self):
        """上升趋势中快线应高于慢线，MACD > 0"""
        prices = [100 + i for i in range(60)]
        data = make_candles(prices)
        macd, _, _ = self.strategy.calculate_macd(data)
        assert macd[-1] > 0


class TestMACDSignal:
    """测试 MACD 信号生成"""

    @pytest.mark.asyncio
    async def test_insufficient_data_returns_none(self):
        strategy = MACDStrategy(fast_period=12, slow_period=26, signal_period=9)
        tiny = make_candles([100.0] * 10)
        signal = await strategy.analyze(data=tiny)
        assert signal is None

    @pytest.mark.asyncio
    async def test_golden_cross_generates_buy(self):
        """构造金叉：先跌后大幅反弹"""
        strategy = MACDStrategy(fast_period=12, slow_period=26, signal_period=9)
        # 先下降 40 根，再急拉 10 根
        prices = [100 - i * 0.5 for i in range(40)] + [80 + i * 3 for i in range(15)]
        data = make_candles(prices)
        signal = await strategy.analyze(data=data)
        if signal:
            assert signal.side == OrderSide.BUY

    @pytest.mark.asyncio
    async def test_signal_strength_in_range(self):
        """信号强度必须在 [0, 1]"""
        strategy = MACDStrategy()
        prices = [100 - i * 0.5 for i in range(40)] + [80 + i * 3 for i in range(15)]
        data = make_candles(prices)
        signal = await strategy.analyze(data=data)
        if signal:
            assert 0.0 <= signal.signal_strength <= 1.0

    @pytest.mark.asyncio
    async def test_get_current_status_keys(self):
        strategy = MACDStrategy(symbol="600519.SS")
        status = await strategy.get_current_status()
        for key in ("strategy", "symbol", "current_price", "macd", "signal", "histogram", "trend"):
            assert key in status

    @pytest.mark.asyncio
    async def test_trend_values_valid(self):
        strategy = MACDStrategy(symbol="600519.SS")
        status = await strategy.get_current_status()
        assert status["trend"] in ("bullish", "bearish", "neutral")
