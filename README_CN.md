# TenBagger — 量化交易平台

[![CI Tests](https://github.com/teng00123/TenBagger/actions/workflows/ci-tests.yml/badge.svg)](https://github.com/teng00123/TenBagger/actions/workflows/ci-tests.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Vue](https://img.shields.io/badge/Vue-3.x-42b883.svg)](https://vuejs.org/)

🌐 **语言**: [简体中文](README_CN.md) | [English](README.md)
📋 **版本日志**: [版本历史](CHANGELOG.md)
🤝 **贡献指南**: [Contributing Guide](CONTRIBUTING.md)

基于 **FastAPI + Vue 3** 的前后端分离量化交易平台，提供现代化、模块化的金融交易系统解决方案。后端负责策略计算、数据处理与交易执行，前端提供直观的交互界面，实现策略分析、回测与交易管理。

> ⚠️ **本系统仅用于学习和研究目的，请勿用于真实交易。**

## 功能特性

- ✅ **后端**: Python + FastAPI，提供 RESTful API
- ✅ **前端**: Vue 3 + Element Plus，现代化 UI 界面
- ✅ **交易策略**:
  - 均线交叉策略 (MA)
  - RSI 相对强弱指标策略
- ✅ **实时分析**: 市场信号检测与交易建议
- ✅ **回测系统**: 策略历史表现回测
- ✅ **交易管理**: 订单执行、持仓管理、交易历史
- ✅ **Docker 支持**: docker-compose 一键启动

## 项目结构

```
TenBagger/
├── backend/              # 后端代码
│   ├── main.py           # FastAPI 入口
│   ├── config.py         # 配置文件
│   ├── requirements.txt  # Python 依赖（pip）
│   ├── pyproject.toml    # Python 依赖（poetry）
│   ├── Dockerfile        # 后端容器配置
│   ├── strategies/       # 交易策略
│   │   ├── ma_strategy.py
│   │   └── rsi_strategy.py
│   ├── models/           # Pydantic 数据模型
│   ├── routers/          # API 路由
│   └── utils/            # 工具函数
│
├── frontend/             # 前端代码（Vue 3）
│   ├── src/
│   │   ├── App.vue
│   │   ├── api/
│   │   └── components/
│   │       ├── Dashboard.vue      # 仪表盘
│   │       ├── StrategyPanel.vue  # 策略面板
│   │       └── TradeHistory.vue   # 交易历史
│   ├── Dockerfile        # 前端容器配置（nginx）
│   └── vite.config.js
│
├── docker-compose.yml    # 全栈一键启动
├── .env.example          # 环境变量模板
├── CHANGELOG.md
└── CONTRIBUTING.md
```

## 快速开始

### 方式一：Docker（推荐）

```bash
git clone https://github.com/teng00123/TenBagger.git
cd TenBagger

cp .env.example .env
docker-compose up --build
```

- 前端：http://localhost:80
- 后端 API：http://localhost:8000
- API 文档：http://localhost:8000/docs

### 方式二：手动启动

**后端**

```bash
cd backend

# 创建虚拟环境（可选）
python -m venv venv
source venv/bin/activate   # macOS/Linux
# venv\Scripts\activate    # Windows

# 安装依赖
pip install -r requirements.txt
# 或使用 poetry: poetry install

# 配置环境变量
cp ../.env.example ../.env  # 按需修改

# 启动服务
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

后端：http://localhost:8000 | API 文档：http://localhost:8000/docs

**前端**

```bash
cd frontend
npm install
npm run dev
```

前端：http://localhost:5173

## API 接口

### 交易相关

| 方法 | 接口 | 说明 |
|------|------|------|
| GET | `/api/trading/account` | 获取账户信息 |
| POST | `/api/trading/order` | 下单交易 |
| GET | `/api/trading/orders` | 获取订单列表 |
| GET | `/api/trading/history` | 获取交易历史 |
| POST | `/api/trading/positions/update` | 更新持仓价格 |

### 策略相关

| 方法 | 接口 | 说明 |
|------|------|------|
| GET | `/api/strategies/list` | 获取策略列表 |
| POST | `/api/strategies/analyze` | 分析市场信号 |
| GET | `/api/strategies/status/{type}/{symbol}` | 获取策略状态 |
| POST | `/api/strategies/backtest` | 运行回测 |
| GET | `/api/strategies/symbols` | 获取支持的交易标的 |

## 交易策略

### 均线交叉策略 (MA)

- 短期均线上穿长期均线 → **金叉** → 买入信号
- 短期均线下穿长期均线 → **死叉** → 卖出信号
- 默认参数：`short_window=5`，`long_window=20`

### RSI 策略

- RSI < 30（超卖区）→ **买入信号**
- RSI > 70（超买区）→ **卖出信号**
- 默认参数：`rsi_period=14`，`rsi_oversold=30`，`rsi_overbought=70`

## 配置说明

复制 `.env.example` 为 `.env` 并按需修改：

```env
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True
INITIAL_CAPITAL=100000
COMMISSION_RATE=0.0003     # 手续费率（万分之三）
DATA_SOURCE=mock            # mock（模拟数据）| real（真实数据）
ALLOWED_ORIGINS=http://localhost:5173
```

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python 3.11、FastAPI、Pydantic、NumPy、Pandas |
| 前端 | Vue 3、Vite、Element Plus、Axios、Pinia |
| 运维 | Docker、GitHub Actions |

## 扩展开发

**添加新策略**：在 `backend/strategies/` 创建策略文件，实现 `analyze()` 和 `get_current_status()` 方法，然后在 `backend/routers/strategies.py` 中注册。

**接入真实数据**：修改 `backend/utils/data_fetcher.py`，可接入 Yahoo Finance、聚宽、Tushare 等数据源。

## 贡献

请参阅 [CONTRIBUTING.md](CONTRIBUTING.md) 了解开发环境配置、Commit 规范与 PR 流程。

## License

[MIT License](https://opensource.org/licenses/MIT) © teng
