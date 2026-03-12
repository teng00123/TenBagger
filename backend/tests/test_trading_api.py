"""
tests/test_trading_api.py — Trading Router API 测试
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from main import app
from routers.trading import trading_state


@pytest.fixture(autouse=True)
def reset_trading_state():
    """每个测试前重置全局交易状态，避免用例间污染"""
    from config import Config
    trading_state.capital = Config.INITIAL_CAPITAL
    trading_state.frozen_capital = 0
    trading_state.positions.clear()
    trading_state.orders.clear()
    trading_state.trade_history.clear()
    yield


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as c:
        yield c


class TestAccountAPI:

    @pytest.mark.asyncio
    async def test_get_account_returns_200(self, client):
        resp = await client.get("/api/trading/account")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_account_initial_capital(self, client):
        from config import Config
        resp = await client.get("/api/trading/account")
        data = resp.json()
        assert data["available_capital"] == Config.INITIAL_CAPITAL

    @pytest.mark.asyncio
    async def test_account_has_required_fields(self, client):
        resp = await client.get("/api/trading/account")
        data = resp.json()
        for field in ("total_capital", "available_capital", "frozen_capital", "positions", "total_pnl"):
            assert field in data


class TestOrderAPI:

    @pytest.mark.asyncio
    async def test_buy_order_success(self, client):
        resp = await client.post("/api/trading/order", json={
            "symbol": "600519.SS",
            "side": "buy",
            "price": 100.0,
            "quantity": 10,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "order_id" in data["data"]

    @pytest.mark.asyncio
    async def test_buy_creates_position(self, client):
        await client.post("/api/trading/order", json={
            "symbol": "000001.SZ",
            "side": "buy",
            "price": 10.0,
            "quantity": 100,
        })
        account = (await client.get("/api/trading/account")).json()
        symbols = [p["symbol"] for p in account["positions"]]
        assert "000001.SZ" in symbols

    @pytest.mark.asyncio
    async def test_buy_deducts_capital(self, client):
        from config import Config
        await client.post("/api/trading/order", json={
            "symbol": "600519.SS",
            "side": "buy",
            "price": 200.0,
            "quantity": 10,
        })
        account = (await client.get("/api/trading/account")).json()
        assert account["available_capital"] < Config.INITIAL_CAPITAL

    @pytest.mark.asyncio
    async def test_buy_insufficient_capital_returns_400(self, client):
        resp = await client.post("/api/trading/order", json={
            "symbol": "600519.SS",
            "side": "buy",
            "price": 999999.0,
            "quantity": 9999,
        })
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_sell_without_position_returns_400(self, client):
        resp = await client.post("/api/trading/order", json={
            "symbol": "NO_SUCH_STOCK",
            "side": "sell",
            "price": 100.0,
            "quantity": 10,
        })
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_sell_more_than_held_returns_400(self, client):
        # 先买 10 股
        await client.post("/api/trading/order", json={
            "symbol": "600519.SS",
            "side": "buy",
            "price": 100.0,
            "quantity": 10,
        })
        # 尝试卖 100 股
        resp = await client.post("/api/trading/order", json={
            "symbol": "600519.SS",
            "side": "sell",
            "price": 110.0,
            "quantity": 100,
        })
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_buy_then_sell_clears_position(self, client):
        await client.post("/api/trading/order", json={
            "symbol": "600519.SS",
            "side": "buy",
            "price": 100.0,
            "quantity": 10,
        })
        await client.post("/api/trading/order", json={
            "symbol": "600519.SS",
            "side": "sell",
            "price": 110.0,
            "quantity": 10,
        })
        account = (await client.get("/api/trading/account")).json()
        assert all(p["symbol"] != "600519.SS" for p in account["positions"])

    @pytest.mark.asyncio
    async def test_sell_at_profit_increases_capital(self, client):
        from config import Config
        await client.post("/api/trading/order", json={
            "symbol": "600519.SS",
            "side": "buy",
            "price": 100.0,
            "quantity": 10,
        })
        await client.post("/api/trading/order", json={
            "symbol": "600519.SS",
            "side": "sell",
            "price": 200.0,   # 卖出价高于买入价
            "quantity": 10,
        })
        account = (await client.get("/api/trading/account")).json()
        assert account["available_capital"] > Config.INITIAL_CAPITAL


class TestOrderHistoryAPI:

    @pytest.mark.asyncio
    async def test_get_orders_empty(self, client):
        resp = await client.get("/api/trading/orders")
        assert resp.status_code == 200
        assert resp.json() == []

    @pytest.mark.asyncio
    async def test_get_orders_after_trade(self, client):
        await client.post("/api/trading/order", json={
            "symbol": "600519.SS",
            "side": "buy",
            "price": 100.0,
            "quantity": 5,
        })
        resp = await client.get("/api/trading/orders")
        assert len(resp.json()) == 1

    @pytest.mark.asyncio
    async def test_get_trade_history(self, client):
        await client.post("/api/trading/order", json={
            "symbol": "600519.SS",
            "side": "buy",
            "price": 100.0,
            "quantity": 5,
        })
        resp = await client.get("/api/trading/history")
        assert resp.status_code == 200
        assert len(resp.json()) >= 1


class TestPositionUpdateAPI:

    @pytest.mark.asyncio
    async def test_update_position_prices(self, client):
        await client.post("/api/trading/order", json={
            "symbol": "600519.SS",
            "side": "buy",
            "price": 100.0,
            "quantity": 10,
        })
        resp = await client.post(
            "/api/trading/positions/update",
            json={"600519.SS": 120.0}
        )
        assert resp.status_code == 200
        account = (await client.get("/api/trading/account")).json()
        pos = next(p for p in account["positions"] if p["symbol"] == "600519.SS")
        assert pos["current_price"] == 120.0
        assert pos["unrealized_pnl"] == pytest.approx(200.0)  # (120-100)*10
