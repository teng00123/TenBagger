"""
交易引擎模块 - 连接策略信号与模拟经纪商
实现"信号 -> 虚拟成交 -> 更新持仓"的完整闭环
支持定时任务调度
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
import pandas as pd
import schedule
import time as time_module
from agents.base import BaseStrategy
from engine.broker_sim import BrokerSim


class TradingEngine:
    """交易引擎类"""

    def __init__(self, strategy: BaseStrategy, initial_cash: float = 100000.0):
        self.strategy = strategy
        self.broker = BrokerSim(initial_cash)
        self.trading_log: List[Dict] = []
        self.current_date: Optional[str] = None
        self.is_running = False

    def set_current_date(self, date: str):
        """设置当前交易日"""
        self.current_date = date

    def process_signal(self, signal: str, price_data: Dict[str, float]) -> bool:
        """
        处理策略信号并执行交易
        :param signal: 策略信号 (格式: "BUY_股票代码" 或 "SELL_股票代码")
        :param price_data: 当前价格数据 {股票代码: 价格}
        :return: 是否成功执行交易
        """
        if not signal:
            return False

        # 解析信号
        signal_parts = signal.split('_')
        if len(signal_parts) < 2:
            print(f"无效的信号格式: {signal}")
            return False

        action = signal_parts[0].upper()
        symbol = signal_parts[1]

        if symbol not in price_data:
            print(f"价格数据中未找到股票 {symbol}")
            return False

        current_price = price_data[symbol]

        # 根据信号类型执行交易
        if action == "BUY":
            return self._execute_buy(symbol, current_price)
        elif action == "SELL":
            return self._execute_sell(symbol, current_price)
        elif action == "HOLD":
            print(f"[{self.current_date or datetime.now().strftime('%Y-%m-%d')}] 保持观望: {symbol}")
            return True
        else:
            print(f"未知的交易信号: {signal}")
            return False

    def _execute_buy(self, symbol: str, price: float) -> bool:
        """执行买入操作"""
        # 计算买入数量（基于可用资金的80%）
        available_cash = self.broker.cash
        max_investment = available_cash * 0.8

        # 计算可买入的股票数量（取整百股）
        quantity = int(max_investment // (price * 100)) * 100

        if quantity <= 0:
            print(f"资金不足，无法买入 {symbol}")
            return False

        # 执行买入
        success = self.broker.buy(symbol, price, quantity, self.current_date)

        if success:
            log_entry = {
                'date': self.current_date or datetime.now().strftime('%Y-%m-%d'),
                'symbol': symbol,
                'action': 'BUY',
                'price': price,
                'quantity': quantity,
                'signal_type': '自动买入'
            }
            self.trading_log.append(log_entry)
            print(f"[{log_entry['date']}] 自动买入 {symbol} {quantity}股 @ {price:.2f}元")

        return success

    def _execute_sell(self, symbol: str, price: float) -> bool:
        """执行卖出操作"""
        if symbol not in self.broker.positions:
            print(f"没有 {symbol} 的持仓，无法卖出")
            return False

        position = self.broker.positions[symbol]

        # 卖出全部持仓
        quantity = position.quantity

        # 执行卖出
        success = self.broker.sell(symbol, price, quantity, self.current_date)

        if success:
            log_entry = {
                'date': self.current_date or datetime.now().strftime('%Y-%m-%d'),
                'symbol': symbol,
                'action': 'SELL',
                'price': price,
                'quantity': quantity,
                'signal_type': '自动卖出'
            }
            self.trading_log.append(log_entry)
            print(f"[{log_entry['date']}] 自动卖出 {symbol} {quantity}股 @ {price:.2f}元")

        return success

    def update_portfolio(self, price_data: Dict[str, float]):
        """更新投资组合价值"""
        self.broker.update_portfolio_value(price_data)

    def daily_trading_job(self, symbol: str = "000001"):
        """
        每日收盘后运行的交易任务
        :param symbol: 股票代码
        """
        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 执行每日收盘交易任务")

        # 获取当日收盘价（这里模拟获取最新价格）
        from web.data.data_manager import KLineDataManager
        manager = KLineDataManager()

        # 获取最近一个交易日的数据
        recent_data = manager.get_kline_data(
            symbol,
            interval='1d',
            start_date=(datetime.now() - pd.Timedelta(days=7)).strftime('%Y-%m-%d'),
            end_date=datetime.now().strftime('%Y-%m-%d')
        )

        if recent_data is None or len(recent_data) == 0:
            print("未获取到当日数据")
            return

        # 获取最新数据（最后一行）
        latest_data = recent_data.iloc[-1]
        current_date = latest_data['date'].strftime('%Y-%m-%d')
        current_price = latest_data['close']

        self.set_current_date(current_date)

        # 准备策略分析数据
        strategy_data = {
            symbol: [latest_data['close'], latest_data['ma5'], latest_data['ma10'], latest_data['ma20']]
        }

        # 获取策略信号
        signal = self.strategy.analyze(strategy_data)

        # 准备价格数据
        price_data = {symbol: current_price}

        # 处理信号
        if signal and signal != "HOLD":
            print(f"[{current_date}] 生成信号: {signal}")
            self.process_signal(signal, price_data)
        else:
            print(f"[{current_date}] 无交易信号，保持观望")

        # 更新投资组合价值
        self.update_portfolio(price_data)

        # 打印当前状态
        self.print_current_status()

    def start_daily_schedule(self, symbol: str = "000001", schedule_time: str = "16:00"):
        """
        启动每日定时任务
        :param symbol: 股票代码
        :param schedule_time: 执行时间，格式 "HH:MM"
        """
        print(f"启动定时任务，每天 {schedule_time} 执行交易策略")

        # 清除所有现有任务
        schedule.clear()

        # 添加每日任务
        schedule.every().day.at(schedule_time).do(self.daily_trading_job, symbol=symbol)

        self.is_running = True

        print("定时任务已启动，按 Ctrl+C 停止")

        try:
            while self.is_running:
                schedule.run_pending()
                time_module.sleep(1)
        except KeyboardInterrupt:
            print("\n定时任务已停止")
            self.is_running = False

    def stop_schedule(self):
        """停止定时任务"""
        self.is_running = False
        schedule.clear()
        print("定时任务已停止")

    def run_backtest(self, historical_data: pd.DataFrame, symbol: str = "000001") -> Dict[str, Any]:
        """
        运行回测
        :param historical_data: 历史数据DataFrame
        :param symbol: 股票代码
        :return: 回测结果
        """
        print(f"开始回测 {symbol}，初始资金: {self.broker.initial_cash:.2f}元")
        print("=" * 60)

        signals_executed = 0
        trades_executed = 0

        # 按日期遍历历史数据
        for index, row in historical_data.iterrows():
            date_str = row['date'].strftime('%Y-%m-%d') if hasattr(row['date'], 'strftime') else str(row['date'])
            self.set_current_date(date_str)

            # 准备价格数据
            price_data = {symbol: row['close']}

            # 准备策略分析数据
            strategy_data = {
                symbol: [row['close'], row['ma5'], row['ma10'], row['ma20']]
            }

            # 获取策略信号
            signal = self.strategy.analyze(strategy_data)

            # 处理信号
            if signal and signal != "HOLD":
                signals_executed += 1
                trade_success = self.process_signal(signal, price_data)
                if trade_success:
                    trades_executed += 1

            # 更新投资组合价值
            self.update_portfolio(price_data)

        # 回测结果统计
        portfolio_summary = self.broker.get_portfolio_summary()

        result = {
            'initial_cash': portfolio_summary['initial_cash'],
            'final_value': portfolio_summary['total_value'],
            'total_return': portfolio_summary['total_return'],
            'total_return_percent': portfolio_summary['total_return_percent'],
            'signals_generated': signals_executed,
            'trades_executed': trades_executed,
            'positions_count': portfolio_summary['positions_count'],
            'trading_days': portfolio_summary['day_count'],
            'trading_log': self.trading_log[-10:]  # 最近10笔交易
        }

        return result

    def print_backtest_result(self, result: Dict[str, Any]):
        """打印回测结果"""
        print("\n" + "=" * 60)
        print("回测结果汇总")
        print("=" * 60)
        print(f"初始资金: {result['initial_cash']:.2f}元")
        print(f"最终资产: {result['final_value']:.2f}元")
        print(f"总收益: {result['total_return']:.2f}元 ({result['total_return_percent']:.2f}%)")
        print(f"信号数量: {result['signals_generated']}")
        print(f"成交笔数: {result['trades_executed']}")
        print(f"持仓数量: {result['positions_count']}")
        print(f"交易日数: {result['trading_days']}")

        if result['trading_log']:
            print("\n最近交易记录:")
            for trade in result['trading_log']:
                print(f"  {trade['date']} {trade['action']} {trade['symbol']} "
                      f"{trade['quantity']}股 @ {trade['price']:.2f}元")

        print("=" * 60)

    def get_portfolio_status(self):
        """获取当前投资组合状态"""
        return self.broker.get_portfolio_summary()

    def print_current_status(self):
        """打印当前投资组合状态"""
        self.broker.print_portfolio_status()


# 使用示例
def demo_trading_engine():
    """演示交易引擎的使用"""
    from agents.ma_trend import MATrendStrategy
    from web.data.data_manager import KLineDataManager

    # 创建策略
    strategy = MATrendStrategy({
        'short_window': 5,
        'long_window': 20
    })
    strategy.initialize()

    # 创建交易引擎
    engine = TradingEngine(strategy, initial_cash=100000.0)

    # 获取历史数据
    manager = KLineDataManager()
    historical_data = manager.get_kline_data(
        "000001",
        interval='1d',
        start_date='2024-01-01',
        end_date='2024-12-31'
    )

    if historical_data is None or len(historical_data) == 0:
        print("未获取到历史数据，请先下载数据")
        return

    # 运行回测
    result = engine.run_backtest(historical_data, "000001")

    # 打印结果
    engine.print_backtest_result(result)

    # 打印当前状态
    engine.print_current_status()


def demo_schedule():
    """演示定时任务功能"""
    from agents.ma_trend import MATrendStrategy

    print("=== 定时任务演示 ===")

    # 创建策略
    strategy = MATrendStrategy({
        'short_window': 5,
        'long_window': 20
    })
    strategy.initialize()

    # 创建交易引擎
    engine = TradingEngine(strategy, initial_cash=100000.0)

    # 立即执行一次（模拟收盘后运行）
    print("立即执行一次收盘任务:")
    # engine.daily_trading_job("000001")
    engine.start_daily_schedule(symbol="000001", schedule_time="16:00")

    print("\n=== 定时任务说明 ===")
    print("要启动真正的定时任务，请调用: engine.start_daily_schedule(symbol='000001', schedule_time='16:00')")
    print("这将在每天16:00（收盘后）自动执行交易策略")


if __name__ == "__main__":
    # 可以选择运行回测演示或定时任务演示
    demo_trading_engine()
    # demo_schedule()  # 取消注释来演示定时任务