import numpy as np
from typing import List, Optional, Tuple
from datetime import datetime

from models.schemas import Candlestick, TradeSignal, OrderSide
from utils.data_fetcher import DataFetcher


class MAStrategy:
    """
    均线交叉策略
    
    策略逻辑:
    - 当短期均线上穿长期均线时，产生买入信号（金叉）
    - 当短期均线下穿长期均线时，产生卖出信号（死叉）
    - 信号强度取决于均线之间的差距
    """
    
    def __init__(
        self,
        short_window: int = 5,
        long_window: int = 20,
        symbol: str = "600519.SS"
    ):
        self.short_window = short_window
        self.long_window = long_window
        self.symbol = symbol
        self.data_fetcher = DataFetcher(use_mock=True)
        self.name = f"MA({short_window}/{long_window})"
    
    async def analyze(self, data: Optional[List[Candlestick]] = None) -> Optional[TradeSignal]:
        """
        分析当前市场状态，生成交易信号
        
        Returns:
            TradeSignal: 交易信号，如果没有信号则返回 None
        """
        if data is None:
            data = await self.data_fetcher.get_historical_data(self.symbol, days=self.long_window + 10)
        
        if len(data) < self.long_window:
            return None
        
        # 计算均线
        closes = np.array([c.close for c in data])
        short_ma = np.mean(closes[-self.short_window:])
        long_ma = np.mean(closes[-self.long_window:])
        
        # 计算前一周期的均线用于判断交叉
        prev_short_ma = np.mean(closes[-self.short_window-1:-1])
        prev_long_ma = np.mean(closes[-self.long_window-1:-1])
        
        current_price = closes[-1]
        
        # 判断金叉：短期均线从下向上穿过长期均线
        golden_cross = (prev_short_ma <= prev_long_ma) and (short_ma > long_ma)
        
        # 判断死叉：短期均线从上向下穿过长期均线
        death_cross = (prev_short_ma >= prev_long_ma) and (short_ma < long_ma)
        
        if golden_cross:
            # 计算信号强度：均线差距越大，信号越强
            gap_ratio = (short_ma - long_ma) / long_ma
            signal_strength = min(1.0, abs(gap_ratio) * 10)
            
            return TradeSignal(
                symbol=self.symbol,
                side=OrderSide.BUY,
                price=current_price,
                quantity=100,
                signal_strength=signal_strength,
                strategy=self.name,
                reason=f"金叉信号：短期均线 ({short_ma:.2f}) 上穿长期均线 ({long_ma:.2f})"
            )
        
        elif death_cross:
            gap_ratio = (long_ma - short_ma) / long_ma
            signal_strength = min(1.0, abs(gap_ratio) * 10)
            
            return TradeSignal(
                symbol=self.symbol,
                side=OrderSide.SELL,
                price=current_price,
                quantity=100,
                signal_strength=signal_strength,
                strategy=self.name,
                reason=f"死叉信号：短期均线 ({short_ma:.2f}) 下穿长期均线 ({long_ma:.2f})"
            )
        
        return None
    
    def calculate_ma(self, data: List[Candlestick]) -> Tuple[List[float], List[float]]:
        """计算短期和长期均线"""
        closes = np.array([c.close for c in data])
        
        short_ma = []
        long_ma = []
        
        for i in range(len(closes)):
            if i >= self.short_window - 1:
                short_ma.append(np.mean(closes[i-self.short_window+1:i+1]))
            else:
                short_ma.append(None)
            
            if i >= self.long_window - 1:
                long_ma.append(np.mean(closes[i-self.long_window+1:i+1]))
            else:
                long_ma.append(None)
        
        return short_ma, long_ma
    
    async def get_current_status(self) -> dict:
        """获取策略当前状态"""
        data = await self.data_fetcher.get_historical_data(self.symbol, days=self.long_window + 10)
        short_ma, long_ma = self.calculate_ma(data)
        
        current_short = short_ma[-1] if short_ma[-1] else 0
        current_long = long_ma[-1] if long_ma[-1] else 0
        current_price = data[-1].close if data else 0
        
        # 判断趋势
        if current_short > current_long:
            trend = "bullish"
        elif current_short < current_long:
            trend = "bearish"
        else:
            trend = "neutral"
        
        return {
            "strategy": self.name,
            "symbol": self.symbol,
            "current_price": current_price,
            "short_ma": current_short,
            "long_ma": current_long,
            "trend": trend,
            "ma_gap": current_short - current_long,
            "ma_gap_percent": ((current_short - current_long) / current_long * 100) if current_long else 0
        }
