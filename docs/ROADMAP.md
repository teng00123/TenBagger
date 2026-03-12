# TenBagger 迭代路线图

> 最后更新：2026-03-12

## 当前状态（v0.1.0 基线）

**已完成：**
- ✅ 后端 FastAPI：MA 策略 + RSI 策略 + 模拟交易
- ✅ 前端 Vue3：Dashboard / StrategyPanel / TradeHistory
- ✅ 66 个单元测试，全部通过
- ✅ CI 流水线：commit check + PR diff review + 单测 + Docker build + secrets 扫描
- ✅ Docker 一键部署（docker-compose）
- ✅ 双语 README（EN + CN）

**已知短板：**
- DataFetcher 仅 mock 数据，无真实行情
- 仅 2 个策略（MA / RSI），策略扩展性差
- 交易状态存内存（重启丢失），无持久化
- 前端 3 个组件，功能偏简单
- 无用户认证

---

## Milestone v0.2 — 真实数据 & 策略扩展
> 预计工作量：3–5 天

### 🔴 P0（核心，必做）

| # | 任务 | 文件 | 说明 |
|---|------|------|------|
| 1 | **接入真实行情数据** | `backend/utils/data_fetcher.py` | 对接 Yahoo Finance (`yfinance`) 或 AkShare（国内免费）；保留 `use_mock=True` 开关 |
| 2 | **新增 MACD 策略** | `backend/strategies/macd_strategy.py` | MACD 金叉/死叉信号；补充 8 个单测 |
| 3 | **新增布林带策略** | `backend/strategies/bollinger_strategy.py` | 价格触及上/下轨信号；补充 8 个单测 |
| 4 | **策略注册机制** | `backend/strategies/__init__.py` | 用字典注册策略，新增策略只需加一行，无需改 router |

### 🟡 P1（重要，尽量做）

| # | 任务 | 文件 | 说明 |
|---|------|------|------|
| 5 | **交易状态持久化** | `backend/routers/trading.py` + `backend/db/` | SQLite（轻量）存储持仓 / 订单历史；重启不丢数据 |
| 6 | **前端策略选择组件** | `frontend/src/components/StrategySelector.vue` | 下拉选 MA / RSI / MACD / 布林带，动态切换图表 |
| 7 | **K 线图组件** | `frontend/src/components/CandlestickChart.vue` | 接入 ECharts 或 lightweight-charts，渲染真实 K 线 |

### 🟢 P2（锦上添花）

| # | 任务 | 说明 |
|---|------|------|
| 8 | 回测结果可视化 | 前端展示回测净值曲线、最大回撤、胜率 |
| 9 | 策略参数可配置 | 前端允许调整均线周期、RSI 阈值等参数 |

---

## Milestone v0.3 — 持仓管理 & 风控
> 预计工作量：3–5 天

### 🔴 P0

| # | 任务 | 文件 | 说明 |
|---|------|------|------|
| 1 | **动态仓位管理器**（关联 Issue #4）| `backend/utils/position_manager.py` | 凯利公式 / 固定比例；下单时自动计算建议手数 |
| 2 | **止损 / 止盈逻辑** | `backend/routers/trading.py` | 下单时可附 stop_loss / take_profit 价格；后台定时检查 |
| 3 | **风险指标 API** | `backend/routers/risk.py` | 返回：最大回撤、夏普比率、胜率、盈亏比 |

### 🟡 P1

| # | 任务 | 说明 |
|---|------|------|
| 4 | **多仓位同时持有** | 当前只支持单只股票，扩展为多标的组合 |
| 5 | **告警通知** | 信号触发时通过 webhook / 邮件推送 |
| 6 | **前端风险仪表盘** | 展示组合盈亏、持仓分布饼图 |

---

## Milestone v0.4 — 生产就绪
> 预计工作量：5–7 天

| # | 任务 | 说明 |
|---|------|------|
| 1 | **用户认证** | JWT + 登录接口；保护交易 API |
| 2 | **定时任务** | APScheduler：每分钟拉最新价格，自动触发策略分析 |
| 3 | **PostgreSQL 迁移** | 从 SQLite 迁移；支持多用户 |
| 4 | **监控接入** | Prometheus metrics + Grafana dashboard |
| 5 | **E2E 测试** | Playwright 覆盖核心前端流程 |
| 6 | **GitHub Actions CD** | 推 tag → 自动构建镜像 → 推 Docker Hub |

---

## 下个迭代（v0.2）建议顺序

```
Week 1（Day 1–3）
├── Day 1: 接入 AkShare 真实行情（含开关、缓存）
├── Day 2: MACD 策略实现 + 单测
└── Day 3: 布林带策略实现 + 单测 + 策略注册机制

Week 1（Day 4–5）
├── Day 4: SQLite 持久化交易状态
└── Day 5: 前端 K 线图 + 策略选择组件
```

---

## 技术债 & 已知问题

| 优先级 | 问题 | 位置 |
|--------|------|------|
| 🔴 高 | GitHub Token 曾明文出现在对话中，**必须立即撤销并轮换** | — |
| 🔴 高 | `trading_state` 是全局内存变量，多进程/重启会丢失数据 | `backend/routers/trading.py` |
| 🟡 中 | `DataFetcher._fetch_real_data` 是空实现（raise NotImplementedError）| `backend/utils/data_fetcher.py` |
| 🟡 中 | 前端 `main.js` 而非 `main.ts`，项目声称 Vue3 但未用 TypeScript | `frontend/src/` |
| 🟢 低 | `poetry.lock` 与 `requirements.txt` 并存，维护两套依赖 | `backend/` |
| 🟢 低 | CI `ci-tests.yml` 的 Docker 构建 job 每次完整 build，无层缓存 | `.github/workflows/` |
