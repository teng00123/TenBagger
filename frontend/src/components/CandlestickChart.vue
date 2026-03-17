<template>
  <el-card class="candlestick-card">
    <template #header>
      <div class="chart-header">
        <span>📊 K 线图</span>
        <div class="header-controls">
          <!-- 标的选择 -->
          <el-select
            v-model="symbol"
            size="small"
            style="width: 180px;"
            @change="reload"
          >
            <el-option label="贵州茅台 (600519.SS)" value="600519.SS" />
            <el-option label="平安银行 (000001.SZ)" value="000001.SZ" />
            <el-option label="比特币 (BTC-USD)"     value="BTC-USD" />
          </el-select>

          <!-- 时间周期 -->
          <el-radio-group v-model="days" size="small" @change="reload" style="margin-left: 8px;">
            <el-radio-button :value="30">1月</el-radio-button>
            <el-radio-button :value="60">2月</el-radio-button>
            <el-radio-button :value="120">4月</el-radio-button>
            <el-radio-button :value="240">8月</el-radio-button>
          </el-radio-group>

          <!-- 均线开关 -->
          <el-checkbox-group v-model="maVisible" size="small" style="margin-left: 12px;">
            <el-checkbox-button value="ma5">MA5</el-checkbox-button>
            <el-checkbox-button value="ma20">MA20</el-checkbox-button>
          </el-checkbox-group>

          <el-button
            type="primary"
            size="small"
            style="margin-left: 8px;"
            :loading="loading"
            @click="reload"
          >
            刷新
          </el-button>
        </div>
      </div>
    </template>

    <!-- 最新行情摘要 -->
    <div v-if="latest" class="quote-bar">
      <span class="quote-symbol">{{ symbol }}</span>
      <span class="quote-price" :class="priceClass">{{ latest.close.toFixed(2) }}</span>
      <span class="quote-label">开</span><span>{{ latest.open.toFixed(2) }}</span>
      <span class="quote-label">高</span><span class="positive">{{ latest.high.toFixed(2) }}</span>
      <span class="quote-label">低</span><span class="negative">{{ latest.low.toFixed(2) }}</span>
      <span class="quote-label">量</span><span>{{ formatVolume(latest.volume) }}</span>
    </div>

    <!-- 图表容器 -->
    <div v-loading="loading" element-loading-text="加载行情中...">
      <div ref="chartEl" :style="{ height: height + 'px', width: '100%' }" />
    </div>

    <div v-if="error" class="chart-error">
      <el-empty :description="error" />
    </div>
  </el-card>
</template>

<script setup>
import { ref, watch, onMounted, onBeforeUnmount, nextTick, computed } from 'vue'
import * as echarts from 'echarts'
import { strategiesAPI } from '../api'

// ── Props ────────────────────────────────────────────────────────
const props = defineProps({
  /** 外部传入标的（可选，内部也有下拉） */
  initialSymbol: { type: String, default: '600519.SS' },
  height: { type: Number, default: 480 },
})

// ── 状态 ─────────────────────────────────────────────────────────
const symbol    = ref(props.initialSymbol)
const days      = ref(60)
const maVisible = ref(['ma5', 'ma20'])
const loading   = ref(false)
const error     = ref('')
const latest    = ref(null)
const chartEl   = ref(null)
let chart       = null

// ── 辅助 ─────────────────────────────────────────────────────────
const priceClass = computed(() => {
  if (!latest.value) return ''
  return latest.value.close >= latest.value.open ? 'positive' : 'negative'
})

const formatVolume = (v) => {
  if (v >= 1e8) return (v / 1e8).toFixed(1) + '亿'
  if (v >= 1e4) return (v / 1e4).toFixed(1) + '万'
  return String(v)
}

