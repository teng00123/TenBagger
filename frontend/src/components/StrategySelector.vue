<template>
  <div class="strategy-selector">
    <!-- 策略 & 标的选择行 -->
    <el-row :gutter="16">
      <el-col :span="8">
        <el-form-item label="交易策略">
          <el-select
            v-model="localStrategyType"
            style="width: 100%"
            @change="onStrategyChange"
          >
            <el-option
              v-for="s in strategies"
              :key="s.type"
              :label="s.name"
              :value="s.type"
            />
          </el-select>
        </el-form-item>
      </el-col>

      <el-col :span="8">
        <el-form-item label="交易标的">
          <el-select
            v-model="localSymbol"
            style="width: 100%"
            @change="onSymbolChange"
          >
            <el-option label="贵州茅台 (600519.SS)" value="600519.SS" />
            <el-option label="平安银行 (000001.SZ)" value="000001.SZ" />
            <el-option label="比特币 (BTC-USD)"     value="BTC-USD" />
          </el-select>
        </el-form-item>
      </el-col>

      <el-col :span="8">
        <el-form-item label="策略参数">
          <el-button size="small" @click="showParams = !showParams">
            {{ showParams ? '收起' : '展开' }}
          </el-button>
        </el-form-item>
      </el-col>
    </el-row>

    <!-- 当前策略描述 -->
    <el-alert
      v-if="currentStrategy"
      :title="currentStrategy.description"
      type="info"
      :closable="false"
      show-icon
      style="margin-bottom: 12px;"
    />

    <!-- 参数面板：根据策略类型动态渲染 -->
    <div v-if="showParams" class="params-panel">
      <!-- MA 参数 -->
      <el-row v-if="localStrategyType === 'ma'" :gutter="16">
        <el-col :span="12">
          <el-form-item label="短期均线">
            <el-input-number v-model="params.short_window" :min="1" :max="50" @change="emit" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="长期均线">
            <el-input-number v-model="params.long_window" :min="10" :max="200" @change="emit" />
          </el-form-item>
        </el-col>
      </el-row>

      <!-- RSI 参数 -->
      <el-row v-else-if="localStrategyType === 'rsi'" :gutter="16">
        <el-col :span="8">
          <el-form-item label="RSI 周期">
            <el-input-number v-model="params.rsi_period" :min="5" :max="30" @change="emit" />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="超卖线">
            <el-input-number v-model="params.rsi_oversold" :min="10" :max="40" @change="emit" />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="超买线">
            <el-input-number v-model="params.rsi_overbought" :min="60" :max="90" @change="emit" />
          </el-form-item>
        </el-col>
      </el-row>

      <!-- MACD 参数 -->
      <el-row v-else-if="localStrategyType === 'macd'" :gutter="16">
        <el-col :span="8">
          <el-form-item label="快线周期">
            <el-input-number v-model="params.fast_period" :min="2" :max="50" @change="emit" />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="慢线周期">
            <el-input-number v-model="params.slow_period" :min="5" :max="100" @change="emit" />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="信号线周期">
            <el-input-number v-model="params.signal_period" :min="2" :max="20" @change="emit" />
          </el-form-item>
        </el-col>
      </el-row>

      <!-- 布林带参数 -->
      <el-row v-else-if="localStrategyType === 'bollinger'" :gutter="16">
        <el-col :span="12">
          <el-form-item label="均线周期">
            <el-input-number v-model="params.bb_period" :min="5" :max="100" @change="emit" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="标准差倍数 (k)">
            <el-input-number
              v-model="params.bb_k"
              :min="0.5"
              :max="5"
              :step="0.5"
              @change="emit"
            />
          </el-form-item>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { strategiesAPI } from '../api'

// ── Props & Emits ────────────────────────────────────────────────
const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({
      strategy_type: 'ma',
      symbol: '600519.SS',
    }),
  },
})

const emits = defineEmits(['update:modelValue', 'change'])

// ── 本地状态 ─────────────────────────────────────────────────────
const strategies = ref([])
const showParams  = ref(false)

const localStrategyType = ref(props.modelValue.strategy_type ?? 'ma')
const localSymbol       = ref(props.modelValue.symbol       ?? '600519.SS')

// 所有策略的参数，统一放一个对象（多余字段后端会忽略）
const params = reactive({
  short_window:   props.modelValue.short_window   ?? 5,
  long_window:    props.modelValue.long_window    ?? 20,
  rsi_period:     props.modelValue.rsi_period     ?? 14,
  rsi_oversold:   props.modelValue.rsi_oversold   ?? 30,
  rsi_overbought: props.modelValue.rsi_overbought ?? 70,
  fast_period:    props.modelValue.fast_period    ?? 12,
  slow_period:    props.modelValue.slow_period    ?? 26,
  signal_period:  props.modelValue.signal_period  ?? 9,
  bb_period:      props.modelValue.bb_period      ?? 20,
  bb_k:           props.modelValue.bb_k           ?? 2.0,
})

// ── 计算属性 ─────────────────────────────────────────────────────
const currentStrategy = computed(() =>
  strategies.value.find(s => s.type === localStrategyType.value) ?? null
)

// ── 方法 ─────────────────────────────────────────────────────────
const buildPayload = () => ({
  strategy_type: localStrategyType.value,
  symbol:        localSymbol.value,
  ...params,
})

const emit = () => {
  const payload = buildPayload()
  emits('update:modelValue', payload)
  emits('change', payload)
}

const onStrategyChange = () => {
  showParams.value = false   // 切换策略时收起参数，防止跨策略残留
  emit()
}

const onSymbolChange = () => emit()

// 从后端动态拉取策略列表
const loadStrategies = async () => {
  try {
    const data = await strategiesAPI.listStrategies()
    if (Array.isArray(data)) {
      strategies.value = data
    }
  } catch {
    // 后端不可用时使用默认列表
    strategies.value = [
      { type: 'ma',        name: '均线交叉策略 (MA)',    description: '基于短期和长期均线金叉/死叉产生交易信号' },
      { type: 'rsi',       name: 'RSI 超买超卖策略',     description: '基于相对强弱指标判断超买超卖区域' },
      { type: 'macd',      name: 'MACD 金叉死叉策略',    description: '基于 MACD 指标金叉买入、死叉卖出' },
      { type: 'bollinger', name: '布林带策略',            description: '价格触及布林带上下轨时产生交易信号' },
    ]
  }
}

onMounted(loadStrategies)
</script>

<style scoped>
.strategy-selector {
  width: 100%;
}

.params-panel {
  background: #f5f7fa;
  border-radius: 6px;
  padding: 16px;
  margin-bottom: 12px;
}
</style>
