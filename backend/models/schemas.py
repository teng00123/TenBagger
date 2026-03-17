from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"


class OrderStatus(str, Enum):
    PENDING = "pending"
    EXECUTED = "executed"
    CANCELLED = "cancelled"


class StrategyType(str, Enum):
    MA = "ma"
    RSI = "rsi"
    MACD = "macd"
    BOLLINGER = "bollinger"


# 策略配置模型
class StrategyConfig(BaseModel):
    strategy_type: StrategyType
    symbol: str
    # MA 策略参数
    short_window: Optional[int] = Field(default=5, description="短期均线周期")
    long_window: Optional[int] = Field(default=20, description="长期均线周期")
    # RSI 策略参数
    rsi_period: Optional[int] = Field(default=14, description="RSI 周期")
    rsi_oversold: Optional[float] = Field(default=30.0, description="RSI 超卖线")
    rsi_overbought: Optional[float] = Field(default=70.0, description="RSI 超买线")
    # MACD 策略参数
    fast_period: Optional[int] = Field(default=12, description="MACD 快线周期")
    slow_period: Optional[int] = Field(default=26, description="MACD 慢线周期")
    signal_period: Optional[int] = Field(default=9, description="MACD 信号线周期")
    # 布林带策略参数
    bb_period: Optional[int] = Field(default=20, description="布林带均线周期")
    bb_k: Optional[float] = Field(default=2.0, description="布林带标准差倍数")


# 交易信号
class TradeSignal(BaseModel):
    symbol: str
    side: OrderSide
    price: float
    quantity: int
    signal_strength: float = Field(ge=0, le=1, description="信号强度 0-1")
    timestamp: datetime = Field(default_factory=datetime.now)
    strategy: str
    reason: str


# 订单模型
class Order(BaseModel):
    id: Optional[str] = None
    symbol: str
    side: OrderSide
    price: float
    quantity: int
    status: OrderStatus = OrderStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.now)
    executed_at: Optional[datetime] = None
    strategy: Optional[str] = None


# 持仓模型
class Position(BaseModel):
    symbol: str
    quantity: int
    average_price: float
    current_price: float
    unrealized_pnl: float
    realized_pnl: float = 0.0


# 账户信息
class AccountInfo(BaseModel):
    total_capital: float
    available_capital: float
    frozen_capital: float
    positions: List[Position]
    total_pnl: float
    pnl_rate: float


# K 线数据
class Candlestick(BaseModel):
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int


# 策略回测结果
class BacktestResult(BaseModel):
    strategy_name: str
    symbol: str
    total_return: float
    annual_return: float
    max_drawdown: float
    sharpe_ratio: float
    win_rate: float
    total_trades: int
    trades: List[Dict[str, Any]]


# API 响应
class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None
