<template>
  <el-card class="strategy-panel">
    <template #header>
      <div class="card-header">
        <span>📊 策略面板</span>
        <el-button type="primary" size="small" @click="runAllStrategies">
          运行所有策略
        </el-button>
      </div>
    </template>
    
    <!-- 策略选择 -->
    <el-form :model="strategyForm" label-width="100px" size="small">
      <el-row :gutter="20">
        <el-col :span="8">
          <el-form-item label="交易策略">
            <el-select v-model="strategyForm.strategyType" style="width: 100%">
              <el-option label="均线交叉策略 (MA)" value="ma" />
              <el-option label="RSI 策略" value="rsi" />
            </el-select>
          </el-form-item>
        </el-col>
        
        <el-col :span="8">
          <el-form-item label="交易标的">
            <el-select v-model="strategyForm.symbol" style="width: 100%">
              <el-option label="贵州茅台 (600519.SS)" value="600519.SS" />
              <el-option label="平安银行 (000001.SZ)" value="000001.SZ" />
              <el-option label="比特币 (BTC-USD)" value="BTC-USD" />
            </el-select>
          </el-form-item>
        </el-col>
        
        <el-col :span="8">
          <el-form-item label="策略参数">
            <el-button size="small" @click="showParams = !showParams">
              {{ showParams ? '隐藏' : '设置' }}
            </el-button>
          </el-form-item>
        </el-col>
      </el-row>
      
      <!-- 策略参数 -->
      <div v-if="showParams" class="strategy-params">
        <el-row v-if="strategyForm.strategyType === 'ma'" :gutter="20">
          <el-col :span="12">
            <el-form-item label="短期周期">
              <el-input-number v-model="strategyForm.shortWindow" :min="1" :max="50" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="长期周期">
              <el-input-number v-model="strategyForm.longWindow" :min="10" :max="200" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row v-if="strategyForm.strategyType === 'rsi'" :gutter="20">
          <el-col :span="8">
            <el-form-item label="RSI 周期">
              <el-input-number v-model="strategyForm.rsiPeriod" :min="5" :max="30" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="超卖线">
              <el-input-number v-model="strategyForm.rsiOversold" :min="10" :max="40" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="超买线">
              <el-input-number v-model="strategyForm.rsiOverbought" :min="60" :max="90" />
            </el-form-item>
          </el-col>
        </el-row>
      </div>
      
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
    <div class="strategy-status">
      <h3>📈 策略状态</h3>
      <el-descriptions :column="3" border v-if="strategyStatus">
        <el-descriptions-item label="策略">{{ strategyStatus.strategy }}</el-descriptions-item>
        <el-descriptions-item label="标的">{{ strategyStatus.symbol }}</el-descriptions-item>
        <el-descriptions-item label="当前价格">
          ¥{{ strategyStatus.current_price?.toFixed(2) }}
        </el-descriptions-item>
        
        <el-descriptions-item v-if="strategyStatus.short_ma" label="短期均线">
          {{ strategyStatus.short_ma?.toFixed(2) }}
        </el-descriptions-item>
        <el-descriptions-item v-if="strategyStatus.long_ma" label="长期均线">
          {{ strategyStatus.long_ma?.toFixed(2) }}
        </el-descriptions-item>
        <el-descriptions-item v-if="strategyStatus.trend" label="趋势">
          <el-tag :type="strategyStatus.trend === 'bullish' ? 'success' : 'danger'">
            {{ strategyStatus.trend === 'bullish' ? '看涨' : '看跌' }}
          </el-tag>
        </el-descriptions-item>
        
        <el-descriptions-item v-if="strategyStatus.rsi" label="RSI">
          <span :class="getRSIColorClass(strategyStatus.rsi)">
            {{ strategyStatus.rsi?.toFixed(2) }}
          </span>
        </el-descriptions-item>
        <el-descriptions-item v-if="strategyStatus.market_state" label="市场状态">
          <el-tag :type="getMarketStateType(strategyStatus.market_state)">
            {{ getMarketStateText(strategyStatus.market_state) }}
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
          <p><strong>标的:</strong> {{ tradeSignal.symbol }}</p>
          <p><strong>价格:</strong> ¥{{ tradeSignal.price.toFixed(2) }}</p>
          <p><strong>数量:</strong> {{ tradeSignal.quantity }} 股</p>
          <p><strong>信号强度:</strong> 
            <el-rate v-model="signalRate" disabled :max="1" style="display: inline-block; transform: scale(0.8);" />
            {{ (tradeSignal.signal_strength * 100).toFixed(0) }}%
          </p>
          <p><strong>策略:</strong> {{ tradeSignal.strategy }}</p>
          <p><strong>原因:</strong> {{ tradeSignal.reason }}</p>
          <el-button 
            :type="tradeSignal.side === 'buy' ? 'success' : 'danger'" 
            size="small"
            @click="executeTrade"
            style="margin-top: 10px;"
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
            {{ backtestResult.total_return.toFixed(2) }}%
          </span>
        </el-descriptions-item>
        <el-descriptions-item label="年化收益">
          <span :class="backtestResult.annual_return >= 0 ? 'positive' : 'negative'">
            {{ backtestResult.annual_return.toFixed(2) }}%
          </span>
        </el-descriptions-item>
        <el-descriptions-item label="最大回撤">
          <span class="negative">{{ backtestResult.max_drawdown.toFixed(2) }}%</span>
        </el-descriptions-item>
        <el-descriptions-item label="夏普比率">{{ backtestResult.sharpe_ratio.toFixed(2) }}</el-descriptions-item>
        <el-descriptions-item label="胜率">{{ backtestResult.win_rate.toFixed(2) }}%</el-descriptions-item>
        <el-descriptions-item label="总交易数">{{ backtestResult.total_trades }}</el-descriptions-item>
      </el-descriptions>
    </div>
  </el-card>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { strategiesAPI, tradingAPI } from '../api'

