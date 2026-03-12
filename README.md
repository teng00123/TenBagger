# TenBagger — Quantitative Trading Platform

[![CI Tests](https://github.com/teng00123/TenBagger/actions/workflows/ci-tests.yml/badge.svg)](https://github.com/teng00123/TenBagger/actions/workflows/ci-tests.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Vue](https://img.shields.io/badge/Vue-3.x-42b883.svg)](https://vuejs.org/)

🌐 **Language**: [简体中文](README_CN.md) | [English](README.md)
📋 **Changelog**: [Version History](CHANGELOG.md)
🤝 **Contributing**: [Contributing Guide](CONTRIBUTING.md)

A decoupled quantitative trading platform built with **FastAPI + Vue 3**, providing a modern, modular solution for financial trading systems. The backend handles strategy calculations, data processing and trade execution, while the frontend delivers an intuitive interactive interface with strategy analysis, backtesting, and trade management.

> ⚠️ **For learning and research purposes only. Do not use for real trading.**

## Features

- ✅ **Backend**: Python + FastAPI, RESTful API
- ✅ **Frontend**: Vue 3 + Element Plus, modern UI
- ✅ **Trading Strategies**:
  - Moving Average Crossover Strategy (MA)
  - RSI Relative Strength Index Strategy
- ✅ **Real-time Analysis**: Market signal detection and trading recommendations
- ✅ **Backtesting System**: Historical performance backtesting
- ✅ **Trade Management**: Order execution, position management, trade history
- ✅ **Docker Support**: One-command startup with docker-compose

## Project Structure

```
TenBagger/
├── backend/              # Backend code
│   ├── main.py           # FastAPI entry point
│   ├── config.py         # Configuration
│   ├── requirements.txt  # Python dependencies (pip)
│   ├── pyproject.toml    # Python dependencies (poetry)
│   ├── Dockerfile        # Backend container
│   ├── strategies/       # Trading strategies
│   │   ├── ma_strategy.py
│   │   └── rsi_strategy.py
│   ├── models/           # Pydantic data models
│   ├── routers/          # API routes
│   └── utils/            # Utility functions
│
├── frontend/             # Frontend code (Vue 3)
│   ├── src/
│   │   ├── App.vue
│   │   ├── api/
│   │   └── components/
│   │       ├── Dashboard.vue
│   │       ├── StrategyPanel.vue
│   │       └── TradeHistory.vue
│   ├── Dockerfile        # Frontend container (nginx)
│   └── vite.config.js
│
├── docker-compose.yml    # One-command full-stack startup
├── .env.example          # Environment variable template
├── CHANGELOG.md
└── CONTRIBUTING.md
```

## Quick Start

### Option 1: Docker (Recommended)

```bash
git clone https://github.com/teng00123/TenBagger.git
cd TenBagger

cp .env.example .env
docker-compose up --build
```

- Frontend: http://localhost:80
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Option 2: Manual Setup

**Backend**

```bash
cd backend

# Create virtual environment (optional)
python -m venv venv
source venv/bin/activate   # macOS/Linux
# venv\Scripts\activate    # Windows

# Install dependencies
pip install -r requirements.txt
# Or with poetry: poetry install

# Configure environment
cp ../.env.example ../.env  # edit as needed

# Start service
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Backend: http://localhost:8000 | API Docs: http://localhost:8000/docs

**Frontend**

```bash
cd frontend
npm install
npm run dev
```

Frontend: http://localhost:5173

## API Reference

### Trading

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/trading/account` | Get account info |
| POST | `/api/trading/order` | Place order |
| GET | `/api/trading/orders` | List orders |
| GET | `/api/trading/history` | Trade history |
| POST | `/api/trading/positions/update` | Update position prices |

### Strategies

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/strategies/list` | List strategies |
| POST | `/api/strategies/analyze` | Analyze market signals |
| GET | `/api/strategies/status/{type}/{symbol}` | Strategy status |
| POST | `/api/strategies/backtest` | Run backtest |
| GET | `/api/strategies/symbols` | Supported symbols |

## Trading Strategies

### Moving Average Crossover (MA)

- Short MA crosses above long MA → **Golden Cross** → Buy
- Short MA crosses below long MA → **Death Cross** → Sell
- Default: `short_window=5`, `long_window=20`

### RSI Strategy

- RSI < 30 (Oversold) → **Buy signal**
- RSI > 70 (Overbought) → **Sell signal**
- Default: `rsi_period=14`, `rsi_oversold=30`, `rsi_overbought=70`

## Configuration

Copy `.env.example` to `.env` and customize:

```env
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True
INITIAL_CAPITAL=100000
COMMISSION_RATE=0.0003   # 0.03%
DATA_SOURCE=mock          # mock | real
ALLOWED_ORIGINS=http://localhost:5173
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11, FastAPI, Pydantic, NumPy, Pandas |
| Frontend | Vue 3, Vite, Element Plus, Axios, Pinia |
| DevOps | Docker, GitHub Actions |

## Extending the Platform

**Add a new strategy**: Create a file in `backend/strategies/`, implement `analyze()` and `get_current_status()`, then register in `backend/routers/strategies.py`.

**Integrate real data**: Update `backend/utils/data_fetcher.py` — supports Yahoo Finance, JoinQuant, Tushare, etc.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for dev setup, commit conventions, and PR guidelines.

## License

[MIT License](https://opensource.org/licenses/MIT) © teng
