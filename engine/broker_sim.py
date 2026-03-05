"""
虚拟经纪商模块 - 模拟交易账户的资金和持仓管理
"""
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import pandas as pd


class Position:
    """持仓信息类"""

    def __init__(self, symbol: str, quantity: int, avg_price: float):
        self.symbol = symbol  # 股票代码
        self.quantity = quantity  # 持仓数量
        self.avg_price = avg_price  # 平均成本价
        self.market_value = 0.0  # 市值
        self.pnl = 0.0  # 浮动盈亏
        self.pnl_percent = 0.0  # 盈亏百分比

    def update_market_value(self, current_price: float):
        """更新市值和盈亏"""
        self.market_value = self.quantity * current_price
        self.pnl = self.market_value - (self.quantity * self.avg_price)
        if self.quantity * self.avg_price > 0:
            self.pnl_percent = (self.pnl / (self.quantity * self.avg_price)) * 100
        else:
            self.pnl_percent = 0.0

    def __str__(self) -> str:
        return (f"Position({self.symbol}: {self.quantity}股, "
                f"成本:{self.avg_price:.2f}, 盈亏:{self.pnl:.2f}({self.pnl_percent:.1f}%)")


class BrokerSim:
    """虚拟经纪商类"""

    def __init__(self, initial_cash: float = 100000.0):
        self.initial_cash = initial_cash  # 初始资金
        self.cash = initial_cash  # 可用资金
        self.positions: Dict[str, Position] = {}  # 持仓字典
        self.transaction_history: List[Dict] = []  # 交易历史
        self.total_value = initial_cash  # 总资产
        self.day_count = 0  # 交易日计数

    def buy(self, symbol: str, price: float, quantity: int, date: Optional[str] = None) -> bool:
        """买入股票"""
        if quantity <= 0:
            return False

        total_cost = price * quantity
        commission = max(total_cost * 0.0003, 5.0)  # 佣金：万分之三，最低5元
        total_amount = total_cost + commission

        if self.cash < total_amount:
            print(f"资金不足！需要{total_amount:.2f}元，当前可用资金{self.cash:.2f}元")
            return False

        # 扣除资金
        self.cash -= total_amount

        # 更新持仓
        if symbol in self.positions:
            # 已有持仓，计算新的平均成本
            old_position = self.positions[symbol]
            total_quantity = old_position.quantity + quantity
            total_cost = (old_position.quantity * old_position.avg_price) + total_cost
            new_avg_price = total_cost / total_quantity

            self.positions[symbol] = Position(symbol, total_quantity, new_avg_price)
        else:
            # 新建持仓
            self.positions[symbol] = Position(symbol, quantity, price)

        # 记录交易
        transaction = {
            'date': date or datetime.now().strftime('%Y-%m-%d'),
            'symbol': symbol,
            'action': 'BUY',
            'price': price,
            'quantity': quantity,
            'amount': total_cost,
            'commission': commission,
            'cash_after': self.cash
        }
        self.transaction_history.append(transaction)

        print(f"[{transaction['date']}] 买入 {symbol} {quantity}股 @ {price:.2f}元，总金额{total_cost:.2f}元")
        return True

    def sell(self, symbol: str, price: float, quantity: int, date: Optional[str] = None) -> bool:
        """卖出股票"""
        if symbol not in self.positions:
            print(f"没有{symbol}的持仓！")
            return False

        position = self.positions[symbol]

        if quantity <= 0 or quantity > position.quantity:
            print(f"卖出数量无效！当前持仓{position.quantity}股，请求卖出{quantity}股")
            return False

        total_amount = price * quantity
        commission = max(total_amount * 0.0003, 5.0)  # 佣金
        stamp_tax = total_amount * 0.001  # 印花税：千分之一
        total_receivable = total_amount - commission - stamp_tax

        # 增加资金
        self.cash += total_receivable

        # 更新持仓
        if quantity == position.quantity:
            # 全部卖出，删除持仓
            del self.positions[symbol]
        else:
            # 部分卖出，保留持仓
            self.positions[symbol] = Position(symbol, position.quantity - quantity, position.avg_price)

        # 记录交易
        transaction = {
            'date': date or datetime.now().strftime('%Y-%m-%d'),
            'symbol': symbol,
            'action': 'SELL',
            'price': price,
            'quantity': quantity,
            'amount': total_amount,
            'commission': commission,
            'stamp_tax': stamp_tax,
            'cash_after': self.cash
        }
        self.transaction_history.append(transaction)

        print(f"[{transaction['date']}] 卖出 {symbol} {quantity}股 @ {price:.2f}元，实收{total_receivable:.2f}元")
        return True

    def update_portfolio_value(self, price_data: Dict[str, float]):
        """更新投资组合价值"""
        self.day_count += 1
        portfolio_value = self.cash

        for symbol, position in self.positions.items():
            if symbol in price_data:
                current_price = price_data[symbol]
                position.update_market_value(current_price)
                portfolio_value += position.market_value

        self.total_value = portfolio_value
        return portfolio_value

    def get_portfolio_summary(self) -> Dict:
        """获取投资组合摘要"""
        return {
            'initial_cash': self.initial_cash,
            'current_cash': self.cash,
            'total_value': self.total_value,
            'total_return': self.total_value - self.initial_cash,
            'total_return_percent': ((self.total_value - self.initial_cash) / self.initial_cash) * 100,
            'positions_count': len(self.positions),
            'day_count': self.day_count
        }

    def get_positions_detail(self) -> List[Dict]:
        """获取持仓详情"""
        positions_list = []
        for symbol, position in self.positions.items():
            positions_list.append({
                'symbol': symbol,
                'quantity': position.quantity,
                'avg_price': position.avg_price,
                'market_value': position.market_value,
                'pnl': position.pnl,
                'pnl_percent': position.pnl_percent
            })
        return positions_list

    def get_transaction_history(self, limit: int = 10) -> List[Dict]:
        """获取交易历史"""
        return self.transaction_history[-limit:] if limit > 0 else self.transaction_history

    def print_portfolio_status(self):
        """打印投资组合状态"""
        summary = self.get_portfolio_summary()

        print("\n" + "=" * 60)
        print("投资组合状态")
        print("=" * 60)
        print(f"初始资金: {summary['initial_cash']:.2f}元")
        print(f"当前现金: {summary['current_cash']:.2f}元")
        print(f"总资产: {summary['total_value']:.2f}元")
        print(f"总收益: {summary['total_return']:.2f}元 ({summary['total_return_percent']:.2f}%)")
        print(f"持仓数量: {summary['positions_count']}只")
        print(f"交易日数: {summary['day_count']}天")

        if self.positions:
            print("\n持仓详情:")
            for symbol, position in self.positions.items():
                print(f"  {position}")

        print("=" * 60)


# 使用示例
def demo_broker_sim():
    """演示虚拟经纪商的使用"""
    broker = BrokerSim(initial_cash=100000.0)

    # 模拟交易
    broker.buy("000001", 10.5, 1000, "2024-01-01")
    broker.buy("600519", 1500.0, 50, "2024-01-02")

    # 更新市值
    price_data = {"000001": 11.2, "600519": 1550.0}
    broker.update_portfolio_value(price_data)

    # 打印状态
    broker.print_portfolio_status()

    # 卖出部分持仓
    broker.sell("000001", 11.5, 500, "2024-01-03")

    # 再次更新市值
    price_data = {"000001": 11.8, "600519": 1520.0}
    broker.update_portfolio_value(price_data)

    # 最终状态
    broker.print_portfolio_status()


if __name__ == "__main__":
    demo_broker_sim()