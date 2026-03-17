"""
db/database.py — SQLite 持久化层（SQLAlchemy 2.x async）

持久化内容：
- orders       订单历史
- positions    当前持仓
- trade_history 交易记录
"""
import os
from datetime import datetime
from typing import AsyncGenerator

from sqlalchemy import Column, String, Float, Integer, DateTime, Boolean, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

DB_PATH = os.getenv("DB_PATH", "tenbagger.db")
DATABASE_URL = f"sqlite+aiosqlite:///{DB_PATH}"

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


# ── ORM 模型 ────────────────────────────────────────────────────

class OrderModel(Base):
    __tablename__ = "orders"

    id            = Column(String, primary_key=True)
    symbol        = Column(String, nullable=False)
    side          = Column(String, nullable=False)       # buy / sell
    price         = Column(Float,  nullable=False)
    quantity      = Column(Integer, nullable=False)
    status        = Column(String, default="executed")
    strategy      = Column(String, nullable=True)
    created_at    = Column(DateTime, default=datetime.utcnow)
    executed_at   = Column(DateTime, nullable=True)


class PositionModel(Base):
    __tablename__ = "positions"

    symbol        = Column(String, primary_key=True)
    quantity      = Column(Integer, nullable=False)
    average_price = Column(Float, nullable=False)
    current_price = Column(Float, nullable=False)
    unrealized_pnl= Column(Float, default=0.0)
    realized_pnl  = Column(Float, default=0.0)
    updated_at    = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TradeHistoryModel(Base):
    __tablename__ = "trade_history"

    id            = Column(String, primary_key=True)
    symbol        = Column(String, nullable=False)
    side          = Column(String, nullable=False)
    price         = Column(Float, nullable=False)
    quantity      = Column(Integer, nullable=False)
    strategy      = Column(String, nullable=True)
    executed_at   = Column(DateTime, default=datetime.utcnow)


class AccountModel(Base):
    """单行账户余额表"""
    __tablename__ = "account"

    id              = Column(Integer, primary_key=True, default=1)
    capital         = Column(Float, nullable=False)
    frozen_capital  = Column(Float, default=0.0)
    updated_at      = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ── 初始化 ───────────────────────────────────────────────────────

async def init_db(initial_capital: float = 100_000.0):
    """建表 + 初始化账户余额（仅首次）"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(AccountModel).where(AccountModel.id == 1))
        acct = result.scalar_one_or_none()
        if acct is None:
            session.add(AccountModel(id=1, capital=initial_capital))
            await session.commit()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
