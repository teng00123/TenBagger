# data/fetcher.py
import akshare as ak
from datetime import datetime
from TenBagger.utils.db import get_db_session
from TenBagger.data.models import ETFPrice


class DataFetcher:
    def __init__(self):
        self.session = get_db_session()

    def fetch_and_save(self, code: str, name: str):
        """获取并保存数据到数据库"""
        print(f"正在获取 {name} ({code}) 的数据...")

        # 使用 akshare 获取数据
        try:
            df = ak.fund_etf_hist_sina(symbol=code)
            # 数据清洗与入库逻辑
            count = 0
            for index, row in df.iterrows():
                # 检查是否已存在 (简单防重)
                exists = self.session.query(ETFPrice).filter_by(
                    code=code,
                    date=row['date']
                ).first()
                if not exists:
                    # 根据 row['date'] 的类型进行处理
                    date_value = row['date']
                    if isinstance(date_value, str):
                        # 如果是字符串，需要解析
                        date_obj = datetime.strptime(date_value, '%Y-%m-%d')
                    elif hasattr(date_value, 'strftime'):
                        # 如果是 datetime 或 date 对象，直接使用
                        # 如果是 datetime.date 对象，转换为 datetime 对象
                        if not isinstance(date_value, datetime):
                            date_obj = datetime.combine(date_value, datetime.min.time())
                        else:
                            date_obj = date_value
                    else:
                        # 其他类型，尝试字符串转换
                        date_obj = datetime.strptime(str(date_value), '%Y-%m-%d')

                    record = ETFPrice(
                        code=code,
                        date=date_obj,
                        open=row['open'],
                        close=row['close'],
                        high=row['high'],
                        low=row['low'],
                        volume=row['volume']
                    )
                    self.session.add(record)
                    count += 1

            self.session.commit()
            print(f"成功保存 {count} 条新数据")

        except Exception as e:
            print(f"获取数据失败: {e}")
            self.session.rollback()
