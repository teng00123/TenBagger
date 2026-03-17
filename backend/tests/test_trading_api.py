"""
tests/test_trading_api.py — Trading Router API 测试（SQLite 持久化版）
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from db.database import Base, get_db
from main import app


# ── 测试用内存数据库 fixture ──────────────────────────────────────

@pytest_asyncio.fixture(autouse=True)
async def reset_db():
    """每个测试用例使用独立的 in-memory SQLite，确保隔离"""
    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    TestSession = async_sessionmaker(test_engine, expire_on_commit=False)

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 初始化账户
    from db.database import AccountModel
    from config import Config
    async with TestSession() as s:
        s.add(AccountModel(id=1, capital=Config.INITIAL_CAPITAL, frozen_capital=0.0))
        await s.commit()

    async def override_get_db():
        async with TestSession() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()
    await test_engine.dispose()


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as c:
        yield c


# ── 测试类 ────────────────────────────────────────────────────────

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
        await client.post("/api/trading/order", json={
            "symbol": "600519.SS",
            "side": "buy",
            "price": 100.0,
            "quantity": 10,
        })
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
            "price": 200.0,
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
            json={"600519.SS": 120.0},
        )
        assert resp.status_code == 200
        account = (await client.get("/api/trading/account")).json()
        pos = next(p for p in account["positions"] if p["symbol"] == "600519.SS")
        assert pos["current_price"] == 120.0
        assert pos["unrealized_pnl"] == pytest.approx(200.0)  # (120-100)*10
