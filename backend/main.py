from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from config import Config
from routers import trading, strategies

# 创建 FastAPI 应用
app = FastAPI(
    title="量化交易平台",
    description="基于 FastAPI 的量化交易后端系统，支持多种交易策略",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(trading.router)
app.include_router(strategies.router)


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "欢迎使用量化交易平台 API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "config": Config.get_config()
    }


@app.get("/api/config")
async def get_config():
    """获取系统配置"""
    return Config.get_config()


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=Config.API_HOST,
        port=Config.API_PORT,
        reload=Config.DEBUG
    )
