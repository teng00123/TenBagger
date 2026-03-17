import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from config import Config
from routers import trading, strategies
from db.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """启动时初始化数据库（建表 + 初始化账户余额）"""
    await init_db(initial_capital=Config.INITIAL_CAPITAL)
    yield


# 创建 FastAPI 应用
app = FastAPI(
    title="量化交易平台",
    description="基于 FastAPI 的量化交易后端系统，支持多种交易策略",
    version="0.2.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# 配置 CORS
_raw_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000")
ALLOWED_ORIGINS = [o.strip() for o in _raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(trading.router)
app.include_router(strategies.router)


@app.get("/")
async def root():
    return {
        "message": "欢迎使用量化交易平台 API",
        "version": "0.2.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "config": Config.get_config()}


@app.get("/api/config")
async def get_config():
    return Config.get_config()


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=Config.API_HOST,
        port=Config.API_PORT,
        reload=Config.DEBUG,
    )
