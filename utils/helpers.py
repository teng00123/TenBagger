# utils/helpers.py
import pandas as pd


def calculate_momentum(prices: list, days: int) -> float:
    """
    计算动量 (过去N天的收益率)
    :param prices: 价格列表 (按时间升序)
    :param days: 回溯天数
    :return: 收益率
    """
    if len(prices) < days + 1:
        return 0.0

    # 取最近 days+1 天的数据
    relevant_prices = prices[-(days + 1):]
    roi = (relevant_prices[-1] - relevant_prices[0]) / relevant_prices[0]
    return roi
