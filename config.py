# config.py
import os

# 数据库配置 (利用你熟悉的 SQLAlchemy)
DATABASE_URL = "mysql+pymysql://root:123456@localhost:3306/tenbagger"

# ETF 池配置
ETF_POOL = {
    "沪深300": "sh510300",
    "创业板": "sz159915",
    "纳指100": "sz159941",
}

# 策略参数
MOMENTUM_DAYS = 20  # 动量计算周期

# 风控参数
MAX_SINGLE_POSITION = 0.6  # 单个标的最大仓位
STOP_LOSS_RATIO = -0.10    # 止损线 (示例)

# API Keys (如果后续接入大模型分析)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
