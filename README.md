TenBagger/
├── docker-compose.yml       # 容器编排文件
├── Dockerfile               # 镜像构建文件
├── requirements.txt         # 依赖包
├── config.py                # 全局配置（DB连接、API Key等）
├── main.py                  # 程序入口（启动调度器、初始化）
│
├── agents/                  # 【核心】策略智能体模块
│   ├── __init__.py
│   ├── base.py              # 策略抽象基类
│   ├── ma_trend.py          # 双均线趋势策略
│   └── grid_agent.py        # 网格交易策略
│
├── data/                    # 数据服务模块
│   ├── __init__.py
│   ├── models.py            # SQLAlchemy 数据模型
│   ├── downloader.py        # 数据下载器
│   └── feeder.py            # 实时数据推送
│
├── engine/                  # 交易执行引擎
│   ├── __init__.py
│   ├── router.py            # 信号路由（决定发给模拟盘还是实盘）
│   ├── broker_sim.py        # 模拟经纪商（撮合逻辑）
│   └── risk_manager.py      # 风控模块（重要！）
│
├── web/                     # Web 前后端
│   ├── api/                 # FastAPI 后端接口
│   │   └── views.py
│   └── ui/                  # Streamlit 或 Vue 前端页面
│
├── storage/                 # 本地存储（日志、数据文件）
└── tests/   