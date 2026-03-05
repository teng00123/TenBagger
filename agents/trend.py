# agents/trend.py
from typing import Dict, List
from TenBagger.agents.base import BaseStrategy
from TenBagger.utils.helpers import calculate_momentum
from TenBagger.config import MOMENTUM_DAYS


class TrendStrategy(BaseStrategy):
    """ETF 动量轮动策略"""

    def analyze(self, data: Dict[str, List[float]]) -> str:
        """
        计算所有标的动量，选出最强者
        """
        momentum_scores = {}

        for name, prices in data.items():
            if len(prices) > 0:
                score = calculate_momentum(prices, MOMENTUM_DAYS)
                momentum_scores[name] = score

        # 找出得分最高的
        if not momentum_scores:
            return "HOLD"

        best_etf = max(momentum_scores, key=momentum_scores.get)
        best_score = momentum_scores[best_etf]

        print(f"当前动量排名: {momentum_scores}")

        # 如果最强者也是负收益，则空仓
        if best_score < 0:
            return "SWITCH_TO_CASH"

        return f"BUY_{best_etf}"
