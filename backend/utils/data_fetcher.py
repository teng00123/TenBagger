import random
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional

import numpy as np

from models.schemas import Candlestick

logger = logging.getLogger(__name__)


class DataFetcher:
    """数据获取器 - 支持模拟数据和真实数据（yfinance / AkShare）"""

    def __init__(self, use_mock: bool = True):
        self.use_mock = use_mock
        self._cache: Dict[str, List[Candlestick]] = {}

    # ────────────────────────────────────────────
    # 公开接口
    # ────────────────────────────────────────────

    async def get_historical_data(
        self,
        symbol: str,
        days: int = 60,
        interval: str = "1d",
    ) -> List[Candlestick]:
        """获取历史 K 线数据（有缓存）"""
        cache_key = f"{symbol}_{days}_{interval}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        if self.use_mock:
            data = self._generate_mock_data(symbol, days)
        else:
            data = await self._fetch_real_data(symbol, days)

        self._cache[cache_key] = data
        return data

    async def get_current_price(self, symbol: str) -> float:
        """获取最新价格"""
        data = await self.get_historical_data(symbol, days=2)
        return data[-1].close if data else 0.0

    def clear_cache(self, symbol: Optional[str] = None):
        """清除缓存"""
        if symbol:
            for key in [k for k in self._cache if k.startswith(symbol)]:
                del self._cache[key]
        else:
            self._cache.clear()

    # ────────────────────────────────────────────
    # 真实数据（yfinance，国际标的）
    # ────────────────────────────────────────────

    async def _fetch_real_data(self, symbol: str, days: int) -> List[Candlestick]:
        """
        优先用 yfinance（BTC-USD / 港股 / 国际标的）；
        A 股（.SS / .SZ）降级到 AkShare；
        失败时自动 fallback 到模拟数据。
        """
        try:
            if symbol.endswith(".SS") or symbol.endswith(".SZ"):
                return await self._fetch_akshare(symbol, days)
            else:
                return await self._fetch_yfinance(symbol, days)
        except Exception as e:
            logger.warning("真实数据获取失败 [%s]: %s，降级为模拟数据", symbol, e)
            return self._generate_mock_data(symbol, days)

    async def _fetch_yfinance(self, symbol: str, days: int) -> List[Candlestick]:
        """通过 yfinance 获取数据（在线程池中运行，避免阻塞事件循环）"""
        import yfinance as yf

        def _download():
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=f"{days}d", interval="1d", auto_adjust=True)
            return df

        loop = asyncio.get_event_loop()
        df = await loop.run_in_executor(None, _download)

        if df is None or df.empty:
            raise ValueError(f"yfinance 未返回数据: {symbol}")

        result: List[Candlestick] = []
        for ts, row in df.iterrows():
            result.append(
                Candlestick(
                    timestamp=ts.to_pydatetime(),
                    open=round(float(row["Open"]), 4),
                    high=round(float(row["High"]), 4),
                    low=round(float(row["Low"]), 4),
                    close=round(float(row["Close"]), 4),
                    volume=int(row.get("Volume", 0)),
                )
            )
        return result

    async def _fetch_akshare(self, symbol: str, days: int) -> List[Candlestick]:
        """通过 AkShare 获取 A 股数据（在线程池中运行）"""
        import akshare as ak

        # 转换代码：600519.SS → sh600519 / 000001.SZ → sz000001
        code = symbol.split(".")[0]
        suffix = symbol.split(".")[-1]
        ak_symbol = ("sh" if suffix == "SS" else "sz") + code

        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=days + 10)).strftime("%Y%m%d")

        def _download():
            df = ak.stock_zh_a_hist(
                symbol=code,
                period="daily",
                start_date=start_date,
                end_date=end_date,
                adjust="qfq",  # 前复权
            )
            return df

        loop = asyncio.get_event_loop()
        df = await loop.run_in_executor(None, _download)

        if df is None or df.empty:
            raise ValueError(f"AkShare 未返回数据: {symbol}")

        result: List[Candlestick] = []
        for _, row in df.tail(days).iterrows():
            result.append(
                Candlestick(
                    timestamp=datetime.strptime(str(row["日期"]), "%Y-%m-%d"),
                    open=round(float(row["开盘"]), 4),
                    high=round(float(row["最高"]), 4),
                    low=round(float(row["最低"]), 4),
                    close=round(float(row["收盘"]), 4),
                    volume=int(row.get("成交量", 0)),
                )
            )
        return result

    # ────────────────────────────────────────────
    # 模拟数据
    # ────────────────────────────────────────────

    def _generate_mock_data(self, symbol: str, days: int) -> List[Candlestick]:
        base_prices = {
            "600519.SS": 1700,
            "000001.SZ": 10,
            "BTC-USD": 45000,
        }
        base_price = base_prices.get(symbol, 100)
        volatility = base_price * 0.02

        data: List[Candlestick] = []
        current_price = base_price

        for i in range(days):
            timestamp = datetime.now() - timedelta(days=days - i)
            change = random.gauss(0, volatility)
            open_price = current_price
            close_price = current_price + change
            high_price = max(open_price, close_price) + abs(random.gauss(0, volatility * 0.5))
            low_price = min(open_price, close_price) - abs(random.gauss(0, volatility * 0.5))
            volume = int(random.gauss(1_000_000, 300_000))

            data.append(
                Candlestick(
                    timestamp=timestamp,
                    open=round(open_price, 2),
                    high=round(high_price, 2),
                    low=round(low_price, 2),
                    close=round(close_price, 2),
                    volume=max(0, volume),
                )
            )
            current_price = close_price

        return data


# 全局实例（use_mock 由环境变量控制）
import os
_use_mock = os.getenv("DATA_SOURCE", "mock") == "mock"
data_fetcher = DataFetcher(use_mock=_use_mock)
