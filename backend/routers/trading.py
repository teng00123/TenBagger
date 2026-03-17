"""
routers/trading.py — 交易路由（SQLite 持久化版）

v0.2 P1-5: 用 SQLAlchemy async + aiosqlite 替换全局内存变量，
重启后持仓/订单历史全部保留。
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any
from datetime import datetime
import uuid

from models.schemas import (
    Order, OrderSide, OrderStatus, Position,
    AccountInfo, APIResponse,
)
from config import Config
from db.database import get_db, OrderModel, PositionModel, TradeHistoryModel, AccountModel

router = APIRouter(prefix="/api/trading", tags=["trading"])


# ── 内部辅助 ──────────────────────────────────────────────────────

async def _get_account(session: AsyncSession) -> AccountModel:
    result = await session.execute(select(AccountModel).where(AccountModel.id == 1))
    acct = result.scalar_one_or_none()
    if acct is None:
        acct = AccountModel(id=1, capital=Config.INITIAL_CAPITAL, frozen_capital=0.0)
        session.add(acct)
        await session.flush()
    return acct


async def _get_position(session: AsyncSession, symbol: str) -> PositionModel | None:
    result = await session.execute(
        select(PositionModel).where(PositionModel.symbol == symbol)
    )
    return result.scalar_one_or_none()


# ── 路由 ─────────────────────────────────────────────────────────

@router.get("/account", response_model=AccountInfo)
async def get_account(session: AsyncSession = Depends(get_db)):
    """获取账户信息"""
    acct = await _get_account(session)

    result = await session.execute(select(PositionModel))
    pos_models = result.scalars().all()

    positions = [
        Position(
            symbol=p.symbol,
            quantity=p.quantity,
            average_price=p.average_price,
            current_price=p.current_price,
            unrealized_pnl=p.unrealized_pnl,
            realized_pnl=p.realized_pnl,
        )
        for p in pos_models
    ]

    total_position_value = sum(p.quantity * p.current_price for p in pos_models)
    total_capital = acct.capital + total_position_value
    total_pnl = sum(p.unrealized_pnl + p.realized_pnl for p in pos_models)
    pnl_rate = (total_pnl / Config.INITIAL_CAPITAL * 100) if Config.INITIAL_CAPITAL else 0

    return AccountInfo(
        total_capital=total_capital,
        available_capital=acct.capital - acct.frozen_capital,
        frozen_capital=acct.frozen_capital,
        positions=positions,
        total_pnl=total_pnl,
        pnl_rate=pnl_rate,
    )


@router.post("/order", response_model=APIResponse)
async def place_order(order: Order, session: AsyncSession = Depends(get_db)):
    """下单交易"""
    order.id = str(uuid.uuid4())[:8]
    acct = await _get_account(session)
    required_capital = order.price * order.quantity

    if order.side == OrderSide.BUY:
        available = acct.capital - acct.frozen_capital
        if required_capital > available:
            raise HTTPException(
                status_code=400,
                detail=f"资金不足，需要 {required_capital:.2f}, 可用 {available:.2f}",
            )

        acct.frozen_capital += required_capital
        acct.capital -= required_capital

        pos = await _get_position(session, order.symbol)
        if pos:
            total_cost = pos.quantity * pos.average_price + required_capital
            pos.quantity += order.quantity
            pos.average_price = total_cost / pos.quantity
            pos.current_price = order.price
            pos.unrealized_pnl = (pos.current_price - pos.average_price) * pos.quantity
            pos.updated_at = datetime.utcnow()
        else:
            session.add(
                PositionModel(
                    symbol=order.symbol,
                    quantity=order.quantity,
                    average_price=order.price,
                    current_price=order.price,
                    unrealized_pnl=0.0,
                    realized_pnl=0.0,
                )
            )

    elif order.side == OrderSide.SELL:
        pos = await _get_position(session, order.symbol)
        if pos is None:
            raise HTTPException(status_code=400, detail=f"没有 {order.symbol} 的持仓")
        if pos.quantity < order.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"持仓不足，持有 {pos.quantity}, 欲卖出 {order.quantity}",
            )

        pnl = (order.price - pos.average_price) * order.quantity
        pos.realized_pnl += pnl
        pos.quantity -= order.quantity

        proceeds = order.price * order.quantity
        acct.capital += proceeds
        acct.frozen_capital = max(0.0, acct.frozen_capital - proceeds)

        if pos.quantity == 0:
            await session.delete(pos)
        else:
            pos.current_price = order.price
            pos.unrealized_pnl = (pos.current_price - pos.average_price) * pos.quantity
            pos.updated_at = datetime.utcnow()

    # 持久化订单
    order.status = OrderStatus.EXECUTED
    order.executed_at = datetime.now()

    session.add(
        OrderModel(
            id=order.id,
            symbol=order.symbol,
            side=order.side.value,
            price=order.price,
            quantity=order.quantity,
            status=order.status.value,
            strategy=order.strategy,
            created_at=datetime.utcnow(),
            executed_at=order.executed_at,
        )
    )
    session.add(
        TradeHistoryModel(
            id=order.id,
            symbol=order.symbol,
            side=order.side.value,
            price=order.price,
            quantity=order.quantity,
            strategy=order.strategy,
            executed_at=order.executed_at,
        )
    )

    await session.commit()

    return APIResponse(
        success=True,
        message=f"订单已执行：{order.side.value} {order.symbol} {order.quantity}股 @ {order.price}",
        data={"order_id": order.id},
    )


@router.get("/orders", response_model=List[Order])
async def get_orders(limit: int = 50, session: AsyncSession = Depends(get_db)):
    """获取订单列表"""
    result = await session.execute(
        select(OrderModel).order_by(OrderModel.created_at.desc()).limit(limit)
    )
    rows = result.scalars().all()
    return [
        Order(
            id=r.id,
            symbol=r.symbol,
            side=OrderSide(r.side),
            price=r.price,
            quantity=r.quantity,
            status=OrderStatus(r.status),
            strategy=r.strategy,
            executed_at=r.executed_at,
        )
        for r in rows
    ]


@router.get("/history", response_model=List[Dict[str, Any]])
async def get_trade_history(limit: int = 50, session: AsyncSession = Depends(get_db)):
    """获取交易历史"""
    result = await session.execute(
        select(TradeHistoryModel).order_by(TradeHistoryModel.executed_at.desc()).limit(limit)
    )
    rows = result.scalars().all()
    return [
        {
            "id": r.id,
            "symbol": r.symbol,
            "side": r.side,
            "price": r.price,
            "quantity": r.quantity,
            "executed_at": r.executed_at.isoformat() if r.executed_at else None,
            "strategy": r.strategy,
        }
        for r in rows
    ]


@router.post("/positions/update", response_model=APIResponse)
async def update_positions(
    prices: Dict[str, float],
    session: AsyncSession = Depends(get_db),
):
    """更新持仓的当前价格及未实现盈亏"""
    updated = 0
    for symbol, price in prices.items():
        pos = await _get_position(session, symbol)
        if pos:
            pos.current_price = price
            pos.unrealized_pnl = (price - pos.average_price) * pos.quantity
            pos.updated_at = datetime.utcnow()
            updated += 1

    await session.commit()
    return APIResponse(success=True, message=f"已更新 {updated} 个持仓价格")