const strategyForm = reactive({
  strategyType: 'ma',
  symbol: '600519.SS',
  shortWindow: 5,
  longWindow: 20,
  rsiPeriod: 14,
  rsiOversold: 30,
  rsiOverbought: 70
})

const showParams = ref(false)
const analyzing = ref(false)
const strategyStatus = ref(null)
const tradeSignal = ref(null)
const signalRate = ref(0)
const backtestResult = ref(null)

const getRSIColorClass = (rsi) => {
  if (rsi < 30) return 'positive'
  if (rsi > 70) return 'negative'
  return ''
}

const getMarketStateType = (state) => {
  if (state === 'oversold') return 'success'
  if (state === 'overbought') return 'danger'
  return 'info'
}

const getMarketStateText = (state) => {
  const map = {
    'oversold': '超卖',
    'overbought': '超买',
    'neutral': '中性'
  }
  return map[state] || state
}

const analyzeMarket = async () => {
  analyzing.value = true
  try {
    const config = {
      strategy_type: strategyForm.strategyType,
      symbol: strategyForm.symbol,
      short_window: strategyForm.shortWindow,
      long_window: strategyForm.longWindow,
      rsi_period: strategyForm.rsiPeriod,
      rsi_oversold: strategyForm.rsiOversold,
      rsi_overbought: strategyForm.rsiOverbought
    }
    
    // 获取策略状态
    const statusData = await strategiesAPI.getStrategyStatus(
      strategyForm.strategyType,
      strategyForm.symbol,
      {
        short_window: strategyForm.shortWindow,
        long_window: strategyForm.longWindow,
        rsi_period: strategyForm.rsiPeriod
      }
    )
    
    if (statusData.success && statusData.data) {
      strategyStatus.value = statusData.data
    }
    
    // 分析市场信号
    const result = await strategiesAPI.analyzeMarket(config)
    
    if (result.has_signal && result.signal) {
      tradeSignal.value = result.signal
      signalRate.value = result.signal.signal_strength
      ElMessage.success(`发现${result.signal.side === 'buy' ? '买入' : '卖出'}信号！`)
    } else {
      tradeSignal.value = null
      ElMessage.info('当前没有交易信号')
    }
  } catch (error) {
    console.error('分析市场失败:', error)
    ElMessage.error('分析失败：' + (error.response?.data?.detail || error.message))
  } finally {
    analyzing.value = false
  }
}

const runAllStrategies = async () => {
  const strategies = ['ma', 'rsi']
  const symbols = ['600519.SS', '000001.SZ', 'BTC-USD']
  
  for (const strategy of strategies) {
    for (const symbol of symbols) {
      strategyForm.strategyType = strategy
      strategyForm.symbol = symbol
      await analyzeMarket()
    }
  }
}

const executeTrade = async () => {
  if (!tradeSignal.value) return
  
  try {
    const order = {
      symbol: tradeSignal.value.symbol,
      side: tradeSignal.value.side,
      price: tradeSignal.value.price,
      quantity: tradeSignal.value.quantity,
      strategy: tradeSignal.value.strategy
    }
    
    const result = await tradingAPI.placeOrder(order)
    
    if (result.success) {
      ElMessage.success(result.message)
      tradeSignal.value = null
      // 刷新账户信息
      window.location.reload()
    }
  } catch (error) {
    console.error('执行交易失败:', error)
    ElMessage.error('交易失败：' + (error.response?.data?.detail || error.message))
  }
}

const runBacktest = async () => {
  try {
    const config = {
      strategy_type: strategyForm.strategyType,
      symbol: strategyForm.symbol,
      short_window: strategyForm.shortWindow,
      long_window: strategyForm.longWindow,
      rsi_period: strategyForm.rsiPeriod,
      rsi_oversold: strategyForm.rsiOversold,
      rsi_overbought: strategyForm.rsiOverbought
    }
    
    const result = await strategiesAPI.runBacktest(config, 60)
    backtestResult.value = result
    ElMessage.success('回测完成')
  } catch (error) {
    console.error('回测失败:', error)
    ElMessage.error('回测失败：' + (error.response?.data?.detail || error.message))
  }
}
</script>

<style scoped>
.strategy-panel {
  min-height: 600px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.strategy-params {
  background: #f5f7fa;
  padding: 15px;
  border-radius: 4px;
  margin-bottom: 15px;
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

.trade-signal.buy {
  background: #f0f9eb;
  border: 1px solid #e1f3d8;
}

.trade-signal.sell {
  background: #fef0f0;
  border: 1px solid #fde2e2;
}

.positive {
  color: #67C23A;
}

.negative {
  color: #F56C6C;
}

.backtest-result {
  margin-top: 20px;
}
</style>
