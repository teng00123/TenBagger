from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from utils.db import get_db_session
from .models import TradeRecord, TradeSide
from .pydantic_models import TradeRecordCreate, TradeRecordResponse, StatisticsResponse
from api.core.i18n import get_i18n, get_locale, I18n

# 创建路由实例
router = APIRouter(prefix="/api/trades", tags=["trades"])


# ==================== API 接口 ====================
@router.get("/", response_model=List[TradeRecordResponse])
async def get_trade_records(
        skip: int = Query(0, ge=0, description="跳过记录数"),
        limit: int = Query(100, ge=1, le=1000, description="返回记录数"),
        strategy: Optional[str] = Query(None, description="策略名称筛选"),
        symbol: Optional[str] = Query(None, description="股票代码筛选"),
        side: Optional[TradeSide] = Query(None, description="交易方向筛选"),
        start_date: Optional[datetime] = Query(None, description="开始日期"),
        end_date: Optional[datetime] = Query(None, description="结束日期"),
        db: Session = Depends(get_db_session)
):
    """获取交易记录列表"""
    query = db.query(TradeRecord)

    # 应用筛选条件
    if strategy:
        query = query.filter(TradeRecord.strategy_name.ilike(f"%{strategy}%"))
    if symbol:
        query = query.filter(TradeRecord.symbol == symbol)
    if side:
        query = query.filter(TradeRecord.side == side)
    if start_date:
        query = query.filter(TradeRecord.timestamp >= start_date)
    if end_date:
        query = query.filter(TradeRecord.timestamp <= end_date)

    # 按时间倒序排列并分页
    records = query.order_by(TradeRecord.timestamp.desc()).offset(skip).limit(limit).all()
    return records


@router.get("/{trade_id}", response_model=TradeRecordResponse)
async def get_trade_record(
        trade_id: int,
        db: Session = Depends(get_db_session),
        i18n: I18n = Depends(get_i18n)
):
    """获取单个交易记录详情"""
    record = db.query(TradeRecord).filter(TradeRecord.id == trade_id).first()
    if not record:
        raise HTTPException(status_code=404, detail=i18n.t("交易记录不存在"))
    return record


@router.post("/", response_model=TradeRecordResponse)
async def create_trade_record(
        trade_data: TradeRecordCreate,
        db: Session = Depends(get_db_session)
):
    """创建新的交易记录"""
    # 创建交易记录实例
    trade_record = TradeRecord(**trade_data.dict())

    # 保存到数据库
    db.add(trade_record)
    db.commit()
    db.refresh(trade_record)

    return trade_record


@router.put("/{trade_id}", response_model=TradeRecordResponse)
async def update_trade_record(
        trade_id: int,
        trade_data: TradeRecordCreate,
        db: Session = Depends(get_db_session)
):
    """更新交易记录"""
    record = db.query(TradeRecord).filter(TradeRecord.id == trade_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="交易记录不存在")

    # 更新字段
    for key, value in trade_data.dict().items():
        setattr(record, key, value)

    db.commit()
    db.refresh(record)

    return record


@router.delete("/{trade_id}")
async def delete_trade_record(
        trade_id: int,
        db: Session = Depends(get_db_session),
        i18n: I18n = Depends(get_i18n)
):
    """删除交易记录"""
    record = db.query(TradeRecord).filter(TradeRecord.id == trade_id).first()
    if not record:
        raise HTTPException(status_code=404, detail=i18n.t("交易记录不存在"))

    db.delete(record)
    db.commit()

    return {"message": i18n.t("交易记录删除成功")}


@router.get("/statistics/summary", response_model=StatisticsResponse)
async def get_trade_statistics(
        strategy: Optional[str] = Query(None, description="策略名称筛选"),
        symbol: Optional[str] = Query(None, description="股票代码筛选"),
        start_date: Optional[datetime] = Query(None, description="开始日期"),
        end_date: Optional[datetime] = Query(None, description="结束日期"),
        db: Session = Depends(get_db_session)
):
    """获取交易统计信息"""
    query = db.query(TradeRecord)

    # 应用筛选条件
    if strategy:
        query = query.filter(TradeRecord.strategy_name == strategy)
    if symbol:
        query = query.filter(TradeRecord.symbol == symbol)
    if start_date:
        query = query.filter(TradeRecord.timestamp >= start_date)
    if end_date:
        query = query.filter(TradeRecord.timestamp <= end_date)

    records = query.all()

    if not records:
        return StatisticsResponse(
            total_trades=0,
            total_profit=0.0,
            win_rate=0.0,
            total_commission=0.0,
            buy_count=0,
            sell_count=0
        )

    # 计算统计信息
    total_trades = len(records)
    total_profit = sum(r.profit or 0 for r in records)
    win_trades = sum(1 for r in records if r.profit and r.profit > 0)
    win_rate = (win_trades / total_trades * 100) if total_trades > 0 else 0
    total_commission = sum(r.commission for r in records)
    buy_count = sum(1 for r in records if r.side == TradeSide.BUY)
    sell_count = sum(1 for r in records if r.side == TradeSide.SELL)

    return StatisticsResponse(
        total_trades=total_trades,
        total_profit=total_profit,
        win_rate=win_rate,
        total_commission=total_commission,
        buy_count=buy_count,
        sell_count=sell_count
    )


@router.get("/statistics/recent")
async def get_recent_statistics(
        days: int = Query(30, ge=1, le=365, description="统计天数"),
        db: Session = Depends(get_db_session),
        i18n: I18n = Depends(get_i18n)
):
    """获取最近N天的交易统计"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    query = db.query(TradeRecord).filter(
        TradeRecord.timestamp >= start_date,
        TradeRecord.timestamp <= end_date
    )

    records = query.all()

    # 按日期分组统计
    daily_stats = {}
    for record in records:
        date_str = record.timestamp.strftime("%Y-%m-%d")
        if date_str not in daily_stats:
            daily_stats[date_str] = {
                "date": date_str,
                "trades": 0,
                "profit": 0.0,
                "buy_count": 0,
                "sell_count": 0
            }

        daily_stats[date_str]["trades"] += 1
        daily_stats[date_str]["profit"] += record.profit or 0
        if record.side == TradeSide.BUY:
            daily_stats[date_str]["buy_count"] += 1
        else:
            daily_stats[date_str]["sell_count"] += 1

    return {
        "period": i18n.t("最近{}天".format(days)),
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "daily_stats": list(daily_stats.values())
    }