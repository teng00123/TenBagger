from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from api.Trade.models import TradeSide

class TradeRecordCreate(BaseModel):
    """创建交易记录请求模型"""
    strategy_name: str
    symbol: str
    side: TradeSide
    price: float
    quantity: int
    amount: float
    timestamp: datetime
    profit: Optional[float] = None
    commission: float = 0.0
    notes: Optional[str] = None


class TradeRecordResponse(BaseModel):
    """交易记录响应模型"""
    id: int
    strategy_name: str
    symbol: str
    side: TradeSide
    price: float
    quantity: int
    amount: float
    timestamp: datetime
    profit: Optional[float]
    commission: float
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class StatisticsResponse(BaseModel):
    """统计数据响应模型"""
    total_trades: int
    total_profit: float
    win_rate: float
    total_commission: float
    buy_count: int
    sell_count: int

