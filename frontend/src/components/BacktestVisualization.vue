<template>
  <el-card class="backtest-chart-card">
    <template #header>
      <div class="chart-header">
        <span>📈 回测结果可视化</span>
        <div class="header-controls">
          <el-button type="primary" size="small" @click="runBacktest" :loading="loading">
            运行回测
          </el-button>
          <el-select v-model="selectedDays" size="small" style="width: 100px; margin-left: 8px;" @change="runBacktest">
            <el-option label="1月" :value="30" />
            <el-option label="2月" :value="60" />
            <el-option label="4月" :value="120" />
            <el-option label="8月" :value="240" />
          </el-select>
        </div>
      </div>
    </template>

    <!-- 回测参数表单 -->
    <el-form :model="backtestConfig" label-width="80px" size="small" style="margin-bottom: 20px;">
      <el-row :gutter="16">
        <el-col :span="6">
          <el-form-item label="策略类型">
            <el-select v-model="backtestConfig.strategy_type" style="width: 100%;">
              <el-option label="均线交叉 (MA)" value="ma" />
              <el-option label="RSI 策略" value="rsi" />
              <el-option label="MACD 策略" value="macd" />
              <el-option label="布林带策略" value="bollinger" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="6">
          <el-form-item label="交易标的">
            <el-select v-model="backtestConfig.symbol" style="width: 100%;">
              <el-option label="贵州茅台 (600519.SS)" value="600519.SS" />
              <el-option label="平安银行 (000001.SZ)" value="000001.SZ" />
              <el-option label="比特币 (BTC-USD)" value="BTC-USD" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="6">
          <el-form-item label="初始资金">
            <el-input-number v-model="backtestConfig.initial_capital" :min="10000" :max="1000000" :step="10000" style="width: 100%;" />
          </el-form-item>
        </el-col>
      </el-row>
    </el-form>

    <!-- 加载状态 -->
    <div v-if="loading" v-loading="true" element-loading-text="回测运行中..." style="height: 400px;"></div>

    <!-- 回测结果 -->
    <div v-else-if="backtestResult">
      <!-- 关键指标卡片 -->
      <el-row :gutter="16" style="margin-bottom: 20px;">
        <el-col :span="4">
          <el-card shadow="hover">
            <div class="metric-item">
              <div class="metric-label">总收益率</div>
              <div class="metric-value" :class="getReturnClass(backtestResult.total_return)">
                {{ backtestResult.total_return >= 0 ? '+' : '' }}{{ backtestResult.total_return.toFixed(2) }}%
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="4">
          <el-card shadow="hover">
            <div class="metric-item">
              <div class="metric-label">年化收益率</div>
              <div class="metric-value" :class="getReturnClass(backtestResult.annual_return)">
                {{ backtestResult.annual_return >= 0 ? '+' : '' }}{{ backtestResult.annual_return.toFixed(2) }}%
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="4">
          <el-card shadow="hover">
            <div class="metric-item">
              <div class="metric-label">最大回撤</div>
              <div class="metric-value negative">-{{ backtestResult.max_drawdown.toFixed(2) }}%</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="4">
          <el-card shadow="hover">
            <div class="metric-item">
              <div class="metric-label">夏普比率</div>
              <div class="metric-value">{{ backtestResult.sharpe_ratio.toFixed(2) }}</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="4">
          <el-card shadow="hover">
            <div class="metric-item">
              <div class="metric-label">胜率</div>
              <div class="metric-value">{{ backtestResult.win_rate.toFixed(1) }}%</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="4">
          <el-card shadow="hover">
            <div class="metric-item">
              <div class="metric-label">总交易数</div>
              <div class="metric-value">{{ backtestResult.total_trades }}</div>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 权益曲线图（模拟数据） -->
      <div ref="equityChartEl" style="height: 350px; margin-bottom: 20px;"></div>

      <!-- 交易明细表格 -->
      <el-collapse v-model="activeTab" style="margin-top: 20px;">
        <el-collapse-item title="📋 交易明细" name="trades">
          <el-table :data="backtestResult.trades.slice(0, 20)" style="width: 100%;" height="250">
            <el-table-column prop="date" label="日期" width="120" />
            <el-table-column prop="type" label="类型" width="80">
              <template #default="scope">
                <el-tag :type="scope.row.type === 'buy' ? 'success' : 'danger'" size="small">
                  {{ scope.row.type === 'buy' ? '买入' : '卖出' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="price" label="价格" width="100">
              <template #default="scope">¥{{ scope.row.price.toFixed(2) }}</template>
            </el-table-column>
            <el-table-column prop="quantity" label="数量" width="80" />
            <el-table-column prop="profit" label="盈亏" width="100">
              <template #default="scope">
                <span v-if="scope.row.profit" :class="scope.row.profit >= 0 ? 'positive' : 'negative'">
                  {{ scope.row.profit >= 0 ? '+' : '' }}{{ scope.row.profit.toFixed(2) }}
                </span>
              </template>
            </el-table-column>
          </el-table>
          <div v-if="backtestResult.trades.length > 20" style="text-align: center; margin-top: 10px;">
            显示前 20 笔交易，共 {{ backtestResult.trades.length }} 笔
          </div>
        </el-collapse-item>
      </el-collapse>
    </div>

    <!-- 空状态 -->
    <div v-else class="empty-state">
      <el-empty description="点击「运行回测」开始分析策略表现" />
    </div>
  </el-card>
</template>

<script setup>
import { ref, reactive, onMounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { strategiesAPI } from '../api'
import { ElMessage } from 'element-plus'

// Props
const props = defineProps({
  initialConfig: {
    type: Object,
    default: () => ({})
  }
})

// 响应式数据
const loading = ref(false)
const backtestResult = ref(null)
const selectedDays = ref(60)
const activeTab = ref(['trades'])
const equityChartEl = ref(null)
let equityChart = null

// 回测配置
const backtestConfig = reactive({
  strategy_type: props.initialConfig.strategy_type || 'ma',
  symbol: props.initialConfig.symbol || '600519.SS',
  short_window: props.initialConfig.short_window || 5,
  long_window: props.initialConfig.long_window || 20,
  rsi_period: props.initialConfig.rsi_period || 14,
  rsi_oversold: props.initialConfig.rsi_oversold || 30,
  rsi_overbought: props.initialConfig.rsi_overbought || 70,
  fast_period: props.initialConfig.fast_period || 12,
  slow_period: props.initialConfig.slow_period || 26,
  signal_period: props.initialConfig.signal_period || 9,
  bb_period: props.initialConfig.bb_period || 20,
  bb_k: props.initialConfig.bb_k || 2.0,
  initial_capital: props.initialConfig.initial_capital || 100000
})

// 生命周期
onMounted(() => {
  // 初始化图表
  nextTick(() => {
    if (equityChartEl.value) {
      equityChart = echarts.init(equityChartEl.value)
    }
  })
})

// 方法
const runBacktest = async () => {
  loading.value = true
  try {
    const result = await strategiesAPI.runBacktest(backtestConfig, selectedDays.value)
    backtestResult.value = result
    
    // 渲染模拟的权益曲线图
    await nextTick()
    renderEquityChart()
    
    ElMessage.success('回测完成！')
  } catch (error) {
    ElMessage.error('回测失败：' + (error.response?.data?.detail || error.message))
  } finally {
    loading.value = false
  }
}

const renderEquityChart = () => {
  if (!backtestResult.value || !equityChart) return
  
  // 生成模拟的权益曲线数据
  const days = selectedDays.value
  const startEquity = 100000
  const finalReturn = backtestResult.value.total_return / 100
  const finalEquity = startEquity * (1 + finalReturn)
  
  // 生成权益曲线点
  const equityData = []
  const dates = []
  for (let i = 0; i <= days; i++) {
    const progress = i / days
    const currentEquity = startEquity + (finalEquity - startEquity) * progress
    // 添加一些随机波动使曲线更真实
    const volatility = 0.02 * Math.sin(i * 0.1) * (1 - progress * 0.5)
    const adjustedEquity = currentEquity * (1 + volatility)
    
    equityData.push(Math.round(adjustedEquity))
    
    // 生成日期
    const date = new Date()
    date.setDate(date.getDate() - (days - i))
    dates.push(date.toISOString().split('T')[0])
  }
  
  const option = {
    title: {
      text: '权益曲线模拟',
      left: 'center',
      textStyle: { fontSize: 14 }
    },
    tooltip: {
      trigger: 'axis',
      formatter: (params) => {
        const p = params[0]
        const return_rate = ((p.value - startEquity) / startEquity * 100).toFixed(2)
        return `${p.name}<br/>权益: ¥${p.value.toLocaleString()}<br/>收益率: ${return_rate}%`
      }
    },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: {
      type: 'category',
      data: dates,
      axisLabel: { rotate: 45 }
    },
    yAxis: {
      type: 'value',
      axisLabel: { formatter: '¥{value}' }
    },
    series: [{
      name: '权益',
      type: 'line',
      data: equityData,
      smooth: true,
      lineStyle: { width: 2, color: '#409EFF' },
      areaStyle: {
        color: {
          type: 'linear',
          x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [{ offset: 0, color: 'rgba(64,158,255,0.3)' }, { offset: 1, color: 'rgba(64,158,255,0.05)' }]
        }
      }
    }]
  }
  
  equityChart.setOption(option)
}

const getReturnClass = (value) => {
  if (value > 0) return 'positive'
  if (value < 0) return 'negative'
  return ''
}

// 监听窗口大小变化
window.addEventListener('resize', () => {
  equityChart?.resize()
})
</script>

<style scoped>
.backtest-chart-card {
  margin-bottom: 20px;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-controls {
  display: flex;
  align-items: center;
}

.metric-item {
  text-align: center;
  padding: 8px;
}

.metric-label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
}

.metric-value {
  font-size: 18px;
  font-weight: bold;
  color: #303133;
}

.metric-value.positive {
  color: #67C23A;
}

.metric-value.negative {
  color: #F56C6C;
}

.empty-state {
  height: 400px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.positive {
  color: #67C23A;
}

.negative {
  color: #F56C6C;
}
</style>