# Quantitative Trading Platform

🌐 **Language**: [中文](README_CN.md) | [English](README.md)

This project is a decoupled quantitative trading platform built with FastAPI + Vue 3, designed to provide a modern, modular solution for financial trading systems
csdn.net
. The system adopts a RESTful API architecture, where the backend handles strategy calculations, data processing, and trade execution, while the frontend provides an intuitive interactive interface. It implements features like strategy analysis, backtesting, and trade management
. The project is under the MIT License and is currently intended for learning and research purposes only.

## Features

- ✅ **Backend**: Python + FastAPI, providing RESTful API
- ✅ **Frontend**: Vue 3 + Element Plus, modern UI interface
- ✅ **Trading Strategies**: 
  - Moving Average Crossover Strategy (MA)
  - RSI Relative Strength Index Strategy
- ✅ **Real-time Analysis**: Market signal detection and trading recommendations
- ✅ **Backtesting System**: Historical performance backtesting
- ✅ **Trade Management**: Order execution, position management, trade history

## Project Structure

```
quant-trading-platform/
├── backend/              # Backend code
│   ├── main.py          # FastAPI entry point
│   ├── config.py        # Configuration file
│   ├── requirements.txt # Python dependencies
│   ├── strategies/      # Trading strategies
│   │   ├── ma_strategy.py    # Moving Average strategy
│   │   └── rsi_strategy.py   # RSI strategy
│   ├── models/          # Data models
│   │   └── schemas.py   # Pydantic models
│   ├── routers/         # API routes
│   │   ├── trading.py   # Trading related APIs
│   │   └── strategies.py # Strategy related APIs
│   └── utils/           # Utility functions
│       └── data_fetcher.py # Data fetching
│
├── frontend/            # Frontend code
│   ├── src/
│   │   ├── App.vue     # Main application
│   │   ├── main.js     # Entry file
│   │   ├── api/        # API calls
│   │   │   └── index.js
│   │   └── components/ # Vue components
│   │       ├── Dashboard.vue      # Dashboard
│   │       ├── StrategyPanel.vue  # Strategy panel
│   │       └── TradeHistory.vue   # Trade history
│   ├── package.json
│   └── vite.config.js
│
└── README.md
```

## Quick Start

### Backend Setup

```bash
cd backend

# Create virtual environment (optional)
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# Install dependencies using poetry
poetry install

# Start service
python main.py
# Or using uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Backend service will start at http://localhost:8000
API Documentation: http://localhost:8000/docs

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend service will start at http://localhost:3000

## API Interfaces

### Trading Related

- `GET /api/trading/account` - Get account information
- `POST /api/trading/order` - Place trading order
- `GET /api/trading/orders` - Get order list
- `GET /api/trading/history` - Get trade history
- `POST /api/trading/positions/update` - Update position prices

### Strategy Related

- `GET /api/strategies/list` - Get strategy list
- `POST /api/strategies/analyze` - Analyze market signals
- `GET /api/strategies/status/{type}/{symbol}` - Get strategy status
- `POST /api/strategies/backtest` - Run backtest
- `GET /api/strategies/symbols` - Get supported trading symbols

## Trading Strategies

### 1. Moving Average Crossover Strategy (MA)

**Principle**: 
- Short-term MA crosses above long-term MA → Golden Cross → Buy signal
- Short-term MA crosses below long-term MA → Death Cross → Sell signal

**Parameters**:
- `short_window`: Short-term MA period (default: 5)
- `long_window`: Long-term MA period (default: 20)

### 2. RSI Strategy

**Principle**:
- RSI < 30 (Oversold zone) → Buy signal
- RSI > 70 (Overbought zone) → Sell signal

**Parameters**:
- `rsi_period`: RSI calculation period (default: 14)
- `rsi_oversold`: Oversold line (default: 30)
- `rsi_overbought`: Overbought line (default: 70)

## Configuration

Edit `backend/config.py` or create `.env` file:

```env
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True
INITIAL_CAPITAL=100000
COMMISSION_RATE=0.0003
DATA_SOURCE=mock
```

## Technology Stack

**Backend**:
- Python 3.9+
- FastAPI
- Pydantic
- NumPy
- Pandas

**Frontend**:
- Vue 3
- Vite
- Element Plus
- Axios
- Pinia

## Important Notes

⚠️ **This system is for learning and research purposes only**

- Currently uses mock data for backtesting and demonstration
- Real trading requires integration with real data sources and broker APIs
- Investment involves risks, trade with caution
- Do not use directly for real trading

## Development Guide

### Adding New Strategies

1. Create new strategy file in `backend/strategies/`
2. Implement `analyze()` and `get_current_status()` methods
3. Register in `backend/routers/strategies.py`

### Integrating Real Data

Modify `backend/utils/data_fetcher.py`:
- Implement `_fetch_real_data()` method
- Can integrate with Yahoo Finance, JoinQuant, Tushare, etc.

## License

MIT License

## Author

teng