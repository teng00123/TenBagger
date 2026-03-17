"""
strategies/__init__.py — 策略注册中心

新增策略只需：
1. 在 backend/strategies/ 下新建 xxx_strategy.py
2. 在 REGISTRY 字典中加一行
无需修改 router。
"""
from typing import Any, Dict, Type

from strategies.ma_strategy import MAStrategy
from strategies.rsi_strategy import RSIStrategy
from strategies.macd_strategy import MACDStrategy
from strategies.bollinger_strategy import BollingerStrategy

# ── 策略元信息注册表 ─────────────────────────────────────────────
# key: strategy_type 字符串（与 StrategyType enum 保持一致）
REGISTRY: Dict[str, Dict[str, Any]] = {
    "ma": {
        "class": MAStrategy,
        "name": "均线交叉策略",
        "description": "基于短期和长期均线金叉/死叉产生交易信号",
        "parameters": {
            "short_window": {"type": "int", "default": 5, "description": "短期均线周期"},
            "long_window":  {"type": "int", "default": 20, "description": "长期均线周期"},
        },
    },
    "rsi": {
        "class": RSIStrategy,
        "name": "RSI 超买超卖策略",
        "description": "基于相对强弱指标判断超买超卖区域",
        "parameters": {
            "rsi_period":      {"type": "int",   "default": 14,   "description": "RSI 计算周期"},
            "rsi_oversold":    {"type": "float", "default": 30.0, "description": "超卖线"},
            "rsi_overbought":  {"type": "float", "default": 70.0, "description": "超买线"},
        },
    },
    "macd": {
        "class": MACDStrategy,
        "name": "MACD 金叉死叉策略",
        "description": "基于 MACD 指标金叉买入、死叉卖出",
        "parameters": {
            "fast_period":   {"type": "int", "default": 12, "description": "快线 EMA 周期"},
            "slow_period":   {"type": "int", "default": 26, "description": "慢线 EMA 周期"},
            "signal_period": {"type": "int", "default": 9,  "description": "信号线 EMA 周期"},
        },
    },
    "bollinger": {
        "class": BollingerStrategy,
        "name": "布林带策略",
        "description": "价格触及布林带上下轨时产生交易信号",
        "parameters": {
            "period": {"type": "int",   "default": 20,  "description": "布林带均线周期"},
            "k":      {"type": "float", "default": 2.0, "description": "标准差倍数"},
        },
    },
}


def build_strategy(strategy_type: str, symbol: str, params: Dict[str, Any]):
    """
    根据 strategy_type 实例化策略对象。
    params 中只传该策略支持的参数，多余的忽略。
    """
    entry = REGISTRY.get(strategy_type)
    if entry is None:
        raise ValueError(f"未知策略类型: {strategy_type}，可用: {list(REGISTRY)}")

    cls: Type = entry["class"]
    supported = set(entry["parameters"].keys()) | {"symbol"}
    filtered = {k: v for k, v in {**params, "symbol": symbol}.items() if k in supported}

    return cls(**filtered)


def list_strategies():
    """返回所有注册策略的描述信息（不含 class 引用）"""
    return [
        {
            "type": key,
            "name": meta["name"],
            "description": meta["description"],
            "parameters": meta["parameters"],
        }
        for key, meta in REGISTRY.items()
    ]
