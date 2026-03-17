import numpy as np
from typing import List, Optional

from models.schemas import Candlestick, TradeSignal, OrderSide
from utils.data_fetcher import DataFetcher


class MACDStrategy:
    """
    MACD 策略（Moving Average Convergence Divergence）

    策略逻辑：
    - MACD 线（DIF）= EMA(12) - EMA(26)
    - 信号线（DEA）= EMA(MACD, 9)
    - 柱状图（HIST）= MACD - 信号线
    - 金叉：MACD 上穿信号线 → 买入
    - 死叉：MACD 下穿信号线 → 卖出
    """

    def __init__(
        self,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
        symbol: str = "600519.SS",
    ):
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period
        self.symbol = symbol
        self.data_fetcher = DataFetcher()
        self.name = f"MACD({fast_period},{slow_period},{signal_period})"

    # ── 核心计算 ──────────────────────────────────

    def _ema(self, values: np.ndarray, period: int) -> np.ndarray:
        """指数移动平均"""
        alpha = 2.0 / (period + 1)
        ema = np.empty_like(values)
        ema[0] = values[0]
        for i in range(1, len(values)):
            ema[i] = alpha * values[i] + (1 - alpha) * ema[i - 1]
        return ema

    def calculate_macd(
        self, data: List[Candlestick]
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        计算 MACD 三条线
        Returns: (macd_line, signal_line, histogram)
        """
        closes = np.array([c.close for c in data], dtype=float)
        ema_fast = self._ema(closes, self.fast_period)
        ema_slow = self._ema(closes, self.slow_period)
        macd_line = ema_fast - ema_slow
        signal_line = self._ema(macd_line, self.signal_period)
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram

    # ── 信号生成 ──────────────────────────────────

    async def analyze(
        self, data: Optional[List[Candlestick]] = None
    ) -> Optional[TradeSignal]:
        min_bars = self.slow_period + self.signal_period + 5
        if data is None:
            data = await self.data_fetcher.get_historical_data(
                self.symbol, days=min_bars + 10
            )

        if len(data) < min_bars:
            return None

        macd_line, signal_line, histogram = self.calculate_macd(data)

        curr_macd, prev_macd = macd_line[-1], macd_line[-2]
        curr_sig, prev_sig = signal_line[-1], signal_line[-2]
        current_price = data[-1].close

        golden_cross = prev_macd <= prev_sig and curr_macd > curr_sig
        death_cross = prev_macd >= prev_sig and curr_macd < curr_sig

        if golden_cross:
            strength = min(1.0, abs(curr_macd - curr_sig) / (abs(curr_sig) + 1e-9) * 5)
            return TradeSignal(
                symbol=self.symbol,
                side=OrderSide.BUY,
                price=current_price,
                quantity=100,
                signal_strength=round(strength, 4),
                strategy=self.name,
                reason=(
                    f"MACD 金叉：DIF({curr_macd:.4f}) 上穿 DEA({curr_sig:.4f})，"
                    f"HIST={histogram[-1]:.4f}"
                ),
            )

        if death_cross:
            strength = min(1.0, abs(curr_sig - curr_macd) / (abs(curr_sig) + 1e-9) * 5)
            return TradeSignal(
                symbol=self.symbol,
                side=OrderSide.SELL,
                price=current_price,
                quantity=100,
                signal_strength=round(strength, 4),
                strategy=self.name,
                reason=(
                    f"MACD 死叉：DIF({curr_macd:.4f}) 下穿 DEA({curr_sig:.4f})，"
                    f"HIST={histogram[-1]:.4f}"
                ),
            )

        return None

    async def get_current_status(self) -> dict:
        data = await self.data_fetcher.get_historical_data(
            self.symbol, days=self.slow_period + self.signal_period + 15
        )
        macd_line, signal_line, histogram = self.calculate_macd(data)

        curr_macd = float(macd_line[-1])
        curr_sig = float(signal_line[-1])
        curr_hist = float(histogram[-1])
        current_price = data[-1].close if data else 0.0

        if curr_macd > curr_sig:
            trend = "bullish"
        elif curr_macd < curr_sig:
            trend = "bearish"
        else:
            trend = "neutral"

        return {
            "strategy": self.name,
            "symbol": self.symbol,
            "current_price": current_price,
            "macd": round(curr_macd, 6),
            "signal": round(curr_sig, 6),
            "histogram": round(curr_hist, 6),
            "trend": trend,
        }
