<template>
  <el-card class="strategy-params-card">
    <template #header>
      <div class="card-header">
        <span>⚙️ 策略参数配置</span>
        <div class="header-actions">
          <el-button size="small" @click="resetToDefault">
            重置默认
          </el-button>
          <el-button size="small" type="primary" @click="saveAsPreset">
            保存预设
          </el-button>
        </div>
      </div>
    </template>

    <!-- 策略类型选择 -->
    <el-form :model="localConfig" label-width="100px" size="small" style="margin-bottom: 20px;">
      <el-row :gutter="16">
        <el-col :span="8">
          <el-form-item label="策略类型">
            <el-select v-model="localConfig.strategy_type" style="width: 100%;" @change="onStrategyChange">
              <el-option label="均线交叉 (MA)" value="ma" />
              <el-option label="RSI 策略" value="rsi" />
              <el-option label="MACD 策略" value="macd" />
              <el-option label="布林带策略" value="bollinger" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="标的代码">
            <el-select v-model="localConfig.symbol" style="width: 100%;" filterable>
              <el-option-group label="A股">
                <el-option label="贵州茅台 (600519.SS)" value="600519.SS" />
                <el-option label="平安银行 (000001.SZ)" value="000001.SZ" />
                <el-option label="招商银行 (600036.SS)" value="600036.SS" />
                <el-option label="万科A (000002.SZ)" value="000002.SZ" />
              </el-option-group>
              <el-option-group label="美股">
                <el-option label="苹果 (AAPL)" value="AAPL" />
                <el-option label="特斯拉 (TSLA)" value="TSLA" />
                <el-option label="谷歌 (GOOGL)" value="GOOGL" />
              </el-option-group>
              <el-option-group label="加密货币">
                <el-option label="比特币 (BTC-USD)" value="BTC-USD" />
                <el-option label="以太坊 (ETH-USD)" value="ETH-USD" />
              </el-option-group>
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="初始资金">
            <el-input-number 
              v-model="localConfig.initial_capital" 
              :min="10000" 
              :max="10000000" 
              :step="10000"
              style="width: 100%;"
              prefix="¥"
            />
          </el-form-item>
        </el-col>
      </el-row>
    </el-form>

    <!-- 参数配置标签页 -->
    <el-tabs v-model="activeParamTab" type="border-card" style="margin-bottom: 20px;">
      <!-- MA 参数 -->
      <el-tab-pane name="ma" label="均线参数">
        <el-form label-width="140px" size="small">
          <el-row :gutter="16">
            <el-col :span="12">
              <el-form-item label="短期均线周期">
                <el-input-number 
                  v-model="localConfig.short_window" 
                  :min="1" 
                  :max="50" 
                  :step="1"
                  style="width: 100%;"
                />
                <div class="param-hint">短期均线窗口期（推荐：5-20）</div>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="长期均线周期">
                <el-input-number 
                  v-model="localConfig.long_window" 
                  :min="10" 
                  :max="200" 
                  :step="5"
                  style="width: 100%;"
                />
                <div class="param-hint">长期均线窗口期（推荐：20-100）</div>
              </el-form-item>
            </el-col>
          </el-row>
          <el-form-item label="均线类型">
            <el-radio-group v-model="localConfig.ma_type">
              <el-radio-button label="SMA">简单移动平均</el-radio-button>
              <el-radio-button label="EMA">指数移动平均</el-radio-button>
            </el-radio-group>
          </el-form-item>
        </el-form>
      </el-tab-pane>

      <!-- RSI 参数 -->
      <el-tab-pane name="rsi" label="RSI参数">
        <el-form label-width="140px" size="small">
          <el-row :gutter="16">
            <el-col :span="8">
              <el-form-item label="RSI 计算周期">
                <el-input-number 
                  v-model="localConfig.rsi_period" 
                  :min="5" 
                  :max="30" 
                  :step="1"
                  style="width: 100%;"
                />
                <div class="param-hint">RSI计算周期（常用：14）</div>
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="超卖阈值">
                <el-input-number 
                  v-model="localConfig.rsi_oversold" 
                  :min="10" 
                  :max="40" 
                  :step="5"
                  style="width: 100%;"
                />
                <div class="param-hint">低于此值视为超卖（常用：30）</div>
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="超买阈值">
                <el-input-number 
                  v-model="localConfig.rsi_overbought" 
                  :min="60" 
                  :max="90" 
                  :step="5"
                  style="width: 100%;"
                />
                <div class="param-hint">高于此值视为超买（常用：70）</div>
              </el-form-item>
            </el-col>
          </el-row>
        </el-form>
      </el-tab-pane>

      <!-- MACD 参数 -->
      <el-tab-pane name="macd" label="MACD参数">
        <el-form label-width="140px" size="small">
          <el-row :gutter="16">
            <el-col :span="8">
              <el-form-item label="快线周期(EMA)">
                <el-input-number 
                  v-model="localConfig.fast_period" 
                  :min="2" 
                  :max="50" 
                  :step="1"
                  style="width: 100%;"
                />
                <div class="param-hint">快速EMA周期（常用：12）</div>
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="慢线周期(EMA)">
                <el-input-number 
                  v-model="localConfig.slow_period" 
                  :min="5" 
                  :max="100" 
                  :step="1"
                  style="width: 100%;"
                />
                <div class="param-hint">慢速EMA周期（常用：26）</div>
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="信号线周期">
                <el-input-number 
                  v-model="localConfig.signal_period" 
                  :min="2" 
                  :max="20" 
                  :step="1"
                  style="width: 100%;"
                />
                <div class="param-hint">信号线周期（常用：9）</div>
              </el-form-item>
            </el-col>
          </el-row>
        </el-form>
      </el-tab-pane>

      <!-- 布林带参数 -->
      <el-tab-pane name="bollinger" label="布林带参数">
        <el-form label-width="140px" size="small">
          <el-row :gutter="16">
            <el-col :span="8">
              <el-form-item label="移动平均周期">
                <el-input-number 
                  v-model="localConfig.bb_period" 
                  :min="5" 
                  :max="100" 
                  :step="5"
                  style="width: 100%;"
                />
                <div class="param-hint">中轨SMA周期（常用：20）</div>
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="标准差倍数">
                <el-input-number 
                  v-model="localConfig.bb_k" 
                  :min="0.5" 
                  :max="3" 
                  :step="0.1"
                  :precision="1"
                  style="width: 100%;"
                />
                <div class="param-hint">标准差乘数（常用：2.0）</div>
              </el-form-item>
            </el-col>
          </el-row>
        </el-form>
      </el-tab-pane>
    </el-tabs>

    <!-- 参数预览 -->
    <el-alert 
      title="当前参数配置预览" 
      type="info" 
      :closable="false"
      style="margin-bottom: 16px;"
    >
      <pre class="params-preview">{{ formatParamsPreview() }}</pre>
    </el-alert>

    <!-- 操作按钮 -->
    <div class="action-buttons">
      <el-button @click="exportConfig">导出配置</el-button>
      <el-button @click="importConfig">导入配置</el-button>
      <el-button type="primary" @click="applyConfig">应用配置</el-button>
    </div>
  </el-card>
