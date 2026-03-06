import json
import os


def get_stock_code():
    """
    获取股票代码列表

    Returns:
        list: 股票代码列表
    """
    # 获取项目根目录
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    stock_pool_path = os.path.join(project_root, 'data', 'stock_pool.json')

    # 检查文件是否存在
    if not os.path.exists(stock_pool_path):
        raise FileNotFoundError(f"股票池文件不存在: {stock_pool_path}")

    # 加载股票池
    with open(stock_pool_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    stock_code_list = []
    # 批量抓取并存储
    for stock in data['stock_pool']:
        code = stock['code']
        stock_code_list.append(code)

    return stock_code_list


def get_stock_info():
    """
    获取完整的股票信息

    Returns:
        list: 包含完整股票信息的字典列表
    """
    # 获取项目根目录
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    stock_pool_path = os.path.join(project_root, 'data', 'stock_pool.json')

    # 检查文件是否存在
    if not os.path.exists(stock_pool_path):
        raise FileNotFoundError(f"股票池文件不存在: {stock_pool_path}")

    # 加载股票池
    with open(stock_pool_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    return data['stock_pool']


def get_stock_by_code(stock_code: str):
    """
    根据股票代码获取股票信息

    Args:
        stock_code (str): 股票代码

    Returns:
        dict: 股票信息，如果不存在返回None
    """
    stocks = get_stock_info()
    for stock in stocks:
        if stock['code'] == stock_code:
            return stock
    return None


if __name__ == "__main__":
    # 测试函数
    try:
        codes = get_stock_code()
        print("股票代码列表:", codes)

        stocks = get_stock_info()
        print("股票详细信息:")
        for stock in stocks:
            print(f"  {stock['code']} - {stock['name']} ({stock['market']})")

    except FileNotFoundError as e:
        print(f"错误: {e}")
    except Exception as e:
        print(f"其他错误: {e}")