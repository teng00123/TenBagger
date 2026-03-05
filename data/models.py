# data/models.py
from sqlalchemy import Column, String, Float, Date, BigInteger, DECIMAL, Index
from data.base_model import Base


class ETFPrice(Base):
    """ETF 每日价格表"""
    __tablename__ = "etf_prices"
    # 添加 extend_existing=True 避免重复定义错误
    __table_args__ = {'extend_existing': True}

    # 以下字段已从基类继承：id, created_at, updated_at

    # ETF价格特有字段
    code = Column(String(255), index=True, comment="ETF代码")
    date = Column(Date, index=True, comment="交易日期")
    open = Column(Float, comment="开盘价")
    close = Column(Float, comment="收盘价")
    high = Column(Float, comment="最高价")
    low = Column(Float, comment="最低价")
    volume = Column(BigInteger, comment="成交量")

    # 可以添加ETF价格特有的方法
    def get_price_change(self):
        """计算价格变化（收盘价相对开盘价）"""
        if self.open and self.close:
            return (self.close - self.open) / self.open * 100
        return 0.0


class KLine(Base):
    """K线图表结构

    支持不同周期的K线数据，包括：
    - 1分钟 (1m)
    - 5分钟 (5m)
    - 15分钟 (15m)
    - 30分钟 (30m)
    - 60分钟 (60m)
    - 日线 (1d)
    - 周线 (1w)
    - 月线 (1M)
    """
    __tablename__ = "k_lines"
    __table_args__ = (
        # 复合索引，提高按代码和日期查询的性能
        Index('idx_code_date', 'code', 'date'),
        Index('idx_code_interval', 'code', 'interval'),
        {'extend_existing': True}
    )

    # 以下字段已从基类继承：id, created_at, updated_at

    # K线基础字段
    code = Column(String(50), nullable=False, comment="标的代码")
    interval = Column(String(10), nullable=False, comment="K线周期", default="1d")
    date = Column(Date, nullable=False, comment="K线日期/时间")
    open = Column(DECIMAL(20, 8), comment="开盘价")
    close = Column(DECIMAL(20, 8), comment="收盘价")
    high = Column(DECIMAL(20, 8), comment="最高价")
    low = Column(DECIMAL(20, 8), comment="最低价")
    volume = Column(BigInteger, comment="成交量")
    amount = Column(DECIMAL(20, 4), comment="成交金额")

    # 扩展字段
    change = Column(DECIMAL(10, 4), comment="涨跌额")
    change_rate = Column(DECIMAL(10, 6), comment="涨跌幅（%）")
    turnover_rate = Column(DECIMAL(10, 6), comment="换手率（%）")
    amplitude = Column(DECIMAL(10, 6), comment="振幅（%）")

    # 市场指标
    market_value = Column(DECIMAL(20, 4), comment="市值")
    pe_ratio = Column(DECIMAL(10, 4), comment="市盈率")
    pb_ratio = Column(DECIMAL(10, 4), comment="市净率")

    # 技术指标（可存储预计算指标）
    ma5 = Column(DECIMAL(20, 8), comment="5日均价")
    ma10 = Column(DECIMAL(20, 8), comment="10日均价")
    ma20 = Column(DECIMAL(20, 8), comment="20日均价")
    ma60 = Column(DECIMAL(20, 8), comment="60日均价")

    # 交易信号标记
    signal = Column(String(20), comment="交易信号（BUY/SELL/HOLD）")
    signal_strength = Column(DECIMAL(5, 2), comment="信号强度")

    def get_kline_info(self):
        """获取K线基本信息"""
        return {
            "code": self.code,
            "interval": self.interval,
            "date": self.date.strftime("%Y-%m-%d") if self.date else None,
            "open": float(self.open) if self.open else None,
            "close": float(self.close) if self.close else None,
            "high": float(self.high) if self.high else None,
            "low": float(self.low) if self.low else None,
            "volume": int(self.volume) if self.volume else None,
            "change_rate": float(self.change_rate) if self.change_rate else None,
        }

    def is_bullish(self):
        """判断是否为阳线（收盘价高于开盘价）"""
        if self.open and self.close:
            return self.close > self.open
        return False

    def is_bearish(self):
        """判断是否为阴线（收盘价低于开盘价）"""
        if self.open and self.close:
            return self.close < self.open
        return False

    def get_amplitude_calculated(self):
        """计算振幅（如果没有预存储）"""
        if self.high and self.low and self.close:
            return ((float(self.high) - float(self.low)) / float(self.close)) * 100
        return 0.0