</template>

<script setup>
import { ref, reactive, watch, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

// Props & Emits
const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({})
  }
})

const emits = defineEmits(['update:modelValue', 'apply'])

// 响应式数据
const activeParamTab = ref('ma')
const localConfig = reactive({
  // 基础配置
  strategy_type: 'ma',
  symbol: '600519.SS',
  initial_capital: 100000,
  
  // MA 参数
  short_window: 5,
  long_window: 20,
  ma_type: 'SMA',
  
  // RSI 参数
  rsi_period: 14,
  rsi_oversold: 30,
  rsi_overbought: 70,
  
  // MACD 参数
  fast_period: 12,
  slow_period: 26,
  signal_period: 9,
  
  // 布林带参数
  bb_period: 20,
  bb_k: 2.0
})

// 生命周期
onMounted(() => {
  // 从 props 初始化配置
  Object.assign(localConfig, props.modelValue)
  // 设置对应的参数标签页
  activeParamTab.value = localConfig.strategy_type
})

// 监听外部配置变化
watch(() => props.modelValue, (newVal) => {
  Object.assign(localConfig, newVal)
}, { deep: true })

// 方法
const onStrategyChange = (newStrategy) => {
  activeParamTab.value = newStrategy
  // 根据策略类型设置默认参数
  if (newStrategy === 'ma') {
    Object.assign(localConfig, { short_window: 5, long_window: 20 })
  } else if (newStrategy === 'rsi') {
    Object.assign(localConfig, { rsi_period: 14, rsi_oversold: 30, rsi_overbought: 70 })
  } else if (newStrategy === 'macd') {
    Object.assign(localConfig, { fast_period: 12, slow_period: 26, signal_period: 9 })
  } else if (newStrategy === 'bollinger') {
    Object.assign(localConfig, { bb_period: 20, bb_k: 2.0 })
  }
}

