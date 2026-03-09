from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
import numpy as np

from models.schemas import (
    StrategyConfig, StrategyType, TradeSignal, 
    BacktestResult, APIResponse, Candlestick
)
from strategies.ma_strategy import MAStrategy
from strategies.rsi_strategy import RSIStrategy
from utils.data_fetcher import DataFetcher

router = APIRouter(prefix="/api/strategies", tags=["strategies"])

# 策略实例缓存
strategy_cache: Dict[str, Any] = {}


def get_strategy(config: StrategyConfig):
    """根据配置获取策略实例"""
    cache_key = f"{config.strategy_type.value}_{config.symbol}"
    
    if cache_key not in strategy_cache:
        if config.strategy_type == StrategyType.MA:
            strategy_cache[cache_key] = MAStrategy(
                short_window=config.short_window,
                long_window=config.long_window,
                symbol=config.symbol
            )
        elif config.strategy_type == StrategyType.RSI:
            strategy_cache[cache_key] = RSIStrategy(
                rsi_period=config.rsi_period,
                oversold_threshold=config.rsi_oversold,
                overbought_threshold=config.rsi_overbought,
                symbol=config.symbol
            )
    
    return strategy_cache[cache_key]


@router.get("/list", response_model=List[Dict[str, Any]])
async def list_strategies():
    """获取可用策略列表"""
    return [
        {
            "type": "ma",
            "name": "均线交叉策略",
            "description": "基于短期和长期均线交叉产生交易信号",
            "parameters": {
                "short_window": {"type": "int", "default": 5, "description": "短期均线周期"},
                "long_window": {"type": "int", "default": 20, "description": "长期均线周期"}
            }
        },
        {
            "type": "rsi",
            "name": "RSI 策略",
            "description": "基于相对强弱指标判断超买超卖",
            "parameters": {
                "rsi_period": {"type": "int", "default": 14, "description": "RSI 计算周期"},
                "rsi_oversold": {"type": "float", "default": 30.0, "description": "超卖线"},
                "rsi_overbought": {"type": "float", "default": 70.0, "description": "超买线"}
            }
        }
    ]


@router.post("/analyze", response_model=Dict[str, Any])
async def analyze_market(config: StrategyConfig):
    """
    使用指定策略分析市场
    
    返回当前市场的交易信号
    """
    strategy = get_strategy(config)
    signal = await strategy.analyze()
    
    if signal:
        return {
            "has_signal": True,
            "signal": {
                "symbol": signal.symbol,
                "side": signal.side.value,
                "price": signal.price,
                "quantity": signal.quantity,
                "signal_strength": signal.signal_strength,
                "strategy": signal.strategy,
                "reason": signal.reason,
                "timestamp": signal.timestamp.isoformat()
            }
        }
    else:
        return {
            "has_signal": False,
            "signal": None,
            "message": "当前没有交易信号"
        }


@router.get("/status/{strategy_type}/{symbol}")
async def get_strategy_status(
    strategy_type: StrategyType,
    symbol: str,
    short_window: int = 5,
    long_window: int = 20,
    rsi_period: int = 14
):
    """获取策略当前状态"""
    config = StrategyConfig(
        strategy_type=strategy_type,
        symbol=symbol,
        short_window=short_window,
        long_window=long_window,
        rsi_period=rsi_period
    )
    
    strategy = get_strategy(config)
    status = await strategy.get_current_status()
    
    return APIResponse(
        success=True,
        message="策略状态获取成功",
        data=status
    )


