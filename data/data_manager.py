"""
这个文件专注于数据管理和数据库操作
包含技术指标计算、信号生成等核心业务逻辑
"""

from data.models import KLine
from utils.db import get_db_session, init_db
import pandas as pd

class KLineDataManager:
    """K线数据管理器"""

    # K线周期映射
    INTERVAL_MAP = {
        '1m': '1分钟',
        '5m': '5分钟',
        '15m': '15分钟',
        '30m': '30分钟',
        '60m': '60分钟',
        '1d': '日线',
        '1w': '周线',
        '1M': '月线'
    }

    def __init__(self):
        """
        初始化数据库连接
        """
        init_db()
        self.session = get_db_session()


    def calculate_indicators(self, df):
        """
        计算技术指标
        :param df: DataFrame
        :return: DataFrame（带技术指标）
        """
        df = df.copy()

        # 计算涨跌额和涨跌幅
        if 'close' in df.columns and len(df) > 0:
            df['change'] = df['close'].diff()
            df['change_rate'] = df['close'].pct_change() * 100

        # 计算振幅
        if all(col in df.columns for col in ['high', 'low', 'close']):
            df['amplitude'] = ((df['high'] - df['low']) / df['close'].shift(1)) * 100

        # 计算均线
        if 'close' in df.columns:
            df['ma5'] = df['close'].rolling(window=5, min_periods=1).mean()
            df['ma10'] = df['close'].rolling(window=10, min_periods=1).mean()
            df['ma20'] = df['close'].rolling(window=20, min_periods=1).mean()
            df['ma60'] = df['close'].rolling(window=60, min_periods=1).mean()

        return df

    def generate_signal(self, row):
        """
        生成交易信号（简单策略示例）
        :param row: 数据行
        :return: (signal, strength)
        """
        signal = 'HOLD'
        strength = 0.0

        # 如果没有足够数据，返回 HOLD
        if pd.isna(row.get('ma5')) or pd.isna(row.get('ma10')):
            return signal, strength

        # 简单均线策略
        if row['close'] > row['ma5'] > row['ma10']:
            signal = 'BUY'
            strength = min((row['close'] - row['ma10']) / row['ma10'] * 100, 10.0)
        elif row['close'] < row['ma5'] < row['ma10']:
            signal = 'SELL'
            strength = min((row['ma10'] - row['close']) / row['ma10'] * 100, 10.0)

        return signal, round(strength, 2)

    def save_kline_data(self, df, code, interval='1d', batch_size=1000):
        """
        保存K线数据到数据库
        :param df: DataFrame（包含K线数据）
        :param code: 股票代码
        :param interval: K线周期
        :param batch_size: 批量插入大小
        """

        try:
            # 确保列名标准化
            df = self._normalize_columns(df)

            # 添加代码和周期
            df['code'] = code
            df['interval'] = interval

            # 计算技术指标
            df = self.calculate_indicators(df)

            # 转换为字典列表
            records = df.to_dict('records')

            # 批量保存
            for i in range(0, len(records), batch_size):
                batch = records[i:i + batch_size]

                for record in batch:
                    # 生成交易信号
                    signal, strength = self.generate_signal(record)
                    record['signal'] = signal
                    record['signal_strength'] = strength

                    # 处理 NaN 值
                    record = {k: (None if pd.isna(v) else v) for k, v in record.items()}

                    # 创建 KLine 对象
                    kline = KLine(**record)

                    # 使用 merge 避免重复
                    self.session.merge(kline)

                self.session.commit()
                print(f"已保存 {min(i + batch_size, len(records))}/{len(records)} 条数据")

            print(f"✓ 成功保存 {code} 的 {interval} K线数据 {len(records)} 条")

        except Exception as e:
            self.session.rollback()
            print(f"✗ 保存失败: {e}")
            raise e
        finally:
            self.session.close()

    def _normalize_columns(self, df):
        """标准化列名"""
        column_mapping = {
            '日期': 'date',
            '开盘': 'open',
            '收盘': 'close',
            '最高': 'high',
            '最低': 'low',
            '成交量': 'volume',
            '成交额': 'amount',
            '换手率': 'turnover_rate',
            '振幅': 'amplitude',
            '涨跌幅': 'change_rate',
            '涨跌额': 'change',
            '股票代码': 'code',
            'date': 'date',
            'open': 'open',
            'close': 'close',
            'high': 'high',
            'low': 'low',
            'vol': 'volume',
            'amount': 'amount',
            'turnover': 'turnover_rate'
        }

        df = df.rename(columns=column_mapping)

        # 确保日期格式正确
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])

        return df

    def get_kline_data(self, code, interval='1d', start_date=None, end_date=None):
        """
        查询K线数据
        :param code: 股票代码
        :param interval: K线周期
        :param start_date: 开始日期
        :param end_date: 结束日期
        :return: DataFrame
        """

        try:
            query = self.session.query(KLine).filter(
                KLine.code == code,
                KLine.interval == interval
            )

            if start_date:
                query = query.filter(KLine.date >= start_date)
            if end_date:
                query = query.filter(KLine.date <= end_date)

            query = query.order_by(KLine.date)
            results = query.all()

            # 转换为 DataFrame
            data = [{
                'date': r.date,
                'open': float(r.open) if r.open else None,
                'high': float(r.high) if r.high else None,
                'low': float(r.low) if r.low else None,
                'close': float(r.close) if r.close else None,
                'volume': int(r.volume) if r.volume else None,
                'amount': float(r.amount) if r.amount else None,
                'change': float(r.change) if r.change else None,
                'change_rate': float(r.change_rate) if r.change_rate else None,
                'turnover_rate': float(r.turnover_rate) if r.turnover_rate else None,
                'amplitude': float(r.amplitude) if r.amplitude else None,
                'ma5': float(r.ma5) if r.ma5 else None,
                'ma10': float(r.ma10) if r.ma10 else None,
                'ma20': float(r.ma20) if r.ma20 else None,
                'ma60': float(r.ma60) if r.ma60 else None,
                'signal': r.signal,
                'signal_strength': float(r.signal_strength) if r.signal_strength else None
            } for r in results]

            return pd.DataFrame(data)

        finally:
            self.session.close()

    def get_latest_price(self, code, interval='1d'):
        """获取最新价格"""
        try:
            result = self.session.query(KLine).filter(
                KLine.code == code,
                KLine.interval == interval
            ).order_by(KLine.date.desc()).first()

            return result.get_kline_info() if result else None
        finally:
            self.session.close()

