from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
import numpy as np

from models.schemas import (
    StrategyConfig, StrategyType, BacktestResult, APIResponse
)
from strategies import build_strategy, list_strategies as _list_strategies
from utils.data_fetcher import DataFetcher

router = APIRouter(prefix="/api/strategies", tags=["strategies"])


def _config_to_params(config: StrategyConfig) -> Dict[str, Any]:
    """将 StrategyConfig 转为策略构造参数字典"""
    return {
        "short_window":  config.short_window,
        "long_window":   config.long_window,
        "rsi_period":    config.rsi_period,
        "oversold_threshold":  config.rsi_oversold,
        "overbought_threshold": config.rsi_overbought,
        "fast_period":   config.fast_period,
        "slow_period":   config.slow_period,
        "signal_period": config.signal_period,
        "period":        config.bb_period,
        "k":             config.bb_k,
    }


@router.get("/list", response_model=List[Dict[str, Any]])
async def list_strategies_endpoint():
    """获取所有已注册策略列表"""
    return _list_strategies()


@router.post("/analyze", response_model=Dict[str, Any])
async def analyze_market(config: StrategyConfig):
    """使用指定策略分析市场，返回交易信号"""
    try:
        strategy = build_strategy(
            config.strategy_type.value,
            config.symbol,
            _config_to_params(config),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    signal = await strategy.analyze()

    if signal:
        return {
            "has_signal": True,
            "signal": {
                "symbol":          signal.symbol,
                "side":            signal.side.value,
                "price":           signal.price,
                "quantity":        signal.quantity,
                "signal_strength": signal.signal_strength,
                "strategy":        signal.strategy,
                "reason":          signal.reason,
                "timestamp":       signal.timestamp.isoformat(),
            },
        }
    return {"has_signal": False, "signal": None, "message": "当前没有交易信号"}


@router.get("/status/{strategy_type}/{symbol}")
async def get_strategy_status(
    strategy_type: StrategyType,
    symbol: str,
    short_window: int = 5,
    long_window: int = 20,
    rsi_period: int = 14,
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9,
    bb_period: int = 20,
    bb_k: float = 2.0,
):
    """获取策略当前状态"""
    params = {
        "short_window": short_window,
        "long_window": long_window,
        "rsi_period": rsi_period,
        "fast_period": fast_period,
        "slow_period": slow_period,
        "signal_period": signal_period,
        "period": bb_period,
        "k": bb_k,
    }
    try:
        strategy = build_strategy(strategy_type.value, symbol, params)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    status = await strategy.get_current_status()
    return APIResponse(success=True, message="策略状态获取成功", data=status)


@router.post("/backtest", response_model=BacktestResult)
async def run_backtest(
    config: StrategyConfig,
    days: int = 60,
    initial_capital: float = 100000,
):
    """运行策略回测"""
    try:
        strategy = build_strategy(
            config.strategy_type.value,
            config.symbol,
            _config_to_params(config),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    data_fetcher = DataFetcher()
    data = await data_fetcher.get_historical_data(config.symbol, days=days)

    if len(data) < 20:
        raise HTTPException(status_code=400, detail="历史数据不足")

    capital = initial_capital
    positions: Dict[str, int] = {}
    trades = []
    equity_curve = [initial_capital]
    closes = np.array([c.close for c in data])

    for i in range(20, len(data)):
        window_data = data[: i + 1]
        sig = await strategy.analyze(data=window_data)

        if sig is not None:
            if sig.side.value == "buy" and config.symbol not in positions:
                qty = int(capital * 0.95 / closes[i])
                if qty > 0:
                    positions[config.symbol] = qty
                    capital -= qty * closes[i]
                    trades.append({"index": i, "type": "buy",  "price": closes[i], "quantity": qty, "date": data[i].timestamp.isoformat()})
            elif sig.side.value == "sell" and config.symbol in positions:
                qty = positions.pop(config.symbol)
                capital += qty * closes[i]
                trades.append({"index": i, "type": "sell", "price": closes[i], "quantity": qty, "date": data[i].timestamp.isoformat()})

        cur_equity = capital + sum(qty * closes[i] for sym, qty in positions.items())
        equity_curve.append(cur_equity)

    # 平掉所有持仓
    for sym, qty in positions.items():
        capital += qty * closes[-1]
        trades.append({"index": len(data) - 1, "type": "sell_close", "price": closes[-1], "quantity": qty, "date": data[-1].timestamp.isoformat()})

    total_return = (capital - initial_capital) / initial_capital * 100
    annual_return = total_return * (365 / days)

    eq = np.array(equity_curve)
    peak = np.maximum.accumulate(eq)
    max_drawdown = float(np.max((peak - eq) / (peak + 1e-9) * 100))

    rets = np.diff(equity_curve) / (np.array(equity_curve[:-1]) + 1e-9)
    sharpe = float(np.mean(rets) / np.std(rets) * np.sqrt(252)) if len(rets) > 1 and np.std(rets) > 0 else 0.0

    buys  = [t for t in trades if t["type"] == "buy"]
    sells = [t for t in trades if t["type"] in ("sell", "sell_close")]
    wins  = sum(1 for i, s in enumerate(sells) if i < len(buys) and s["price"] > buys[i]["price"])
    win_rate = wins / len(buys) * 100 if buys else 0.0

    return BacktestResult(
        strategy_name=strategy.name,
        symbol=config.symbol,
        total_return=round(total_return, 2),
        annual_return=round(annual_return, 2),
        max_drawdown=round(max_drawdown, 2),
        sharpe_ratio=round(sharpe, 2),
        win_rate=round(win_rate, 2),
        total_trades=len(trades),
        trades=trades,
    )


@router.get("/kline/{symbol}")
async def get_kline_data(
    symbol: str,
    days: int = 60,
    interval: str = "1d",
):
    """
    获取 K 线数据（供前端 CandlestickChart 使用）

    返回 ECharts candlestick 格式：
    {
      "dates": ["2024-01-01", ...],
      "ohlcv": [[open, close, low, high, volume], ...],   # ECharts 约定顺序
      "ma5":   [float | null, ...],
      "ma20":  [float | null, ...]
    }
    """
    fetcher = DataFetcher()
    data = await fetcher.get_historical_data(symbol, days=days, interval=interval)

    if not data:
        raise HTTPException(status_code=404, detail=f"无法获取 {symbol} 的行情数据")

    closes = np.array([c.close for c in data])

    def ma_series(window: int) -> list:
        result = []
        for i in range(len(closes)):
            if i + 1 < window:
                result.append(None)
            else:
                result.append(round(float(np.mean(closes[i + 1 - window:i + 1])), 4))
        return result

    dates = [c.timestamp.strftime("%Y-%m-%d") for c in data]
    # ECharts candlestick data item: [open, close, low, high]
    ohlcv = [
        [
            round(c.open,   4),
            round(c.close,  4),
            round(c.low,    4),
            round(c.high,   4),
            c.volume,
        ]
        for c in data
    ]

    return {
        "symbol":  symbol,
        "dates":   dates,
        "ohlcv":   ohlcv,
        "ma5":     ma_series(5),
        "ma20":    ma_series(20),
        "latest":  {
            "open":   data[-1].open,
            "high":   data[-1].high,
            "low":    data[-1].low,
            "close":  data[-1].close,
            "volume": data[-1].volume,
        },
    }


@router.get("/symbols")
async def get_supported_symbols():
    """获取支持的交易标的"""
    from config import Config
    return APIResponse(
        success=True,
        message="获取成功",
        data={
            "symbols": Config.DEFAULT_SYMBOLS,
            "descriptions": {
                "600519.SS": "贵州茅台",
                "000001.SZ": "平安银行",
                "BTC-USD":   "比特币",
            },
        },
    )


@router.get("/kline/{symbol}")
async def get_kline_data(symbol: str, days: int = 60):
    """获取 K 线数据（供前端图表使用）"""
    fetcher = DataFetcher()
    data = await fetcher.get_historical_data(symbol, days=days)
    return APIResponse(
        success=True,
        message="K 线数据获取成功",
        data=[
            {
                "timestamp": c.timestamp.isoformat(),
                "open":   c.open,
                "high":   c.high,
                "low":    c.low,
                "close":  c.close,
                "volume": c.volume,
            }
            for c in data
        ],
    )
