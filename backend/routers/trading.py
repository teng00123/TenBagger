from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from datetime import datetime
import uuid

from models.schemas import (
    Order, OrderSide, OrderStatus, Position, 
    AccountInfo, TradeSignal, APIResponse
)
from config import Config

router = APIRouter(prefix="/api/trading", tags=["trading"])

# 模拟账户状态
class TradingState:
    def __init__(self):
        self.capital = Config.INITIAL_CAPITAL
        self.frozen_capital = 0
        self.positions: Dict[str, Position] = {}
        self.orders: List[Order] = []
        self.trade_history: List[Dict[str, Any]] = []
    
    def get_account_info(self) -> AccountInfo:
        total_position_value = sum(
            p.quantity * p.current_price for p in self.positions.values()
        )
        total_capital = self.capital + total_position_value
        total_pnl = sum(p.unrealized_pnl + p.realized_pnl for p in self.positions.values())
        pnl_rate = (total_pnl / Config.INITIAL_CAPITAL * 100) if Config.INITIAL_CAPITAL else 0
        
        return AccountInfo(
            total_capital=total_capital,
            available_capital=self.capital - self.frozen_capital,
            frozen_capital=self.frozen_capital,
            positions=list(self.positions.values()),
            total_pnl=total_pnl,
            pnl_rate=pnl_rate
        )

# 全局交易状态
trading_state = TradingState()


@router.get("/account", response_model=AccountInfo)
async def get_account():
    """获取账户信息"""
    return trading_state.get_account_info()


@router.post("/order", response_model=APIResponse)
async def place_order(order: Order):
    """
    下单交易
    
    - **symbol**: 交易标的
    - **side**: 买卖方向 (buy/sell)
    - **price**: 价格
    - **quantity**: 数量
    """
    order.id = str(uuid.uuid4())[:8]
    
    # 计算所需资金
    required_capital = order.price * order.quantity
    
    if order.side == OrderSide.BUY:
        # 检查资金是否充足
        if required_capital > trading_state.capital:
            raise HTTPException(
                status_code=400, 
                detail=f"资金不足，需要 {required_capital:.2f}, 可用 {trading_state.capital:.2f}"
            )
        
        # 冻结资金
        trading_state.frozen_capital += required_capital
        
        # 更新或创建持仓
        if order.symbol in trading_state.positions:
            pos = trading_state.positions[order.symbol]
            total_cost = pos.quantity * pos.average_price + required_capital
            pos.quantity += order.quantity
            pos.average_price = total_cost / pos.quantity
        else:
            trading_state.positions[order.symbol] = Position(
                symbol=order.symbol,
                quantity=order.quantity,
                average_price=order.price,
                current_price=order.price,
                unrealized_pnl=0
            )
    
    elif order.side == OrderSide.SELL:
        # 检查持仓是否充足
        if order.symbol not in trading_state.positions:
            raise HTTPException(status_code=400, detail=f"没有 {order.symbol} 的持仓")
        
        pos = trading_state.positions[order.symbol]
        if pos.quantity < order.quantity:
            raise HTTPException(
                status_code=400, 
                detail=f"持仓不足，持有 {pos.quantity}, 欲卖出 {order.quantity}"
            )
        
        # 计算盈亏
        pnl = (order.price - pos.average_price) * order.quantity
        pos.realized_pnl += pnl
        
        # 更新持仓
        pos.quantity -= order.quantity
        if pos.quantity == 0:
            del trading_state.positions[order.symbol]
        else:
            pos.current_price = order.price
        
        # 增加可用资金
        trading_state.capital += order.price * order.quantity
    
    # 更新订单状态
    order.status = OrderStatus.EXECUTED
    order.executed_at = datetime.now()
    trading_state.orders.append(order)
    
    # 记录交易历史
    trading_state.trade_history.append({
        "id": order.id,
        "symbol": order.symbol,
        "side": order.side.value,
        "price": order.price,
        "quantity": order.quantity,
        "executed_at": order.executed_at.isoformat(),
        "strategy": order.strategy
    })
    
    return APIResponse(
        success=True,
        message=f"订单已执行：{order.side.value} {order.symbol} {order.quantity}股 @ {order.price}",
        data={"order_id": order.id}
    )


@router.get("/orders", response_model=List[Order])
async def get_orders(limit: int = 50):
    """获取订单列表"""
    return trading_state.orders[-limit:]


@router.get("/history", response_model=List[Dict[str, Any]])
async def get_trade_history(limit: int = 50):
    """获取交易历史"""
    return trading_state.trade_history[-limit:]


@router.post("/positions/update")
async def update_positions(prices: Dict[str, float]):
    """
    更新持仓的当前价格
    
    用于更新持仓的未实现盈亏
    """
    for symbol, price in prices.items():
        if symbol in trading_state.positions:
            pos = trading_state.positions[symbol]
            pos.current_price = price
            pos.unrealized_pnl = (price - pos.average_price) * pos.quantity
    
    return APIResponse(
        success=True,
        message=f"已更新 {len(prices)} 个持仓价格"
    )
