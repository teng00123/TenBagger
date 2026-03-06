from data.data_manager import KLineDataManager
from data.data_fetcher import KLineDataFetcher
from datetime import datetime
import pandas as pd

class DataDownloader:
    """数据下载器类，负责股票数据的下载和管理"""

    def __init__(self):
        self.manager = KLineDataManager()
        self.default_stock_code = "600519"  # 默认股票代码：沪深300ETF

    def download_daily_data(self, stock_code=None, start_date="20230101"):
        """下载日线数据并存入数据库"""
        stock_code = stock_code or self.default_stock_code
        print(f"\n=== 获取 {stock_code} 日线数据 ===")

        df = KLineDataFetcher.fetch_from_akshare(
            stock_code,
            interval='1d',
            start_date=start_date,
            end_date=datetime.now().strftime('%Y%m%d')
        )

        print(f"获取到 {len(df)} 条数据")
        print(df.head())

        # 存入数据库（会自动计算技术指标和生成交易信号）
        self.manager.save_kline_data(df, stock_code, interval='1d')
        return df

    def download_weekly_data(self, stock_code=None, start_date="20220101"):
        """下载周线数据"""
        stock_code = stock_code or self.default_stock_code
        print(f"\n=== 获取 {stock_code} 周线数据 ===")

        df_weekly = KLineDataFetcher.fetch_from_akshare(
            stock_code,
            interval='1w',
            start_date=start_date
        )
        self.manager.save_kline_data(df_weekly, stock_code, interval='1w')
        return df_weekly

    def download_minute_data(self, stock_code=None, interval='5m'):
        """下载分钟数据"""
        stock_code = stock_code or self.default_stock_code
        print(f"\n=== 获取 {stock_code} {interval}分钟数据 ===")

        df_minute = KLineDataFetcher.fetch_minute_data_from_akshare(
            stock_code,
            interval=interval
        )
        print(f"获取到 {len(df_minute)} 条分钟数据")
        self.manager.save_kline_data(df_minute, stock_code, interval=interval)
        return df_minute

    def query_recent_data(self, stock_code=None, days=30, interval='1d'):
        """查询最近的数据"""
        stock_code = stock_code or self.default_stock_code
        print(f"\n=== 查询最近{days}天数据 ===")

        recent_data = self.manager.get_kline_data(
            stock_code,
            interval=interval,
            start_date=(datetime.now() - pd.Timedelta(days=days)).strftime('%Y-%m-%d')
        )
        print(f"查询到 {len(recent_data)} 条数据")
        print(recent_data[['date', 'open', 'close', 'ma5', 'ma10', 'signal']].tail())
        return recent_data

    def get_latest_price(self, stock_code=None):
        """获取最新价格信息"""
        stock_code = stock_code or self.default_stock_code
        latest = self.manager.get_latest_price(stock_code)
        print(f"\n最新价格信息: {latest}")
        return latest

    def batch_download_stocks(self, stock_list=None, interval='1d', start_date='20230101'):
        """批量下载多只股票数据"""
        if stock_list is None:
            stock_list = ['000001', '000002', '600000', '600036', '600519']

        print(f"\n=== 批量导入股票数据 ===")

        # 批量获取
        results = KLineDataFetcher.batch_fetch_stocks(
            stock_list,
            interval=interval,
            start_date=start_date
        )

        # 批量保存
        for code, df in results.items():
            self.manager.save_kline_data(df, code, interval=interval)

        return results

    def analyze_data(self, stock_code=None, start_date='2024-01-01', interval='1d'):
        """数据分析示例"""
        stock_code = stock_code or self.default_stock_code
        print(f"\n=== {stock_code} 数据分析示例 ===")

        # 查询某股票数据
        df = self.manager.get_kline_data(stock_code, interval=interval, start_date=start_date)

        # 统计信号分布
        print("\n交易信号统计:")
        print(df['signal'].value_counts())

        # 统计涨跌
        bullish = len(df[df['close'] > df['open']])
        bearish = len(df[df['close'] < df['open']])
        print(f"\n阳线: {bullish} 天, 阴线: {bearish} 天")

        # 平均涨幅
        avg_change = df['change_rate'].mean()
        print(f"平均涨幅: {avg_change:.2f}%")

        return df

    def run_demo(self):
        """运行完整的演示流程"""
        print("开始数据下载演示...")

        # 1. 下载日线数据
        self.download_daily_data()

        # 2. 下载周线数据
        self.download_weekly_data()

        # 3. 下载分钟数据
        self.download_minute_data()

        # 4. 查询数据
        self.query_recent_data()

        # 5. 获取最新价格
        self.get_latest_price()

        # 6. 批量下载
        self.batch_download_stocks()

        # 7. 数据分析
        self.analyze_data()

        print("\n========== 完成 ==========")


# 使用示例
if __name__ == "__main__":
    downloader = DataDownloader()
    downloader.run_demo()