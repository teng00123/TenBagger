import json
from data_fetcher import KLineDataFetcher
from data_manager import KLineDataManager

# 加载股票池
with open('stock_pool.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

manager = KLineDataManager()

# 批量抓取并存储
for stock in data['stock_pool']:
    code = stock['code']
    try:
        print(f"正在处理: {stock['name']} ({code})")
        df = KLineDataFetcher.fetch_from_akshare(code, start_date='20230101')
        manager.save_kline_data(df, code, interval='1d')
    except Exception as e:
        print(f"失败: {code}, 原因: {e}")
