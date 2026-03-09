import random
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import asyncio

from models.schemas import Candlestick


class DataFetcher:
    """数据获取器 - 支持模拟数据和真实数据"""
    
    def __init__(self, use_mock: bool = True):
        self.use_mock = use_mock
        self._cache: Dict[str, List[Candlestick]] = {}
    
    async def get_historical_data(
        self, 
        symbol: str, 
        days: int = 60,
        interval: str = "1d"
    ) -> List[Candlestick]:
        """获取历史 K 线数据"""
        cache_key = f"{symbol}_{days}_{interval}"
        
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        if self.use_mock:
            data = self._generate_mock_data(symbol, days)
        else:
            data = await self._fetch_real_data(symbol, days)
        
        self._cache[cache_key] = data
        return data
    
    def _generate_mock_data(self, symbol: str, days: int) -> List[Candlestick]:
        """生成模拟 K 线数据"""
        # 根据股票代码设置不同的基准价格
        base_prices = {
            "600519.SS": 1700,  # 贵州茅台
            "000001.SZ": 10,    # 平安银行
            "BTC-USD": 45000,   # 比特币
        }
        base_price = base_prices.get(symbol, 100)
        
        # 添加一些波动性
        volatility = base_price * 0.02
        
        data = []
        current_price = base_price
        
        for i in range(days):
            timestamp = datetime.now() - timedelta(days=days-i)
            
            # 生成随机但合理的价格变动
            change = random.gauss(0, volatility)
            open_price = current_price
            close_price = current_price + change
            
            high_price = max(open_price, close_price) + abs(random.gauss(0, volatility * 0.5))
            low_price = min(open_price, close_price) - abs(random.gauss(0, volatility * 0.5))
            
            volume = int(random.gauss(1000000, 300000))
            
            candlestick = Candlestick(
                timestamp=timestamp,
                open=round(open_price, 2),
                high=round(high_price, 2),
                low=round(low_price, 2),
                close=round(close_price, 2),
                volume=max(0, volume)
            )
            data.append(candlestick)
            
            current_price = close_price
        
        return data
    
    async def _fetch_real_data(self, symbol: str, days: int) -> List[Candlestick]:
        """获取真实数据（预留接口）"""
        # 这里可以接入真实的数据源，如 Yahoo Finance、聚宽等
        # 目前返回模拟数据作为降级
        return self._generate_mock_data(symbol, days)
    
    async def get_current_price(self, symbol: str) -> float:
        """获取当前价格"""
        data = await self.get_historical_data(symbol, days=2)
        if data:
            return data[-1].close
        return 0.0
    
    def clear_cache(self, symbol: Optional[str] = None):
        """清除缓存"""
        if symbol:
            keys_to_remove = [k for k in self._cache if k.startswith(symbol)]
            for key in keys_to_remove:
                del self._cache[key]
        else:
            self._cache.clear()


# 全局实例
data_fetcher = DataFetcher(use_mock=True)
