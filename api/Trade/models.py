from sqlalchemy import Column, Integer, String, Float, DateTime, Enum
from sqlalchemy.orm import Session
from data.base_model import Base
from datetime import datetime
import enum

class TradeSide(str, enum.Enum):
    """交易方向枚举"""
    BUY = "buy"
    SELL = "sell"


class TradeRecord(Base):
    """交易记录表"""
    __tablename__ = "trade_records"

    strategy_name = Column(String(50), index=True, comment="策略名称")
    symbol = Column(String(20), index=True, comment="股票/期货代码")
    side = Column(Enum(TradeSide), comment="买卖方向")
    price = Column(Float, comment="成交价格")
    quantity = Column(Integer, comment="成交数量")
    amount = Column(Float, comment="成交金额")
    timestamp = Column(DateTime, index=True, comment="交易时间")
    profit = Column(Float, nullable=True, comment="盈亏金额(卖出时)")
    commission = Column(Float, default=0.0, comment="手续费")
    notes = Column(String(200), nullable=True, comment="备注")

    @classmethod
    def create(cls, db: Session, strategy_name: str, symbol: str, side: TradeSide,
               price: float, quantity: int, commission: float = 0.0,
               profit: float = None, notes: str = None) -> 'TradeRecord':
        """
        创建交易记录

        Args:
            db: 数据库会话
            strategy_name: 策略名称
            symbol: 股票/期货代码
            side: 买卖方向
            price: 成交价格
            quantity: 成交数量
            commission: 手续费，默认0.0
            profit: 盈亏金额，卖出时使用
            notes: 备注信息

        Returns:
            TradeRecord: 创建的交易记录对象
        """
        # 计算成交金额
        amount = price * quantity

        # 创建交易记录对象
        trade_record = cls(
            strategy_name=strategy_name,
            symbol=symbol,
            side=side,
            price=price,
            quantity=quantity,
            amount=amount,
            timestamp=datetime.now(),
            profit=profit,
            commission=commission,
            notes=notes
        )

        # 添加到数据库
        db.add(trade_record)
        db.commit()
        db.refresh(trade_record)

        return trade_record

    @classmethod
    def create_buy_record(cls, db: Session, strategy_name: str, symbol: str,
                          price: float, quantity: int, commission: float = 0.0,
                          notes: str = None) -> 'TradeRecord':
        """
        创建买入交易记录（简化方法）

        Args:
            db: 数据库会话
            strategy_name: 策略名称
            symbol: 股票/期货代码
            price: 成交价格
            quantity: 成交数量
            commission: 手续费，默认0.0
            notes: 备注信息

        Returns:
            TradeRecord: 创建的买入交易记录对象
        """
        return cls.create(db, strategy_name, symbol, TradeSide.BUY, price, quantity,
                          commission, None, notes)

    @classmethod
    def create_sell_record(cls, db: Session, strategy_name: str, symbol: str,
                           price: float, quantity: int, profit: float = None,
                           commission: float = 0.0, notes: str = None) -> 'TradeRecord':
        """
        创建卖出交易记录（简化方法）

        Args:
            db: 数据库会话
            strategy_name: 策略名称
            symbol: 股票/期货代码
            price: 成交价格
            quantity: 成交数量
            profit: 盈亏金额
            commission: 手续费，默认0.0
            notes: 备注信息

        Returns:
            TradeRecord: 创建的卖出交易记录对象
        """
        return cls.create(db, strategy_name, symbol, TradeSide.SELL, price, quantity,
                          commission, profit, notes)

if __name__ == '__main__':
    from utils.db import get_db_session
    session = get_db_session()
    # 创建买入记录
    buy_record = TradeRecord.create_buy_record(
        db=session,
        strategy_name="双均线策略",
        symbol="000001",
        price=10.5,
        quantity=100,
        commission=3.15,
        notes="策略自动买入"
    )

    # 创建卖出记录
    sell_record = TradeRecord.create_sell_record(
        db=session,
        strategy_name="双均线策略",
        symbol="000001",
        price=12.0,
        quantity=100,
        profit=150.0,
        commission=3.6,
        notes="策略自动卖出，盈利150元"
    )