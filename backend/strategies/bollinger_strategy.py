import numpy as np
from typing import List, Optional

from models.schemas import Candlestick, TradeSignal, OrderSide
from utils.data_fetcher import DataFetcher


class BollingerStrategy:
    """
    布林带策略（Bollinger Bands）

    策略逻辑：
    - 中轨 = SMA(close, period)
    - 上轨 = 中轨 + k * std
    - 下轨 = 中轨 - k * std
    - 价格触及下轨（超卖）→ 买入信号
    - 价格触及上轨（超买）→ 卖出信号
    """

    def __init__(
        self,
        period: int = 20,
        k: float = 2.0,
        symbol: str = "600519.SS",
    ):
        self.period = period
        self.k = k
        self.symbol = symbol
        self.data_fetcher = DataFetcher()
        self.name = f"BB({period},{k})"

    # ── 核心计算 ──────────────────────────────────

    def calculate_bands(
        self, data: List[Candlestick]
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        计算布林带三条线
        Returns: (upper, middle, lower)  shape = (len(data),)
        前 period-1 个元素为 NaN
        """
        closes = np.array([c.close for c in data], dtype=float)
        n = len(closes)
        upper = np.full(n, np.nan)
        middle = np.full(n, np.nan)
        lower = np.full(n, np.nan)

        for i in range(self.period - 1, n):
            window = closes[i - self.period + 1 : i + 1]
            sma = np.mean(window)
            std = np.std(window, ddof=0)
            middle[i] = sma
            upper[i] = sma + self.k * std
            lower[i] = sma - self.k * std

        return upper, middle, lower

    def _band_width(self, upper: float, lower: float, middle: float) -> float:
        """带宽（归一化）"""
        return (upper - lower) / middle if middle else 0.0

    # ── 信号生成 ──────────────────────────────────

    async def analyze(
        self, data: Optional[List[Candlestick]] = None
    ) -> Optional[TradeSignal]:
        if data is None:
            data = await self.data_fetcher.get_historical_data(
                self.symbol, days=self.period + 20
            )

        if len(data) < self.period + 2:
            return None

        upper, middle, lower = self.calculate_bands(data)

        curr_close = data[-1].close
        prev_close = data[-2].close
        curr_upper = upper[-1]
        curr_lower = lower[-1]
        curr_mid = middle[-1]

        if np.isnan(curr_upper):
            return None

        # 触及下轨（前一根在轨外，当前回归轨内）
        touch_lower = prev_close <= lower[-2] and curr_close > lower[-1]
        # 触及上轨
        touch_upper = prev_close >= upper[-2] and curr_close < upper[-1]

        # 也支持价格在轨外的强信号
        below_lower = curr_close < curr_lower
        above_upper = curr_close > curr_upper

        if touch_lower or below_lower:
            # 信号强度：离下轨越远越强
            dist = (curr_mid - curr_close) / (curr_mid - curr_lower + 1e-9)
            strength = min(1.0, max(0.0, dist))
            return TradeSignal(
                symbol=self.symbol,
                side=OrderSide.BUY,
                price=curr_close,
                quantity=100,
                signal_strength=round(strength, 4),
                strategy=self.name,
                reason=(
                    f"布林带下轨信号：价格({curr_close:.2f}) 触及下轨({curr_lower:.2f})，"
                    f"带宽={self._band_width(curr_upper, curr_lower, curr_mid):.4f}"
                ),
            )

        if touch_upper or above_upper:
            dist = (curr_close - curr_mid) / (curr_upper - curr_mid + 1e-9)
            strength = min(1.0, max(0.0, dist))
            return TradeSignal(
                symbol=self.symbol,
                side=OrderSide.SELL,
                price=curr_close,
                quantity=100,
                signal_strength=round(strength, 4),
                strategy=self.name,
                reason=(
                    f"布林带上轨信号：价格({curr_close:.2f}) 触及上轨({curr_upper:.2f})，"
                    f"带宽={self._band_width(curr_upper, curr_lower, curr_mid):.4f}"
                ),
            )

        return None

    async def get_current_status(self) -> dict:
        data = await self.data_fetcher.get_historical_data(
            self.symbol, days=self.period + 20
        )
        upper, middle, lower = self.calculate_bands(data)

        curr_close = data[-1].close if data else 0.0
        curr_upper = float(upper[-1]) if not np.isnan(upper[-1]) else 0.0
        curr_mid = float(middle[-1]) if not np.isnan(middle[-1]) else 0.0
        curr_lower = float(lower[-1]) if not np.isnan(lower[-1]) else 0.0

        if curr_close > curr_upper:
            market_state = "overbought"
        elif curr_close < curr_lower:
            market_state = "oversold"
        else:
            pct = (curr_close - curr_lower) / (curr_upper - curr_lower + 1e-9)
            market_state = "upper_half" if pct > 0.5 else "lower_half"

        return {
            "strategy": self.name,
            "symbol": self.symbol,
            "current_price": curr_close,
            "upper_band": round(curr_upper, 4),
            "middle_band": round(curr_mid, 4),
            "lower_band": round(curr_lower, 4),
            "band_width": round(self._band_width(curr_upper, curr_lower, curr_mid), 6),
            "market_state": market_state,
        }
