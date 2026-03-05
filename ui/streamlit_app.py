"""
Streamlit 交易数据可视化应用
快速展示资金曲线和持仓表
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
from datetime import datetime, timedelta
import json

# 导入国际化模块
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# 配置页面
st.set_page_config(
    page_title="TenBagger 交易分析",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API 配置
API_BASE_URL = "http://localhost:8000/api"


def fetch_trade_records(days: int = 30):
    """从API获取交易记录"""
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        params = {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'limit': 1000
        }

        response = requests.get(f"{API_BASE_URL}/trades/", params=params)
        if response.status_code == 200:
            return response.json()
        else:
            st.error("API请求失败: {status_code}", status_code=response.status_code)
            return []
    except Exception as e:
        st.error("获取交易记录失败: {}".format(e))
        return []


def fetch_statistics(days: int = 30):
    """获取交易统计信息"""
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        params = {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        }

        response = requests.get(f"{API_BASE_URL}/trades/statistics/summary", params=params)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        st.error(f"获取统计信息失败: {e}")
        return None


def calculate_portfolio_value(trade_records):
    """计算投资组合价值曲线"""
    if not trade_records:
        return pd.DataFrame()

    # 转换为DataFrame
    df = pd.DataFrame(trade_records)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp')

    # 假设初始资金为100000
    initial_cash = 100000.0
    cash = initial_cash
    portfolio_value = []

    # 按日期分组计算
    dates = pd.date_range(start=df['timestamp'].min(), end=datetime.now(), freq='D')

    for date in dates:
        date_str = date.strftime('%Y-%m-%d')

        # 获取该日期前的所有交易
        day_trades = df[df['timestamp'] <= date]

        # 计算持仓和现金
        positions = {}
        day_cash = initial_cash

        for _, trade in day_trades.iterrows():
            symbol = trade['symbol']
            side = trade['side']
            price = trade['price']
            quantity = trade['quantity']

            if side == 'BUY':
                cost = price * quantity
                if cost <= day_cash:
                    day_cash -= cost
                    if symbol not in positions:
                        positions[symbol] = 0
                    positions[symbol] += quantity
            elif side == 'SELL':
                if symbol in positions and positions[symbol] >= quantity:
                    revenue = price * quantity
                    day_cash += revenue
                    positions[symbol] -= quantity
                    if positions[symbol] == 0:
                        del positions[symbol]

        # 计算持仓市值（使用最后交易价格）
        position_value = 0
        for symbol, qty in positions.items():
            # 获取该股票的最后交易价格
            symbol_trades = day_trades[day_trades['symbol'] == symbol]
            if not symbol_trades.empty:
                last_price = symbol_trades.iloc[-1]['price']
                position_value += last_price * qty

        total_value = day_cash + position_value
        portfolio_value.append({
            'date': date,
            'total_value': total_value,
            'cash': day_cash,
            'position_value': position_value,
            'return_percent': (total_value - initial_cash) / initial_cash * 100
        })

    return pd.DataFrame(portfolio_value)


def create_equity_curve_chart(portfolio_df):
    """创建资金曲线图"""
    if portfolio_df.empty:
        return None

    fig = go.Figure()

    # 总资产曲线
    fig.add_trace(go.Scatter(
        x=portfolio_df['date'],
        y=portfolio_df['total_value'],
        mode='lines',
        name='总资产',
        line=dict(color='#1f77b4', width=3),
        hovertemplate='日期: %{x}<br>总资产: %{y:.2f}元<extra></extra>'
    ))

    # 现金曲线
    fig.add_trace(go.Scatter(
        x=portfolio_df['date'],
        y=portfolio_df['cash'],
        mode='lines',
        name='现金',
        line=dict(color='#ff7f0e', width=2),
        hovertemplate='日期: %{x}<br>现金: %{y:.2f}元<extra></extra>'
    ))

    # 持仓市值曲线
    fig.add_trace(go.Scatter(
        x=portfolio_df['date'],
        y=portfolio_df['position_value'],
        mode='lines',
        name='持仓市值',
        line=dict(color='#2ca02c', width=2),
        hovertemplate='日期: %{x}<br>持仓市值: %{y:.2f}元<extra></extra>'
    ))

    fig.update_layout(
        title='资金曲线',
        xaxis_title='日期',
        yaxis_title='金额（元）',
        hovermode='x unified',
        height=400,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    return fig


def create_holdings_table(trade_records):
    """创建持仓表"""
    if not trade_records:
        return pd.DataFrame()

    df = pd.DataFrame(trade_records)
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    # 计算当前持仓
    holdings = {}
    for _, trade in df.iterrows():
        symbol = trade['symbol']
        side = trade['side']
        price = trade['price']
        quantity = trade['quantity']

        if symbol not in holdings:
            holdings[symbol] = {'quantity': 0, 'avg_cost': 0, 'total_cost': 0}

        if side == 'BUY':
            current_total = holdings[symbol]['quantity'] * holdings[symbol]['avg_cost']
            new_total = current_total + price * quantity
            new_quantity = holdings[symbol]['quantity'] + quantity
            holdings[symbol]['avg_cost'] = new_total / new_quantity if new_quantity > 0 else 0
            holdings[symbol]['quantity'] = new_quantity
            holdings[symbol]['total_cost'] = new_total
        elif side == 'SELL':
            holdings[symbol]['quantity'] = max(0, holdings[symbol]['quantity'] - quantity)
            if holdings[symbol]['quantity'] == 0:
                holdings[symbol]['avg_cost'] = 0
                holdings[symbol]['total_cost'] = 0

    # 过滤掉零持仓
    holdings = {k: v for k, v in holdings.items() if v['quantity'] > 0}

    # 转换为DataFrame
    holdings_df = pd.DataFrame([
        {
            '股票代码': symbol,
            '持仓数量': data['quantity'],
            '平均成本': data['avg_cost'],
            '持仓成本': data['total_cost'],
            '当前价格': df[df['symbol'] == symbol].iloc[-1]['price'] if not df[df['symbol'] == symbol].empty else 0
        }
        for symbol, data in holdings.items()
    ])

    if not holdings_df.empty:
        holdings_df['当前市值'] = holdings_df['持仓数量'] * holdings_df['当前价格']
        holdings_df['盈亏'] = holdings_df['当前市值'] - holdings_df['持仓成本']
        holdings_df['盈亏率'] = (holdings_df['盈亏'] / holdings_df['持仓成本'] * 100).round(2)

    return holdings_df


def main():
    """主函数"""
    # 语言选择器
    with st.sidebar:
        st.title("配置")


        days_to_show = st.slider("显示天数", min_value=7, max_value=365, value=90)

    # 主界面
    st.title("📈 TenBagger 交易分析系统")
    st.markdown("---")


    # 加载数据
    with st.spinner("加载交易数据中..."):
        trade_records = fetch_trade_records(days_to_show)
        statistics = fetch_statistics(days_to_show)

    if not trade_records:
        st.warning("未找到交易记录，请确保API服务正在运行")
        st.info("""
        请按以下步骤启动服务：
        1. 确保数据库中有交易记录
        2. 启动FastAPI服务：`uvicorn web.main:app --reload`
        3. 刷新本页面
        """)
        return

    # 显示统计信息
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "总交易笔数",
            f"{statistics['total_trades']}" if statistics else "N/A",
            delta=None
        )

    with col2:
        st.metric(
            "总收益",
            f"{statistics['total_profit']:.2f}元" if statistics else "N/A",
            delta=f"{statistics['total_profit']:.2f}元" if statistics else None
        )

    with col3:
        st.metric(
            "胜率",
            f"{statistics['win_rate']:.1f}%" if statistics else "N/A",
            delta=None
        )

    with col4:
        st.metric(
            "手续费",
            f"{statistics['total_commission']:.2f}元" if statistics else "N/A",
            delta=None
        )

    st.markdown("---")

    # 资金曲线
    st.subheader("💰 资金曲线")
    portfolio_df = calculate_portfolio_value(trade_records)

    if not portfolio_df.empty:
        fig = create_equity_curve_chart(portfolio_df)
        if fig:
            st.plotly_chart(fig, use_container_width=True)

        # 显示最新数据
        latest_data = portfolio_df.iloc[-1]
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("最新总资产", f"{latest_data['total_value']:.2f}元")
        with col2:
            st.metric("现金余额", f"{latest_data['cash']:.2f}元")
        with col3:
            st.metric("总收益率", f"{latest_data['return_percent']:.2f}%")
    else:
        st.info("暂无资金曲线数据")

    st.markdown("---")

    # 持仓表
    st.subheader("📊 持仓明细")
    holdings_df = create_holdings_table(trade_records)

    if not holdings_df.empty:
        st.dataframe(
            holdings_df,
            use_container_width=True,
            hide_index=True
        )

        # 持仓统计
        total_cost = holdings_df['持仓成本'].sum()
        total_value = holdings_df['当前市值'].sum()
        total_profit = holdings_df['盈亏'].sum()

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("总持仓成本", f"{total_cost:.2f}元")
        with col2:
            st.metric("总持仓市值", f"{total_value:.2f}元")
        with col3:
            st.metric("总持仓盈亏", f"{total_profit:.2f}元")
    else:
        st.info("暂无持仓数据")

    st.markdown("---")

    # 交易记录表格
    st.subheader("📋 最近交易记录")
    trades_df = pd.DataFrame(trade_records)
    if not trades_df.empty:
        trades_df['timestamp'] = pd.to_datetime(trades_df['timestamp'])
        trades_df = trades_df.sort_values('timestamp', ascending=False)

        # 选择显示的列
        display_columns = ['timestamp', 'strategy_name', 'symbol', 'side', 'price', 'quantity', 'profit']
        chinese_headers = ['交易时间', '策略名称', '股票代码', '买卖方向', '成交价格', '成交数量', '盈亏金额']
        column_mapping = dict(zip(display_columns, chinese_headers))
        available_columns = [col for col in display_columns if col in trades_df.columns]

        # 创建显示用的DataFrame，使用中文表头
        display_df = trades_df[available_columns].copy()
        display_df.rename(columns=column_mapping, inplace=True)

    st.dataframe(
            display_df.head(20),
            use_container_width=True,
            hide_index=True
        )

    # 底部信息
    st.markdown("---")
    st.caption("数据更新时间: {time}".format(time=datetime.now().strftime('%Y-%m-%d %H:%M:%S')))


if __name__ == "__main__":
    main()