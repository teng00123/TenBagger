# 量化交易平台

🌐 **语言**: [中文](README_CN.md) | [English](README.md)

一个基于 FastAPI + Vue 3 的前后端分离量化交易平台。

## 功能特性

- ✅ **后端**: Python + FastAPI，提供 RESTful API
- ✅ **前端**: Vue 3 + Element Plus，现代化 UI 界面
- ✅ **交易策略**: 
  - 均线交叉策略 (MA)
  - RSI 相对强弱指标策略
- ✅ **实时分析**: 市场信号检测与交易建议
- ✅ **回测系统**: 策略历史表现回测
- ✅ **交易管理**: 订单执行、持仓管理、交易历史

## 项目结构

```
quant-trading-platform/
├── backend/              # 后端代码
│   ├── main.py          # FastAPI 入口
│   ├── config.py        # 配置文件
│   ├── requirements.txt # Python 依赖
│   ├── strategies/      # 交易策略
│   │   ├── ma_strategy.py    # 均线策略
│   │   └── rsi_strategy.py   # RSI 策略
│   ├── models/          # 数据模型
│   │   └── schemas.py   # Pydantic 模型
│   ├── routers/         # API 路由
│   │   ├── trading.py   # 交易相关 API
│   │   └── strategies.py # 策略相关 API
│   └── utils/           # 工具函数
│       └── data_fetcher.py # 数据获取
│
├── frontend/            # 前端代码
│   ├── src/
│   │   ├── App.vue     # 主应用
│   │   ├── main.js     # 入口文件
│   │   ├── api/        # API 调用
│   │   │   └── index.js
│   │   └── components/ # Vue 组件
│   │       ├── Dashboard.vue      # 仪表盘
│   │       ├── StrategyPanel.vue  # 策略面板
│   │       └── TradeHistory.vue   # 交易历史
│   ├── package.json
│   └── vite.config.js
│
└── README.md
```

## 快速开始

### 后端启动

```bash
cd backend

# 创建虚拟环境 (可选)
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 启动服务
python main.py
# 或使用 uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

后端服务将在 http://localhost:8000 启动
API 文档：http://localhost:8000/docs

### 前端启动

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端服务将在 http://localhost:3000 启动

## API 接口

### 交易相关

- `GET /api/trading/account` - 获取账户信息
- `POST /api/trading/order` - 下单交易
- `GET /api/trading/orders` - 获取订单列表
- `GET /api/trading/history` - 获取交易历史
- `POST /api/trading/positions/update` - 更新持仓价格

### 策略相关

- `GET /api/strategies/list` - 获取策略列表
- `POST /api/strategies/analyze` - 分析市场信号
- `GET /api/strategies/status/{type}/{symbol}` - 获取策略状态
- `POST /api/strategies/backtest` - 运行回测
- `GET /api/strategies/symbols` - 获取支持的交易标的

## 交易策略

### 1. 均线交叉策略 (MA)

**原理**: 
- 短期均线上穿长期均线 → 金叉 → 买入信号
- 短期均线下穿长期均线 → 死叉 → 卖出信号

**参数**:
- `short_window`: 短期均线周期 (默认：5)
- `long_window`: 长期均线周期 (默认：20)

### 2. RSI 策略

**原理**:
- RSI < 30 (超卖区) → 买入信号
- RSI > 70 (超买区) → 卖出信号

**参数**:
- `rsi_period`: RSI 计算周期 (默认：14)
- `rsi_oversold`: 超卖线 (默认：30)
- `rsi_overbought`: 超买线 (默认：70)

## 配置说明

编辑 `backend/config.py` 或创建 `.env` 文件：

```env
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True
INITIAL_CAPITAL=100000
COMMISSION_RATE=0.0003
DATA_SOURCE=mock
```

## 技术栈

**后端**:
- Python 3.9+
- FastAPI
- Pydantic
- NumPy
- Pandas

**前端**:
- Vue 3
- Vite
- Element Plus
- Axios
- Pinia

## 注意事项

⚠️ **本系统仅用于学习和研究目的**

- 当前使用模拟数据进行回测和演示
- 实盘交易需要接入真实数据源和券商 API
- 投资有风险，交易需谨慎
- 请勿直接用于真实交易

## 扩展开发

### 添加新策略

1. 在 `backend/strategies/` 创建新策略文件
2. 实现 `analyze()` 和 `get_current_status()` 方法
3. 在 `backend/routers/strategies.py` 中注册

### 接入真实数据

修改 `backend/utils/data_fetcher.py`:
- 实现 `_fetch_real_data()` 方法
- 可接入 Yahoo Finance、聚宽、Tushare 等数据源

## License

MIT License

## 作者

teng