// ── ECharts 配置构建 ─────────────────────────────────────────────
const buildOption = (data) => {
  const { dates, ohlcv, ma5, ma20 } = data

  // 涨跌色
  const UP   = '#ef232a'
  const DOWN = '#14b143'

  const series = [
    {
      name: 'K线',
      type: 'candlestick',
      data: ohlcv,
      itemStyle: {
        color:        UP,
        color0:       DOWN,
        borderColor:  UP,
        borderColor0: DOWN,
      },
    },
  ]

  if (maVisible.value.includes('ma5')) {
    series.push({
      name: 'MA5',
      type: 'line',
      data: ma5,
      smooth: true,
      lineStyle: { width: 1.5, color: '#f4a024' },
      showSymbol: false,
    })
  }
  if (maVisible.value.includes('ma20')) {
    series.push({
      name: 'MA20',
      type: 'line',
      data: ma20,
      smooth: true,
      lineStyle: { width: 1.5, color: '#5793f3' },
      showSymbol: false,
    })
  }

  // 成交量柱状图颜色随涨跌
  const volColors = ohlcv.map(d => (d[1] >= d[0] ? UP : DOWN))
  series.push({
    name: '成交量',
    type: 'bar',
    xAxisIndex: 1,
    yAxisIndex: 1,
    data: ohlcv.map((d, i) => ({
      value: d[4],
      itemStyle: { color: volColors[i] },
    })),
    barMaxWidth: 8,
  })

  return {
    animation: false,
    backgroundColor: 'transparent',
    legend: {
      top: 4,
      right: 10,
      data: ['K线', 'MA5', 'MA20'],
      textStyle: { color: '#606266', fontSize: 12 },
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' },
      formatter(params) {
        const candle = params.find(p => p.seriesName === 'K线')
        if (!candle) return ''
        const [o, c, l, h] = candle.data
        const change = ((c - o) / o * 100).toFixed(2)
        const color  = c >= o ? UP : DOWN
        return `
          <div style="font-size:12px;line-height:1.8">
            <b>${candle.name}</b><br/>
            开 ${o}&nbsp;&nbsp;收 <span style="color:${color}">${c}</span><br/>
            高 ${h}&nbsp;&nbsp;低 ${l}<br/>
            涨跌 <span style="color:${color}">${change}%</span>
          </div>
        `
      },
    },
    axisPointer: { link: [{ xAxisIndex: 'all' }] },
    grid: [
      { left: 60, right: 20, top: 40, bottom: 120 },
      { left: 60, right: 20, height: 60, bottom: 50 },
    ],
    xAxis: [
      {
        type: 'category',
        data: dates,
        scale: true,
        boundaryGap: false,
        axisLine: { onZero: false },
        axisLabel: { fontSize: 11 },
        splitLine: { show: false },
        min: 'dataMin',
        max: 'dataMax',
      },
      {
        type: 'category',
        gridIndex: 1,
        data: dates,
        scale: true,
        boundaryGap: false,
        axisLabel: { show: false },
        axisLine: { onZero: false },
        splitLine: { show: false },
        min: 'dataMin',
        max: 'dataMax',
      },
    ],
    yAxis: [
      {
        scale: true,
        splitArea: { show: true },
        axisLabel: { fontSize: 11 },
      },
      {
        scale: true,
        gridIndex: 1,
        splitNumber: 2,
        axisLabel: {
          fontSize: 10,
          formatter: v => formatVolume(v),
        },
        axisLine: { show: false },
        axisTick: { show: false },
        splitLine: { show: false },
      },
    ],
    dataZoom: [
      {
        type: 'inside',
        xAxisIndex: [0, 1],
        start: 50,
        end: 100,
      },
      {
        show: true,
        xAxisIndex: [0, 1],
        type: 'slider',
        bottom: 8,
        start: 50,
        end: 100,
        height: 28,
      },
    ],
    series,
  }
}

// ── 数据加载 ─────────────────────────────────────────────────────
const reload = async () => {
  loading.value = true
  error.value   = ''
  try {
    const data = await strategiesAPI.getKlineData(symbol.value, days.value)
    latest.value = data.latest
    await nextTick()
    if (!chart && chartEl.value) {
      chart = echarts.init(chartEl.value, null, { renderer: 'canvas' })
    }
    if (chart) {
      chart.setOption(buildOption(data), true)
    }
  } catch (e) {
    error.value = '行情数据加载失败：' + (e.response?.data?.detail ?? e.message)
  } finally {
    loading.value = false
  }
}

// 均线开关变化时只重绘，不重新请求数据
watch(maVisible, async () => {
  if (!chart) return
  const data = await strategiesAPI.getKlineData(symbol.value, days.value).catch(() => null)
  if (data) chart.setOption(buildOption(data), true)
})

// ── 响应式 resize ─────────────────────────────────────────────────
const onResize = () => chart?.resize()

onMounted(() => {
  reload()
  window.addEventListener('resize', onResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  chart?.dispose()
  chart = null
})
</script>

<style scoped>
.candlestick-card { margin-bottom: 20px; }

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.header-controls {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 4px;
}

.quote-bar {
  display: flex;
  align-items: baseline;
  gap: 10px;
  font-size: 13px;
  padding: 6px 4px 10px;
  border-bottom: 1px solid #ebeef5;
  margin-bottom: 4px;
  flex-wrap: wrap;
}

.quote-symbol {
  font-weight: 600;
  color: #303133;
  font-size: 15px;
}

.quote-price {
  font-size: 22px;
  font-weight: bold;
  letter-spacing: 0.5px;
}

.quote-label {
  color: #909399;
  margin-left: 6px;
}

.chart-error {
  padding: 20px 0;
}

.positive { color: #ef232a; }
.negative { color: #14b143; }
</style>
