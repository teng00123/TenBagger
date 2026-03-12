"""
tests/test_data_fetcher.py — DataFetcher 单元测试
"""
import pytest
from utils.data_fetcher import DataFetcher
from models.schemas import Candlestick


class TestDataFetcherMock:
    """测试模拟数据生成"""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.fetcher = DataFetcher(use_mock=True)

    @pytest.mark.asyncio
    async def test_returns_correct_number_of_candles(self):
        data = await self.fetcher.get_historical_data("600519.SS", days=30)
        assert len(data) == 30

    @pytest.mark.asyncio
    async def test_returns_candlestick_objects(self):
        data = await self.fetcher.get_historical_data("000001.SZ", days=5)
        for candle in data:
            assert isinstance(candle, Candlestick)

    @pytest.mark.asyncio
    async def test_candlestick_ohlc_integrity(self):
        """high >= open/close >= low"""
        data = await self.fetcher.get_historical_data("BTC-USD", days=20)
        for c in data:
            assert c.high >= c.open, f"high {c.high} < open {c.open}"
            assert c.high >= c.close, f"high {c.high} < close {c.close}"
            assert c.low <= c.open, f"low {c.low} > open {c.open}"
            assert c.low <= c.close, f"low {c.low} > close {c.close}"
            assert c.volume >= 0

    @pytest.mark.asyncio
    async def test_different_symbols_have_different_price_ranges(self):
        moutai = await self.fetcher.get_historical_data("600519.SS", days=5)
        bank = await self.fetcher.get_historical_data("000001.SZ", days=5)
        # 茅台基准 1700，平安银行基准 10，均值差距应很大
        assert moutai[0].close > bank[0].close * 10

    @pytest.mark.asyncio
    async def test_cache_returns_same_object(self):
        data1 = await self.fetcher.get_historical_data("600519.SS", days=10)
        data2 = await self.fetcher.get_historical_data("600519.SS", days=10)
        assert data1 is data2   # 缓存命中，同一对象

    @pytest.mark.asyncio
    async def test_clear_cache(self):
        await self.fetcher.get_historical_data("600519.SS", days=10)
        self.fetcher.clear_cache("600519.SS")
        assert not any(k.startswith("600519.SS") for k in self.fetcher._cache)

    @pytest.mark.asyncio
    async def test_clear_all_cache(self):
        await self.fetcher.get_historical_data("600519.SS", days=5)
        await self.fetcher.get_historical_data("000001.SZ", days=5)
        self.fetcher.clear_cache()
        assert len(self.fetcher._cache) == 0

    @pytest.mark.asyncio
    async def test_get_current_price_returns_positive(self):
        price = await self.fetcher.get_current_price("600519.SS")
        assert price > 0

    @pytest.mark.asyncio
    async def test_timestamps_are_in_order(self):
        data = await self.fetcher.get_historical_data("600519.SS", days=10)
        for i in range(1, len(data)):
            assert data[i].timestamp > data[i - 1].timestamp
