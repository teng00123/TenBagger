<template>
  <el-card class="strategy-panel">
    <template #header>
      <div class="card-header">
        <span>📊 策略面板</span>
        <el-button type="primary" size="small" @click="runAllStrategies" :loading="analyzing">
          运行所有策略
        </el-button>
      </div>
    </template>

    <!-- 策略选择器组件 -->
    <el-form label-width="100px" size="small">
      <StrategySelector v-model="strategyConfig" @change="onConfigChange" />

      <el-form-item>
        <el-button type="primary" @click="analyzeMarket" :loading="analyzing">
          分析市场
        </el-button>
        <el-button @click="runBacktest">
          运行回测
        </el-button>
      </el-form-item>
    </el-form>

    <el-divider />

    <!-- 策略状态 -->
    <div v-if="strategyStatus" class="strategy-status">
      <h3>📈 策略状态</h3>
      <el-descriptions :column="3" border>
        <el-descriptions-item label="策略">{{ strategyStatus.strategy }}</el-descriptions-item>
        <el-descriptions-item label="标的">{{ strategyStatus.symbol }}</el-descriptions-item>
        <el-descriptions-item label="当前价格">
          ¥{{ strategyStatus.current_price?.toFixed(2) }}
        </el-descriptions-item>

        <!-- MA -->
        <el-descriptions-item v-if="strategyStatus.short_ma" label="短期均线">
          {{ strategyStatus.short_ma?.toFixed(2) }}
        </el-descriptions-item>
        <el-descriptions-item v-if="strategyStatus.long_ma" label="长期均线">
          {{ strategyStatus.long_ma?.toFixed(2) }}
        </el-descriptions-item>

        <!-- RSI -->
        <el-descriptions-item v-if="strategyStatus.rsi != null" label="RSI">
          <span :class="getRSIClass(strategyStatus.rsi)">
            {{ strategyStatus.rsi?.toFixed(2) }}
          </span>
        </el-descriptions-item>

        <!-- MACD -->
        <el-descriptions-item v-if="strategyStatus.macd != null" label="MACD">
          {{ strategyStatus.macd?.toFixed(4) }}
        </el-descriptions-item>
        <el-descriptions-item v-if="strategyStatus.signal != null" label="信号线">
          {{ strategyStatus.signal?.toFixed(4) }}
        </el-descriptions-item>
        <el-descriptions-item v-if="strategyStatus.histogram != null" label="柱状图">
          <span :class="strategyStatus.histogram >= 0 ? 'positive' : 'negative'">
            {{ strategyStatus.histogram?.toFixed(4) }}
          </span>
        </el-descriptions-item>

        <!-- 布林带 -->
        <el-descriptions-item v-if="strategyStatus.upper_band != null" label="上轨">
          {{ strategyStatus.upper_band?.toFixed(2) }}
        </el-descriptions-item>
        <el-descriptions-item v-if="strategyStatus.middle_band != null" label="中轨">
          {{ strategyStatus.middle_band?.toFixed(2) }}
        </el-descriptions-item>
        <el-descriptions-item v-if="strategyStatus.lower_band != null" label="下轨">
          {{ strategyStatus.lower_band?.toFixed(2) }}
        </el-descriptions-item>

        <!-- 趋势/市场状态 -->
        <el-descriptions-item v-if="strategyStatus.trend" label="趋势">
          <el-tag :type="strategyStatus.trend === 'bullish' ? 'success' : (strategyStatus.trend === 'bearish' ? 'danger' : 'info')">
            {{ trendText(strategyStatus.trend) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item v-if="strategyStatus.market_state" label="市场状态">
          <el-tag :type="marketStateType(strategyStatus.market_state)">
            {{ marketStateText(strategyStatus.market_state) }}
          </el-tag>
        </el-descriptions-item>
      </el-descriptions>
    </div>

    <!-- 交易信号 -->
    <div v-if="tradeSignal" class="trade-signal" :class="tradeSignal.side">
      <h3>🔔 交易信号</h3>
      <el-alert
        :title="tradeSignal.side === 'buy' ? '买入信号' : '卖出信号'"
        :type="tradeSignal.side === 'buy' ? 'success' : 'warning'"
        :closable="false"
        show-icon
      >
        <template #default>
          <p><strong>标的：</strong>{{ tradeSignal.symbol }}</p>
          <p><strong>价格：</strong>¥{{ tradeSignal.price?.toFixed(2) }}</p>
          <p><strong>数量：</strong>{{ tradeSignal.quantity }} 股</p>
          <p><strong>信号强度：</strong>{{ (tradeSignal.signal_strength * 100).toFixed(0) }}%</p>
          <p><strong>策略：</strong>{{ tradeSignal.strategy }}</p>
          <p><strong>原因：</strong>{{ tradeSignal.reason }}</p>
          <el-button
            :type="tradeSignal.side === 'buy' ? 'success' : 'danger'"
            size="small"
            style="margin-top: 10px;"
            @click="executeTrade"
          >
            执行交易
          </el-button>
        </template>
      </el-alert>
    </div>

    <!-- 回测结果 -->
    <div v-if="backtestResult" class="backtest-result">
      <h3>📊 回测结果</h3>
      <el-descriptions :column="4" border>
        <el-descriptions-item label="总收益">
          <span :class="backtestResult.total_return >= 0 ? 'positive' : 'negative'">
            {{ backtestResult.total_return?.toFixed(2) }}%
          </span>
        </el-descriptions-item>
        <el-descriptions-item label="年化收益">
          <span :class="backtestResult.annual_return >= 0 ? 'positive' : 'negative'">
            {{ backtestResult.annual_return?.toFixed(2) }}%
          </span>
        </el-descriptions-item>
        <el-descriptions-item label="最大回撤">
          <span class="negative">{{ backtestResult.max_drawdown?.toFixed(2) }}%</span>
        </el-descriptions-item>
        <el-descriptions-item label="夏普比率">{{ backtestResult.sharpe_ratio?.toFixed(2) }}</el-descriptions-item>
        <el-descriptions-item label="胜率">{{ backtestResult.win_rate?.toFixed(2) }}%</el-descriptions-item>
        <el-descriptions-item label="总交易数">{{ backtestResult.total_trades }}</el-descriptions-item>
      </el-descriptions>
    </div>
  </el-card>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { strategiesAPI, tradingAPI } from '../api'
import StrategySelector from './StrategySelector.vue'

// ── 状态 ─────────────────────────────────────────────────────────
const strategyConfig = reactive({
  strategy_type:  'ma',
  symbol:         '600519.SS',
  short_window:   5,
  long_window:    20,
  rsi_period:     14,
  rsi_oversold:   30,
  rsi_overbought: 70,
  fast_period:    12,
  slow_period:    26,
  signal_period:  9,
  bb_period:      20,
  bb_k:           2.0,
})

const analyzing     = ref(false)
const strategyStatus = ref(null)
const tradeSignal   = ref(null)
const backtestResult = ref(null)

// ── 辅助函数 ─────────────────────────────────────────────────────
const getRSIClass = (rsi) => rsi < 30 ? 'positive' : rsi > 70 ? 'negative' : ''

const trendText = (t) => ({ bullish: '看涨 ↑', bearish: '看跌 ↓', neutral: '震荡 →' }[t] ?? t)

const marketStateType = (s) =>
  ({ oversold: 'success', overbought: 'danger', upper_half: 'warning', lower_half: 'info' }[s] ?? 'info')

const marketStateText = (s) =>
  ({ oversold: '超卖', overbought: '超买', upper_half: '偏强', lower_half: '偏弱' }[s] ?? s)

// ── 事件 ─────────────────────────────────────────────────────────
const onConfigChange = (cfg) => {
  Object.assign(strategyConfig, cfg)
  // 切换策略时清空上次结果
  strategyStatus.value = null
  tradeSignal.value    = null
}

// ── API 调用 ─────────────────────────────────────────────────────
const analyzeMarket = async () => {
  analyzing.value = true
  try {
    // 1. 获取策略状态
    const statusRes = await strategiesAPI.getStrategyStatus(
      strategyConfig.strategy_type,
      strategyConfig.symbol,
      {
        short_window:  strategyConfig.short_window,
        long_window:   strategyConfig.long_window,
        rsi_period:    strategyConfig.rsi_period,
        fast_period:   strategyConfig.fast_period,
        slow_period:   strategyConfig.slow_period,
        signal_period: strategyConfig.signal_period,
        period:        strategyConfig.bb_period,
        k:             strategyConfig.bb_k,
      }
    )
    if (statusRes?.success && statusRes.data) {
      strategyStatus.value = statusRes.data
    }

    // 2. 分析信号
    const result = await strategiesAPI.analyzeMarket({ ...strategyConfig })
    if (result.has_signal && result.signal) {
      tradeSignal.value = result.signal
      ElMessage.success(`发现${result.signal.side === 'buy' ? '买入' : '卖出'}信号！`)
    } else {
      tradeSignal.value = null
      ElMessage.info('当前没有交易信号')
    }
  } catch (e) {
    ElMessage.error('分析失败：' + (e.response?.data?.detail ?? e.message))
  } finally {
    analyzing.value = false
  }
}

const runAllStrategies = async () => {
  const types   = ['ma', 'rsi', 'macd', 'bollinger']
  const symbols = ['600519.SS', '000001.SZ', 'BTC-USD']
  for (const strategy_type of types) {
    for (const symbol of symbols) {
      Object.assign(strategyConfig, { strategy_type, symbol })
      await analyzeMarket()
    }
  }
}

const executeTrade = async () => {
  if (!tradeSignal.value) return
  try {
    const result = await tradingAPI.placeOrder({
      symbol:   tradeSignal.value.symbol,
      side:     tradeSignal.value.side,
      price:    tradeSignal.value.price,
      quantity: tradeSignal.value.quantity,
      strategy: tradeSignal.value.strategy,
    })
    if (result.success) {
      ElMessage.success(result.message)
      tradeSignal.value = null
    }
  } catch (e) {
    ElMessage.error('交易失败：' + (e.response?.data?.detail ?? e.message))
  }
}

const runBacktest = async () => {
  try {
    const result = await strategiesAPI.runBacktest({ ...strategyConfig }, 60)
    backtestResult.value = result
    ElMessage.success('回测完成')
  } catch (e) {
    ElMessage.error('回测失败：' + (e.response?.data?.detail ?? e.message))
  }
}
</script>

<style scoped>
.strategy-panel { min-height: 600px; }

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.strategy-status h3,
.trade-signal h3,
.backtest-result h3 {
  margin-bottom: 15px;
  font-size: 16px;
  color: #303133;
}

.trade-signal {
  margin-top: 20px;
  padding: 15px;
  border-radius: 4px;
}
.trade-signal.buy  { background: #f0f9eb; border: 1px solid #e1f3d8; }
.trade-signal.sell { background: #fef0f0; border: 1px solid #fde2e2; }

.backtest-result { margin-top: 20px; }

.positive { color: #67C23A; }
.negative { color: #F56C6C; }
</style>