@router.post("/backtest", response_model=BacktestResult)
async def run_backtest(
    config: StrategyConfig,
    days: int = 60,
    initial_capital: float = 100000
):
    """
    运行策略回测
    
    使用历史数据模拟策略表现
    """
    strategy = get_strategy(config)
    data_fetcher = DataFetcher(use_mock=True)
    
    # 获取历史数据
    data = await data_fetcher.get_historical_data(config.symbol, days=days)
    
    if len(data) < 20:
        raise HTTPException(status_code=400, detail="历史数据不足")
    
    # 模拟回测
    capital = initial_capital
    positions: Dict[str, int] = {}
    trades = []
    equity_curve = [initial_capital]
    
    closes = np.array([c.close for c in data])
    
    # 简单回测逻辑
    for i in range(20, len(data)):
        window_data = data[:i+1]
        
        # 创建临时策略实例进行分析
        temp_strategy = get_strategy(config)
        
        # 这里简化处理，实际应该用历史数据重新计算
        # 为了演示，我们使用简单的规则
        if config.strategy_type == StrategyType.MA:
            short_ma = np.mean(closes[i-config.short_window:i])
            long_ma = np.mean(closes[i-config.long_window:i])
            
            if short_ma > long_ma and config.symbol not in positions:
                # 买入
                quantity = int(capital * 0.95 / closes[i])
                if quantity > 0:
                    positions[config.symbol] = quantity
                    capital -= quantity * closes[i]
                    trades.append({
                        "index": i,
                        "type": "buy",
                        "price": closes[i],
                        "quantity": quantity,
                        "date": data[i].timestamp.isoformat()
                    })
            
            elif short_ma < long_ma and config.symbol in positions:
                # 卖出
                quantity = positions.pop(config.symbol)
                capital += quantity * closes[i]
                trades.append({
                    "index": i,
                    "type": "sell",
                    "price": closes[i],
                    "quantity": quantity,
                    "date": data[i].timestamp.isoformat()
                })
        
        elif config.strategy_type == StrategyType.RSI:
            # 简化 RSI 计算
            deltas = np.diff(closes[max(0, i-config.rsi_period-1):i+1])
            gains = np.where(deltas > 0, deltas, 0)
            losses = np.where(deltas < 0, -deltas, 0)
            
            if len(gains) > 0 and len(losses) > 0:
                avg_gain = np.mean(gains)
                avg_loss = np.mean(losses)
                
                if avg_loss > 0:
                    rs = avg_gain / avg_loss
                    rsi = 100 - (100 / (1 + rs))
                else:
                    rsi = 100
                
                if rsi < config.rsi_oversold and config.symbol not in positions:
                    quantity = int(capital * 0.95 / closes[i])
                    if quantity > 0:
                        positions[config.symbol] = quantity
                        capital -= quantity * closes[i]
                        trades.append({
                            "index": i,
                            "type": "buy",
                            "price": closes[i],
                            "quantity": quantity,
                            "date": data[i].timestamp.isoformat()
                        })
                
                elif rsi > config.rsi_overbought and config.symbol in positions:
                    quantity = positions.pop(config.symbol)
                    capital += quantity * closes[i]
                    trades.append({
                        "index": i,
                        "type": "sell",
                        "price": closes[i],
                        "quantity": quantity,
                        "date": data[i].timestamp.isoformat()
                    })
        
        # 计算当前权益
        current_equity = capital
        for sym, qty in positions.items():
            current_equity += qty * closes[i]
        equity_curve.append(current_equity)
    
    # 平掉所有持仓
    for sym, qty in positions.items():
        capital += qty * closes[-1]
        trades.append({
            "index": len(data) - 1,
            "type": "sell_close",
            "price": closes[-1],
            "quantity": qty,
            "date": data[-1].timestamp.isoformat()
        })
    
    # 计算回测指标
    total_return = (capital - initial_capital) / initial_capital * 100
    
    # 年化收益率
    annual_return = total_return * (365 / days)
    
    # 最大回撤
    equity_array = np.array(equity_curve)
    peak = np.maximum.accumulate(equity_array)
    drawdown = (peak - equity_array) / peak * 100
    max_drawdown = np.max(drawdown)
    
    # 夏普比率 (简化计算)
    returns = np.diff(equity_curve) / equity_curve[:-1]
    if len(returns) > 1 and np.std(returns) > 0:
        sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252)
    else:
        sharpe_ratio = 0
    
    # 胜率
    buy_trades = [t for t in trades if t["type"] == "buy"]
    sell_trades = [t for t in trades if t["type"] in ["sell", "sell_close"]]
    winning_trades = 0
    
    for i, sell in enumerate(sell_trades):
        if i < len(buy_trades):
            if sell["price"] > buy_trades[i]["price"]:
                winning_trades += 1
    
    win_rate = (winning_trades / len(buy_trades) * 100) if buy_trades else 0
    
    return BacktestResult(
        strategy_name=strategy.name,
        symbol=config.symbol,
        total_return=round(total_return, 2),
        annual_return=round(annual_return, 2),
        max_drawdown=round(max_drawdown, 2),
        sharpe_ratio=round(sharpe_ratio, 2),
        win_rate=round(win_rate, 2),
        total_trades=len(trades),
        trades=trades
    )


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
                "BTC-USD": "比特币"
            }
        }
    )
