import numpy as np
from typing import List, Optional
from datetime import datetime

from models.schemas import Candlestick, TradeSignal, OrderSide
from utils.data_fetcher import DataFetcher


class RSIStrategy:
    """
    RSI (相对强弱指标) 策略
    
    策略逻辑:
    - RSI < 30 (超卖区): 产生买入信号
    - RSI > 70 (超买区): 产生卖出信号
    - RSI 从超卖区回升或从超买区回落时确认信号
    """
    
    def __init__(
        self,
        rsi_period: int = 14,
        oversold_threshold: float = 30.0,
        overbought_threshold: float = 70.0,
        symbol: str = "600519.SS"
    ):
        self.rsi_period = rsi_period
        self.oversold_threshold = oversold_threshold
        self.overbought_threshold = overbought_threshold
        self.symbol = symbol
        self.data_fetcher = DataFetcher(use_mock=True)
        self.name = f"RSI({rsi_period})"
    
    async def analyze(self, data: Optional[List[Candlestick]] = None) -> Optional[TradeSignal]:
        """
        分析当前市场状态，生成交易信号
        
        Returns:
            TradeSignal: 交易信号，如果没有信号则返回 None
        """
        if data is None:
            data = await self.data_fetcher.get_historical_data(
                self.symbol, 
                days=self.rsi_period + 10
            )
        
        if len(data) < self.rsi_period + 1:
            return None
        
        # 计算 RSI
        rsi_values = self.calculate_rsi(data)
        current_rsi = rsi_values[-1]
        prev_rsi = rsi_values[-2] if len(rsi_values) > 1 else current_rsi
        
        current_price = data[-1].close
        
        # 判断买入信号：RSI 从超卖区回升
        buy_signal = (
            prev_rsi < self.oversold_threshold and 
            current_rsi >= self.oversold_threshold
        )
        
        # 判断卖出信号：RSI 从超买区回落
        sell_signal = (
            prev_rsi > self.overbought_threshold and 
            current_rsi <= self.overbought_threshold
        )
        
        # 强信号：RSI 极度超卖或超买
        extreme_oversold = current_rsi < 20
        extreme_overbought = current_rsi > 80
        
        if buy_signal or extreme_oversold:
            # 计算信号强度
            if extreme_oversold:
                signal_strength = min(1.0, (self.oversold_threshold - current_rsi) / 30)
            else:
                signal_strength = min(1.0, (current_rsi - prev_rsi) / 20)
            
            return TradeSignal(
                symbol=self.symbol,
                side=OrderSide.BUY,
                price=current_price,
                quantity=100,
                signal_strength=signal_strength,
                strategy=self.name,
                reason=f"RSI 买入信号：RSI={current_rsi:.2f} (超卖区回升)"
            )
        
        elif sell_signal or extreme_overbought:
            if extreme_overbought:
                signal_strength = min(1.0, (current_rsi - self.overbought_threshold) / 30)
            else:
                signal_strength = min(1.0, (prev_rsi - current_rsi) / 20)
            
            return TradeSignal(
                symbol=self.symbol,
                side=OrderSide.SELL,
                price=current_price,
                quantity=100,
                signal_strength=signal_strength,
                strategy=self.name,
                reason=f"RSI 卖出信号：RSI={current_rsi:.2f} (超买区回落)"
            )
        
        return None
    
    def calculate_rsi(self, data: List[Candlestick]) -> List[float]:
        """
        计算 RSI 指标
        
        RSI = 100 - (100 / (1 + RS))
        RS = 平均涨幅 / 平均跌幅
        """
        closes = np.array([c.close for c in data])
        deltas = np.diff(closes)
        
        rsi_values = []
        
        # 初始化
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        # 计算第一个平均涨幅和跌幅
        avg_gain = np.mean(gains[:self.rsi_period])
        avg_loss = np.mean(losses[:self.rsi_period])
        
        # 第一个 RSI
        if avg_loss == 0:
            rsi_values.append(100.0)
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            rsi_values.append(rsi)
        
        # 使用平滑移动平均计算后续 RSI
        for i in range(self.rsi_period, len(deltas)):
            avg_gain = (avg_gain * (self.rsi_period - 1) + gains[i]) / self.rsi_period
            avg_loss = (avg_loss * (self.rsi_period - 1) + losses[i]) / self.rsi_period
            
            if avg_loss == 0:
                rsi_values.append(100.0)
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
                rsi_values.append(rsi)
        
        return rsi_values
    
    async def get_current_status(self) -> dict:
        """获取策略当前状态"""
        data = await self.data_fetcher.get_historical_data(
            self.symbol, 
            days=self.rsi_period + 10
        )
        rsi_values = self.calculate_rsi(data)
        
        current_rsi = rsi_values[-1] if rsi_values else 50
        current_price = data[-1].close if data else 0
        
        # 判断市场状态
        if current_rsi < self.oversold_threshold:
            market_state = "oversold"
        elif current_rsi > self.overbought_threshold:
            market_state = "overbought"
        else:
            market_state = "neutral"
        
        return {
            "strategy": self.name,
            "symbol": self.symbol,
            "current_price": current_price,
            "rsi": current_rsi,
            "market_state": market_state,
            "oversold_threshold": self.oversold_threshold,
            "overbought_threshold": self.overbought_threshold,
            "distance_to_oversold": current_rsi - self.oversold_threshold,
            "distance_to_overbought": self.overbought_threshold - current_rsi
        }
