"""
tests/test_strategies_api.py — Strategies Router API 测试
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from main import app


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as c:
        yield c


class TestStrategyListAPI:

    @pytest.mark.asyncio
    async def test_list_returns_200(self, client):
        resp = await client.get("/api/strategies/list")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_list_contains_ma_and_rsi(self, client):
        resp = await client.get("/api/strategies/list")
        types = [s["type"] for s in resp.json()]
        assert "ma" in types
        assert "rsi" in types
        assert "macd" in types
        assert "bollinger" in types

    @pytest.mark.asyncio
    async def test_list_strategy_has_required_fields(self, client):
        resp = await client.get("/api/strategies/list")
        for s in resp.json():
            assert "type" in s
            assert "name" in s
            assert "description" in s
            assert "parameters" in s


class TestAnalyzeAPI:

    @pytest.mark.asyncio
    async def test_analyze_ma_returns_200(self, client):
        resp = await client.post("/api/strategies/analyze", json={
            "strategy_type": "ma",
            "symbol": "600519.SS",
        })
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_analyze_rsi_returns_200(self, client):
        resp = await client.post("/api/strategies/analyze", json={
            "strategy_type": "rsi",
            "symbol": "000001.SZ",
        })
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_analyze_response_has_has_signal(self, client):
        resp = await client.post("/api/strategies/analyze", json={
            "strategy_type": "ma",
            "symbol": "600519.SS",
        })
        data = resp.json()
        assert "has_signal" in data

    @pytest.mark.asyncio
    async def test_analyze_signal_structure_when_present(self, client):
        resp = await client.post("/api/strategies/analyze", json={
            "strategy_type": "rsi",
            "symbol": "BTC-USD",
        })
        data = resp.json()
        if data["has_signal"]:
            signal = data["signal"]
            for field in ("symbol", "side", "price", "quantity", "signal_strength", "strategy", "reason"):
                assert field in signal
            assert signal["side"] in ("buy", "sell")
            assert 0.0 <= signal["signal_strength"] <= 1.0


class TestStrategyStatusAPI:

    @pytest.mark.asyncio
    async def test_ma_status_returns_200(self, client):
        resp = await client.get("/api/strategies/status/ma/600519.SS")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_rsi_status_returns_200(self, client):
        resp = await client.get("/api/strategies/status/rsi/000001.SZ")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_status_response_structure(self, client):
        resp = await client.get("/api/strategies/status/ma/600519.SS")
        data = resp.json()
        assert data["success"] is True
        assert "data" in data


class TestBacktestAPI:

    @pytest.mark.asyncio
    async def test_backtest_ma_returns_200(self, client):
        resp = await client.post("/api/strategies/backtest", json={
            "strategy_type": "ma",
            "symbol": "600519.SS",
        })
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_backtest_rsi_returns_200(self, client):
        resp = await client.post("/api/strategies/backtest", json={
            "strategy_type": "rsi",
            "symbol": "000001.SZ",
        })
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_backtest_result_fields(self, client):
        resp = await client.post("/api/strategies/backtest", json={
            "strategy_type": "ma",
            "symbol": "600519.SS",
        })
        data = resp.json()
        for field in ("strategy_name", "symbol", "total_return", "annual_return",
                      "max_drawdown", "sharpe_ratio", "win_rate", "total_trades"):
            assert field in data

    @pytest.mark.asyncio
    async def test_backtest_metrics_in_valid_range(self, client):
        resp = await client.post("/api/strategies/backtest", json={
            "strategy_type": "ma",
            "symbol": "600519.SS",
        })
        data = resp.json()
        assert 0.0 <= data["max_drawdown"]      # 最大回撤 >= 0
        assert 0.0 <= data["win_rate"] <= 100.0  # 胜率 0-100%


class TestSymbolsAPI:

    @pytest.mark.asyncio
    async def test_symbols_returns_200(self, client):
        resp = await client.get("/api/strategies/symbols")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_symbols_contains_defaults(self, client):
        resp = await client.get("/api/strategies/symbols")
        data = resp.json()
        symbols = data["data"]["symbols"]
        assert "600519.SS" in symbols
        assert "000001.SZ" in symbols
        assert "BTC-USD" in symbols


class TestKlineAPI:

    @pytest.mark.asyncio
    async def test_kline_returns_200(self, client):
        resp = await client.get("/api/strategies/kline/600519.SS")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_kline_has_required_keys(self, client):
        resp = await client.get("/api/strategies/kline/600519.SS")
        data = resp.json()
        for key in ("symbol", "dates", "ohlcv", "ma5", "ma20", "latest"):
            assert key in data, f"缺少字段: {key}"

    @pytest.mark.asyncio
    async def test_kline_dates_and_ohlcv_same_length(self, client):
        resp = await client.get("/api/strategies/kline/600519.SS", params={"days": 30})
        data = resp.json()
        assert len(data["dates"]) == len(data["ohlcv"])
        assert len(data["dates"]) == len(data["ma5"])
        assert len(data["dates"]) == len(data["ma20"])

    @pytest.mark.asyncio
    async def test_kline_ohlcv_format(self, client):
        resp = await client.get("/api/strategies/kline/000001.SZ")
        data = resp.json()
        # 每条 OHLCV 应有 5 个元素
        for row in data["ohlcv"]:
            assert len(row) == 5

    @pytest.mark.asyncio
    async def test_kline_latest_fields(self, client):
        resp = await client.get("/api/strategies/kline/BTC-USD")
        data = resp.json()
        latest = data["latest"]
        for field in ("open", "high", "low", "close", "volume"):
            assert field in latest

    @pytest.mark.asyncio
    async def test_kline_ma_prefix_none_values(self, client):
        """MA5 前4个值应为 None（数据不足一个完整窗口）"""
        resp = await client.get("/api/strategies/kline/600519.SS", params={"days": 30})
        data = resp.json()
        assert data["ma5"][0] is None
        assert data["ma5"][3] is None
        assert data["ma5"][4] is not None
