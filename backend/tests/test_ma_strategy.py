"""
tests/test_ma_strategy.py — MAStrategy 单元测试
"""
import pytest
import numpy as np
from strategies.ma_strategy import MAStrategy
from models.schemas import OrderSide


class TestMACalculation:
    """测试均线计算逻辑"""

    def setup_method(self):
        self.strategy = MAStrategy(short_window=5, long_window=20)

    def test_calculate_ma_length(self, sample_candlesticks):
        short_ma, long_ma = self.strategy.calculate_ma(sample_candlesticks)
        assert len(short_ma) == len(sample_candlesticks)
        assert len(long_ma) == len(sample_candlesticks)

    def test_short_ma_none_before_window(self, sample_candlesticks):
        short_ma, _ = self.strategy.calculate_ma(sample_candlesticks)
        # 前 short_window-1 个应为 None
        for i in range(self.strategy.short_window - 1):
            assert short_ma[i] is None

    def test_long_ma_none_before_window(self, sample_candlesticks):
        _, long_ma = self.strategy.calculate_ma(sample_candlesticks)
        for i in range(self.strategy.long_window - 1):
            assert long_ma[i] is None

    def test_ma_values_are_floats_after_window(self, sample_candlesticks):
        short_ma, long_ma = self.strategy.calculate_ma(sample_candlesticks)
        for v in short_ma[self.strategy.short_window - 1:]:
            assert isinstance(v, float)
        for v in long_ma[self.strategy.long_window - 1:]:
            assert isinstance(v, float)

    def test_ma_correctness(self, sample_candlesticks):
        """手动验证最后一根 short_ma 的值"""
        short_ma, _ = self.strategy.calculate_ma(sample_candlesticks)
        closes = [c.close for c in sample_candlesticks]
        expected = np.mean(closes[-self.strategy.short_window:])
        assert abs(short_ma[-1] - expected) < 1e-9

    def test_ascending_data_short_ma_above_long_ma(self, sample_candlesticks):
        """上涨趋势中短均线应高于长均线"""
        short_ma, long_ma = self.strategy.calculate_ma(sample_candlesticks)
        assert short_ma[-1] > long_ma[-1]


class TestMASignal:
    """测试交易信号生成"""

    @pytest.mark.asyncio
    async def test_golden_cross_generates_buy_signal(self, golden_cross_candlesticks):
        strategy = MAStrategy(short_window=5, long_window=20)
        signal = await strategy.analyze(data=golden_cross_candlesticks)
        assert signal is not None
        assert signal.side == OrderSide.BUY

    @pytest.mark.asyncio
    async def test_insufficient_data_returns_none(self):
        from datetime import datetime, timedelta
        from models.schemas import Candlestick
        strategy = MAStrategy(short_window=5, long_window=20)
        tiny_data = [
            Candlestick(
                timestamp=datetime.now() - timedelta(days=i),
                open=100, high=101, low=99, close=100, volume=1000
            )
            for i in range(5)   # 少于 long_window=20
        ]
        signal = await strategy.analyze(data=tiny_data)
        assert signal is None

    @pytest.mark.asyncio
    async def test_signal_strength_between_0_and_1(self, golden_cross_candlesticks):
        strategy = MAStrategy(short_window=5, long_window=20)
        signal = await strategy.analyze(data=golden_cross_candlesticks)
        if signal:
            assert 0.0 <= signal.signal_strength <= 1.0

    @pytest.mark.asyncio
    async def test_signal_has_required_fields(self, golden_cross_candlesticks):
        strategy = MAStrategy(short_window=5, long_window=20, symbol="000001.SZ")
        signal = await strategy.analyze(data=golden_cross_candlesticks)
        if signal:
            assert signal.symbol == "000001.SZ"
            assert signal.strategy.startswith("MA")
            assert signal.reason != ""
            assert signal.price > 0
            assert signal.quantity > 0


class TestMAStatus:
    """测试策略状态获取"""

    @pytest.mark.asyncio
    async def test_get_current_status_keys(self):
        strategy = MAStrategy(short_window=5, long_window=20, symbol="600519.SS")
        status = await strategy.get_current_status()
        for key in ("strategy", "symbol", "current_price", "short_ma", "long_ma", "trend"):
            assert key in status

    @pytest.mark.asyncio
    async def test_trend_values_are_valid(self):
        strategy = MAStrategy(symbol="600519.SS")
        status = await strategy.get_current_status()
        assert status["trend"] in ("bullish", "bearish", "neutral")
