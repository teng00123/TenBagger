"""
tests/conftest.py — 公共 fixtures
"""
import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from httpx import AsyncClient, ASGITransport

# 将 backend/ 加入 sys.path，确保各模块可导入
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from main import app
from models.schemas import Candlestick


# ── 通用 fixtures ──────────────────────────────────────────────────

@pytest.fixture
def sample_candlesticks():
    """生成一组确定性的 K 线数据（价格平稳上涨，便于断言）"""
    base = 100.0
    data = []
    for i in range(30):
        price = base + i * 0.5          # 每天涨 0.5，形成上升趋势
        data.append(Candlestick(
            timestamp=datetime.now() - timedelta(days=30 - i),
            open=price,
            high=price + 0.3,
            low=price - 0.3,
            close=price,
            volume=100000,
        ))
    return data


@pytest.fixture
def golden_cross_candlesticks():
    """精确构造金叉信号：保证倒数第2根 short_ma <= long_ma，最后一根 short_ma > long_ma"""
    data = []
    # 第1段：30根，价格从100持续跌到55（long_ma被拉低，short_ma也低）
    for i in range(30):
        price = 100.0 - i * 1.5      # 100 → 56.5
        data.append(Candlestick(
            timestamp=datetime.now() - timedelta(days=60 - i),
            open=price, high=price + 0.1, low=price - 0.1,
            close=price, volume=100000,
        ))
    # 第2段：4根平盘（作为"前一状态"，此时 short_ma ≈ long_ma 或 short < long）
    for i in range(4):
        price = 57.0
        data.append(Candlestick(
            timestamp=datetime.now() - timedelta(days=30 - i),
            open=price, high=price + 0.1, low=price - 0.1,
            close=price, volume=100000,
        ))
    # 最后1根：价格急拉到120，触发 short_ma 上穿 long_ma
    data.append(Candlestick(
        timestamp=datetime.now() - timedelta(days=26),
        open=120.0, high=121.0, low=119.0,
        close=120.0, volume=100000,
    ))
    return data


@pytest.fixture
def oversold_candlesticks():
    """构造 RSI 极度超卖场景（连续暴跌）"""
    data = []
    price = 100.0
    for i in range(25):
        price = price * 0.97            # 每天跌 3%
        data.append(Candlestick(
            timestamp=datetime.now() - timedelta(days=25 - i),
            open=price + 0.5, high=price + 1, low=price - 0.5,
            close=price, volume=100000,
        ))
    return data


@pytest_asyncio.fixture
async def async_client():
    """提供可复用的 HTTPX 异步测试客户端"""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        yield client
