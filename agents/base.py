# agents/base.py
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging


class BaseStrategy(ABC):
    """策略基类"""

    def __init__(self, params: Dict = None, name: str = "Unnamed Strategy"):
        self.params = params or {}
        self.name = name
        self.logger = self._setup_logger()
        self.initialized = False

    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger(f"strategy.{self.name}")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

    def initialize(self) -> bool:
        """初始化策略"""
        try:
            self._validate_params()
            self.initialized = True
            self.logger.info(f"策略 {self.name} 初始化成功")
            return True
        except Exception as e:
            self.logger.error(f"策略初始化失败: {e}")
            return False

    def _validate_params(self):
        """验证参数有效性"""
        # 子类可以重写此方法来验证特定参数
        if not isinstance(self.params, dict):
            raise ValueError("参数必须为字典类型")

    @abstractmethod
    def analyze(self, data: Dict[str, List[float]]) -> str:
        """
        分析数据并返回信号
        :param data: 字典形式 { 'etf_name': [price_list] }
        :return: 信号 ('BUY_XXX', 'SELL', 'HOLD')
        """
        pass

    def preprocess_data(self, data: Dict[str, List[float]]) -> Dict[str, List[float]]:
        """数据预处理（可重写）"""
        # 默认实现：返回原始数据
        # 子类可以重写此方法进行数据清洗、标准化等操作
        return data

    def should_execute(self, signal: str, last_signal: Optional[str] = None) -> bool:
        """判断是否应该执行信号（可重写）"""
        # 默认实现：总是执行
        # 子类可以重写此方法添加过滤逻辑
        return True

    def execute(self, signal: str):
        """执行交易"""
        if not self.initialized:
            self.logger.warning("策略未初始化，请先调用 initialize() 方法")
            return

        if self.should_execute(signal):
            self.logger.info(f"执行信号: {signal}")
            # TODO: 对接实盘接口
            print(f"[SIGNAL] {signal}")
        else:
            self.logger.info(f"信号被过滤: {signal}")

    def get_performance_metrics(self) -> Dict[str, Any]:
        """获取策略性能指标（可重写）"""
        return {
            "strategy_name": self.name,
            "initialized": self.initialized,
            "timestamp": datetime.now().isoformat(),
            "params": self.params
        }

    def reset(self):
        """重置策略状态"""
        self.initialized = False
        self.logger.info("策略已重置")

    def __str__(self) -> str:
        return f"{self.name} (BaseStrategy)"

    def __repr__(self) -> str:
        return f"BaseStrategy(name='{self.name}', params={self.params})"