
class DynamicPositionManager:
    """动态仓位管理器"""

    def __init__(self, account_balance, max_position_ratio=0.3, risk_per_trade=0.02):
        """
        account_balance: 账户总资金
        max_position_ratio: 单只标的最大仓位比例，默认30%
        risk_per_trade: 单笔交易最大亏损比例，默认2%
        """
        self.account_balance = account_balance
        self.max_position_ratio = max_position_ratio
        self.risk_per_trade = risk_per_trade

    def calculate_position_size(self, current_price, stop_loss_price, contract_multiplier=1):
        """
        根据止损价计算建议持仓手数
        """
        # 单笔交易最大风险金额
        max_risk_amount = self.account_balance * self.risk_per_trade

        # 每手合约的风险金额
        risk_per_contract = abs(current_price - stop_loss_price) * contract_multiplier

        if risk_per_contract > 0:
            # 基于风险计算的仓位
            position_size = int(max_risk_amount / risk_per_contract)
            # 受最大仓位比例限制
            max_position_by_ratio = int(self.account_balance * self.max_position_ratio / current_price)
            return min(position_size, max_position_by_ratio)
        return 1  # 默认返回最小单位


# 使用示例
manager = DynamicPositionManager(account_balance=100000)
current_price = 15.0
stop_loss_price = 14.7  # 假设止损价
position_size = manager.calculate_position_size(current_price, stop_loss_price)
print(f"建议持仓: {position_size} 股")
