"""
这个文件专注于数据获取功能
包含多种数据源的接口实现
"""

from datetime import datetime
import time
import pandas as pd



class KLineDataFetcher:
    """K线数据获取器"""

    @staticmethod
    def fetch_from_akshare(stock_code, interval='1d', start_date='20200101', end_date=None):
        """
        使用 akshare 获取K线数据
        :param stock_code: 股票代码（如 000001）
        :param interval: K线周期（1d, 1w, 1M）
        :param start_date: 开始日期（格式：20200101）
        :param end_date: 结束日期
        """
        try:
            import akshare as ak
        except ImportError:
            raise ImportError("请先安装 akshare: pip install akshare")

        end_date = end_date or datetime.now().strftime('%Y%m%d')

        # 日线
        if interval == '1d':
            df = ak.stock_zh_a_hist(
                symbol=stock_code,
                period="daily",
                start_date=start_date,
                end_date=end_date,
                adjust=""  # 不复权
            )
            df = df.rename(columns={
                '日期': 'date',
                '开盘': 'open',
                '收盘': 'close',
                '最高': 'high',
                '最低': 'low',
                '成交量': 'volume',
                '成交额': 'amount',
                '换手率': 'turnover_rate'
            })

        # 周线
        elif interval == '1w':
            df = ak.stock_zh_a_hist(
                symbol=stock_code,
                period="weekly",
                start_date=start_date,
                end_date=end_date,
                adjust=""
            )
            df = df.rename(columns={
                '日期': 'date',
                '开盘': 'open',
                '收盘': 'close',
                '最高': 'high',
                '最低': 'low',
                '成交量': 'volume',
                '成交额': 'amount'
            })

        # 月线
        elif interval == '1M':
            df = ak.stock_zh_a_hist(
                symbol=stock_code,
                period="monthly",
                start_date=start_date,
                end_date=end_date,
                adjust=""
            )
            df = df.rename(columns={
                '日期': 'date',
                '开盘': 'open',
                '收盘': 'close',
                '最高': 'high',
                '最低': 'low',
                '成交量': 'volume',
                '成交额': 'amount'
            })

        else:
            raise ValueError(f"不支持的K线周期: {interval}")

        df['date'] = pd.to_datetime(df['date'])

        return df

    @staticmethod
    def fetch_minute_data_from_akshare(stock_code, interval='5m'):
        """
        获取分钟K线数据（仅最近几天）
        :param stock_code: 股票代码
        :param interval: 1m, 5m, 15m, 30m, 60m
        """
        try:
            import akshare as ak
        except ImportError:
            raise ImportError("请先安装 akshare: pip install akshare")

        # akshare 分钟线参数
        period_map = {
            '1m': '1',
            '5m': '5',
            '15m': '15',
            '30m': '30',
            '60m': '60'
        }

        if interval not in period_map:
            raise ValueError(f"不支持的分钟周期: {interval}")

        df = ak.stock_zh_a_hist_min_em(
            symbol=stock_code,
            period=period_map[interval],
            adjust=""  # 不复权
        )

        df = df.rename(columns={
            '时间': 'date',
            '开盘': 'open',
            '收盘': 'close',
            '最高': 'high',
            '最低': 'low',
            '成交量': 'volume',
            '成交额': 'amount'
        })

        df['date'] = pd.to_datetime(df['date'])

        return df

    @staticmethod
    def fetch_from_tushare(stock_code, token, interval='1d', start_date='20200101', end_date=None):
        """
        使用 tushare 获取K线数据
        :param stock_code: 股票代码
        :param token: tushare token
        :param interval: K线周期
        :param start_date: 开始日期
        :param end_date: 结束日期
        """
        try:
            import tushare as ts
        except ImportError:
            raise ImportError("请先安装 tushare: pip install tushare")

        ts.set_token(token)
        pro = ts.pro_api()

        end_date = end_date or datetime.now().strftime('%Y%m%d')

        # 判断市场
        ts_code = f"{stock_code}.SZ" if stock_code.startswith('0') else f"{stock_code}.SH"

        # 日线
        if interval == '1d':
            df = pro.daily(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date
            )

        # 周线
        elif interval == '1w':
            df = pro.weekly(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date
            )

        # 月线
        elif interval == '1M':
            df = pro.monthly(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date
            )

        else:
            raise ValueError(f"不支持的K线周期: {interval}")

        df = df.rename(columns={
            'trade_date': 'date',
            'vol': 'volume'
        })

        df['date'] = pd.to_datetime(df['date'])

        return df

    @staticmethod
    def batch_fetch_stocks(stock_list, interval='1d', start_date='20200101',
                           end_date=None, delay=1):
        """
        批量获取多只股票数据
        :param stock_list: 股票代码列表
        :param interval: K线周期
        :param start_date: 开始日期
        :param end_date: 结束日期
        :param delay: 每次请求间隔（秒），避免被封
        :return: 字典 {stock_code: DataFrame}
        """
        results = {}

        for i, code in enumerate(stock_list):
            try:
                print(f"正在获取 {code} 数据 ({i + 1}/{len(stock_list)})...")
                df = KLineDataFetcher.fetch_from_akshare(
                    code, interval, start_date, end_date
                )

                if not df.empty:
                    results[code] = df
                    print(f"✓ {code}: {len(df)} 条数据")
                else:
                    print(f"⚠ {code}: 无数据")

                # 延迟，避免请求过快
                if i < len(stock_list) - 1:
                    time.sleep(delay)

            except Exception as e:
                print(f"✗ {code}: 获取失败 - {e}")
                continue

        print(f"\n完成！成功获取 {len(results)}/{len(stock_list)} 只股票数据")
        return results

