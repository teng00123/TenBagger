# agents/ma_trend.py
from agents.base import BaseStrategy
from data.data_manager import KLineDataManager
from typing import Dict, List, Any
import pandas as pd
from datetime import datetime, timedelta


class MATrendStrategy(BaseStrategy):
    """双均线趋势策略"""

    def __init__(self, params: Dict = None):
        default_params = {
            'short_period': 5,  # 短期均线周期
            'long_period': 20,  # 长期均线周期
            'stock_code': '000001',  # 默认股票代码
            'interval': '1d',  # K线周期
            'lookback_days': 60  # 回看天数
        }

        if params:
            default_params.update(params)

        super().__init__(default_params, name="双均线趋势策略")
        self.name = "双均线趋势策略"
        self.data_manager = KLineDataManager()
        self.history_data = None
        self.signals_history = []

    def _validate_params(self):
        """验证参数有效性"""
        super()._validate_params()

        required_params = ['short_period', 'long_period', 'stock_code', 'interval', 'lookback_days']
        for param in required_params:
            if param not in self.params:
                raise ValueError(f"缺少必要参数: {param}")

        if self.params['short_period'] >= self.params['long_period']:
            raise ValueError("短期均线周期必须小于长期均线周期")

    def load_data(self) -> bool:
        """从数据库加载历史数据"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=self.params['lookback_days'])

            self.history_data = self.data_manager.get_kline_data(
                code=self.params['stock_code'],
                interval=self.params['interval'],
                start_date=start_date.strftime('%Y-%m-%d')
            )

            if self.history_data is None or len(self.history_data) == 0:
                self.logger.warning(f"未找到股票 {self.params['stock_code']} 的历史数据")
                return False

            self.logger.info(f"成功加载 {len(self.history_data)} 条历史数据")
            return True

        except Exception as e:
            self.logger.error(f"加载数据失败: {e}")
            return False

    def calculate_ma_signals(self, data: pd.DataFrame) -> List[Dict[str, Any]]:
        """计算双均线信号"""
        signals = []

        # 计算短期和长期均线
        data['ma_short'] = data['close'].rolling(window=self.params['short_period']).mean()
        data['ma_long'] = data['close'].rolling(window=self.params['long_period']).mean()

        # 计算信号
        for i in range(len(data)):
            if i < self.params['long_period']:
                # 数据不足，无法计算均线
                signal_info = {
                    'date': data.iloc[i]['date'],
                    'close': data.iloc[i]['close'],
                    'ma_short': None,
                    'ma_long': None,
                    'signal': 'HOLD',
                    'reason': '数据不足'
                }
            else:
                ma_short = data.iloc[i]['ma_short']
                ma_long = data.iloc[i]['ma_long']

                if ma_short > ma_long:
                    signal = 'BUY'
                    reason = '短期均线上穿长期均线'
                elif ma_short < ma_long:
                    signal = 'SELL'
                    reason = '短期均线下穿长期均线'
                else:
                    signal = 'HOLD'
                    reason = '均线重合'

                signal_info = {
                    'date': data.iloc[i]['date'],
                    'close': data.iloc[i]['close'],
                    'ma_short': round(ma_short, 2),
                    'ma_long': round(ma_long, 2),
                    'signal': signal,
                    'reason': reason
                }

            signals.append(signal_info)

        return signals

    def analyze(self, data: Dict[str, List[float]]) -> str:
        """
        分析数据并返回信号
        注意：这里我们主要使用从数据库加载的数据进行回测
        """
        if not self.initialized:
            return 'HOLD'

        if self.history_data is None:
            if not self.load_data():
                return 'HOLD'

        # 使用最新的数据点进行分析
        latest_data = self.history_data.iloc[-1]

        # 计算当前信号
        if pd.isna(latest_data.get('ma_short')) or pd.isna(latest_data.get('ma_long')):
            return 'HOLD'

        if latest_data['ma_short'] > latest_data['ma_long']:
            # 创建买入交易记录
            self._create_trade_record('BUY', latest_data)
            return 'BUY'
        elif latest_data['ma_short'] < latest_data['ma_long']:
            # 创建卖出交易记录
            self._create_trade_record('SELL', latest_data)
            return 'SELL'
        else:
            return 'HOLD'

    def _create_trade_record(self, side: str, data: pd.Series):
        """创建交易记录"""
        from api.Trade.models import TradeRecord, TradeSide
        from utils.db import get_db_session

        # 创建数据库会话
        session = get_db_session()
        try:

            # 计算成交金额（假设固定数量100股）
            quantity = 100
            price = data['close']
            amount = price * quantity

            # 创建交易记录
            trade_record = TradeRecord(
                strategy_name=self.name,
                symbol=self.params['stock_code'],
                side=TradeSide.BUY if side == 'BUY' else TradeSide.SELL,
                price=price,
                quantity=quantity,
                amount=amount,
                timestamp=datetime.now(),
                commission=amount * 0.0003,  # 假设手续费为0.03%
                notes=f"双均线策略自动交易，{side}信号触发"
            )

            session.add(trade_record)
            session.commit()
            session.close()

            self.logger.info(f"成功创建{side}交易记录: {self.params['stock_code']} 价格{price}")

        except Exception as e:
            self.logger.error(f"创建交易记录失败: {e}")
            # 回滚会话（如果存在）
            try:
                session.rollback()
                session.close()
            except:
                pass

    def backtest(self) -> Dict[str, Any]:
        """执行回测"""
        if not self.initialized:
            self.logger.warning("策略未初始化")
            return {}

        if not self.load_data():
            return {}

        # 计算所有历史信号
        signals = self.calculate_ma_signals(self.history_data)
        self.signals_history = signals

        # 统计信号分布
        signal_counts = {}
        for signal_info in signals:
            signal = signal_info['signal']
            signal_counts[signal] = signal_counts.get(signal, 0) + 1

        # 计算收益率（简化版）
        total_return = 0
        if len(signals) > 1:
            first_price = signals[0]['close']
            last_price = signals[-1]['close']
            total_return = (last_price - first_price) / first_price * 100

        return {
            'total_signals': len(signals),
            'signal_distribution': signal_counts,
            'total_return_percent': round(total_return, 2),
            'backtest_period': f"{signals[0]['date']} 至 {signals[-1]['date']}"
        }

    def print_signals(self, max_display: int = 20):
        """打印买卖信号"""
        if not self.signals_history:
            self.logger.warning("没有可显示的信号历史")
            return

        print("\n" + "=" * 80)
        print(f"双均线策略信号历史 (显示最近 {min(max_display, len(self.signals_history))} 条)")
        print("=" * 80)

        # 显示最近的信号
        recent_signals = self.signals_history[-max_display:]

        for signal_info in recent_signals:
            date_str = signal_info['date'].strftime('%Y-%m-%d')
            close_price = signal_info['close']
            ma_short = signal_info['ma_short'] or 'N/A'
            ma_long = signal_info['ma_long'] or 'N/A'
            signal = signal_info['signal']
            reason = signal_info['reason']

            print(f"{date_str} | 收盘: {close_price:8.2f} | "
                  f"短期MA: {ma_short:>7} | 长期MA: {ma_long:>7} | "
                  f"信号: {signal:>4} | {reason}")
            # 根据信号类型输出对应的中文描述
            if signal == 'BUY':
                print(f"{date_str} 触发买入信号")
            elif signal == 'SELL':
                print(f"{date_str} 触发卖出信号")
            elif signal == 'HOLD':
                print(f"{date_str} 保持观望信号")
            else:
                print(f"{date_str} 未知信号: {signal}")

        print("=" * 80)

    def run_backtest(self):
        """运行完整的回测流程"""
        self.logger.info("开始双均线策略回测...")

        # 初始化策略
        if not self.initialize():
            return

        # 执行回测
        results = self.backtest()

        if results:
            print("\n" + "=" * 50)
            print("回测结果汇总")
            print("=" * 50)
            print(f"回测期间: {results['backtest_period']}")
            print(f"总信号数: {results['total_signals']}")
            print(f"信号分布: {results['signal_distribution']}")
            print(f"总收益率: {results['total_return_percent']}%")
            print("=" * 50)

            # 打印符合验收标准的信号格式
            print("\n信号详情:")
            self.print_signals()
        else:
            self.logger.error("回测失败")


# 使用示例
if __name__ == "__main__":
    # 创建策略实例
    strategy_params = {
        'short_period': 5,
        'long_period': 20,
        'stock_code': '000001',  # 平安银行
        'interval': '1d',
        'lookback_days': 60
    }

    ma_strategy = MATrendStrategy(strategy_params)
    ma_strategy.run_backtest()