const resetToDefault = () => {
  ElMessageBox.confirm('确定要重置为默认参数吗？', '确认重置', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    // 重置逻辑
    const defaults = {
      ma: { short_window: 5, long_window: 20, ma_type: 'SMA' },
      rsi: { rsi_period: 14, rsi_oversold: 30, rsi_overbought: 70 },
      macd: { fast_period: 12, slow_period: 26, signal_period: 9 },
      bollinger: { bb_period: 20, bb_k: 2.0 }
    }
    Object.assign(localConfig, defaults[localConfig.strategy_type])
    ElMessage.success('已重置为默认参数')
  })
}

const saveAsPreset = async () => {
  try {
    const { value: presetName } = await ElMessageBox.prompt('请输入预设名称', '保存预设', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      inputPattern: /^.{1,20}$/,
      inputErrorMessage: '预设名称长度应在1-20个字符之间'
    })
    if (presetName) {
      // 保存到 localStorage
      const presets = JSON.parse(localStorage.getItem('strategy_presets') || '{}')
      presets[presetName] = { ...localConfig }
      localStorage.setItem('strategy_presets', JSON.stringify(presets))
      ElMessage.success(`预设 "${presetName}" 已保存`)
    }
  } catch {
    // 用户取消
  }
}

const exportConfig = () => {
  const dataStr = JSON.stringify(localConfig, null, 2)
  const dataBlob = new Blob([dataStr], { type: 'application/json' })
  const url = URL.createObjectURL(dataBlob)
  const link = document.createElement('a')
  link.href = url
  link.download = `strategy_config_${localConfig.strategy_type}_${Date.now()}.json`
  link.click()
  URL.revokeObjectURL(url)
  ElMessage.success('配置已导出')
}

const importConfig = () => {
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = '.json'
  input.onchange = (e) => {
    const file = e.target.files[0]
    if (file) {
      const reader = new FileReader()
      reader.onload = (e) => {
        try {
          const config = JSON.parse(e.target.result)
          Object.assign(localConfig, config)
          ElMessage.success('配置导入成功')
        } catch (error) {
          ElMessage.error('配置文件格式错误')
        }
      }
      reader.readAsText(file)
    }
  }
  input.click()
}

const applyConfig = () => {
  emits('update:modelValue', { ...localConfig })
  emits('apply', { ...localConfig })
  ElMessage.success('参数配置已应用')
}

const formatParamsPreview = () => {
  const relevantParams = {}
  
  if (localConfig.strategy_type === 'ma') {
    Object.assign(relevantParams, {
      策略类型: '均线交叉',
      标的: localConfig.symbol,
      短期周期: localConfig.short_window,
      长期周期: localConfig.long_window,
      均线类型: localConfig.ma_type
    })
  } else if (localConfig.strategy_type === 'rsi') {
    Object.assign(relevantParams, {
      策略类型: 'RSI策略',
      标的: localConfig.symbol,
      RSI周期: localConfig.rsi_period,
      超卖阈值: localConfig.rsi_oversold,
      超买阈值: localConfig.rsi_overbought
    })
  } else if (localConfig.strategy_type === 'macd') {
    Object.assign(relevantParams, {
      策略类型: 'MACD策略',
      标的: localConfig.symbol,
      快线周期: localConfig.fast_period,
      慢线周期: localConfig.slow_period,
      信号周期: localConfig.signal_period
    })
  } else if (localConfig.strategy_type === 'bollinger') {
    Object.assign(relevantParams, {
      策略类型: '布林带策略',
      标的: localConfig.symbol,
      均线周期: localConfig.bb_period,
      标准差倍数: localConfig.bb_k
    })
  }
  
  return JSON.stringify(relevantParams, null, 2)
}
</script>

<style scoped>
.strategy-params-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.param-hint {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.params-preview {
  font-family: 'Courier New', monospace;
  font-size: 12px;
  margin: 0;
  white-space: pre-wrap;
}

.action-buttons {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
</style>